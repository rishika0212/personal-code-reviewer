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
    if status.status != "completed":
        raise HTTPException(status_code=400, detail="Review not yet completed")
    
    return review_manager.get_review_results(review_id)


async def run_review(review_id: str, request: ReviewRequest):
    """Background task to run the review"""
    try:
        review_manager.review_status[review_id].status = "processing"
        review_manager._save_to_disk()
        
        # Run the review through all agents
        await review_manager.run_review(
            review_id,
            request,
            progress_callback=lambda p: update_progress(review_id, p)
        )
        
        review_manager.review_status[review_id].status = "completed"
        review_manager.review_status[review_id].progress = 100
        review_manager._save_to_disk()
    except Exception as e:
        logger.error(f"Review failed: {e}")
        if review_id in review_manager.review_status:
            review_manager.review_status[review_id].status = "failed"
            review_manager.review_status[review_id].error = str(e)
            review_manager._save_to_disk()


def update_progress(review_id: str, progress: int):
    """Update review progress"""
    if review_id in review_manager.review_status:
        review_manager.review_status[review_id].progress = progress
        review_manager._save_to_disk()
