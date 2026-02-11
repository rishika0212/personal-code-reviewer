from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any

from schemas.review import ReviewRequest, ReviewResponse, ReviewStatus
from orchestrator.review_manager import review_manager
from utils.logger import logger

router = APIRouter()


@router.post("/", response_model=Dict[str, str])
async def start_review(request: ReviewRequest, background_tasks: BackgroundTasks):
    """Start a new code review"""
    try:
        review_id = review_manager.create_review(request)
        background_tasks.add_task(run_review, review_id, request)
        return {"review_id": review_id, "status": "started"}
    except Exception as e:
        logger.error(f"Failed to start review: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{review_id}", response_model=ReviewStatus)
async def get_review_status(review_id: str):
    """Get the status of a review"""
    if review_id not in review_manager.review_status:
        raise HTTPException(status_code=404, detail="Review not found")
    return review_manager.review_status[review_id]


@router.get("/{review_id}", response_model=ReviewResponse)
async def get_review_results(review_id: str):
    """Get the results of a completed review"""
    if review_id not in review_manager.review_status:
        raise HTTPException(status_code=404, detail="Review not found")
    
    status = review_manager.review_status[review_id]
    if status.status == "failed":
        raise HTTPException(status_code=400, detail=f"Review failed: {status.error or 'Unknown error'}")
    
    if status.status != "completed":
        raise HTTPException(status_code=400, detail=f"Review in progress: {status.status}")
    
    try:
        return review_manager.get_review_results(review_id)
    except ValueError as e:
        logger.error(f"Inconsistency: Review marked as completed but results missing for {review_id}")
        raise HTTPException(status_code=404, detail=str(e))


async def run_review(review_id: str, request: ReviewRequest):
    """Background task to run the review"""
    try:
        review_manager.review_status[review_id].status = "processing"
        review_manager._save_to_disk()
        
        # Run the review through all agents
        await review_manager.run_review(
            review_id,
            request,
            progress_callback=lambda p, m=None: update_progress(review_id, p, m)
        )
        
        review_manager.review_status[review_id].status = "completed"
        review_manager.review_status[review_id].progress = 100
        review_manager.review_status[review_id].message = "Analysis complete"
        review_manager._save_to_disk()
    except Exception as e:
        logger.error(f"Review failed: {e}")
        if review_id in review_manager.review_status:
            review_manager.review_status[review_id].status = "failed"
            review_manager.review_status[review_id].error = str(e)
            review_manager.review_status[review_id].message = "Review failed"
            review_manager._save_to_disk()


def update_progress(review_id: str, progress: int, message: str = None):
    """Update review progress"""
    if review_id in review_manager.review_status:
        old_status = review_manager.review_status[review_id]
        should_save = progress % 5 == 0 or progress == 100 or (message and message != old_status.message)
        
        review_manager.review_status[review_id].progress = progress
        if message:
            review_manager.review_status[review_id].message = message
        
        if should_save:
            review_manager._save_to_disk(save_results=False)
