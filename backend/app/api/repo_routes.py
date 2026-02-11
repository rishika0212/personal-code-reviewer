from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import Dict, Any

from schemas.repo import RepoInput, RepoInfo
from loaders.github_loader import github_loader
from utils.logger import logger

router = APIRouter()


@router.post("/github", response_model=RepoInfo)
async def upload_github_repo(repo_input: RepoInput):
    """Clone and index a GitHub repository"""
    try:
        repo_info = await github_loader.clone_repo(repo_input.url)
        return repo_info
    except Exception as e:
        logger.error(f"Failed to clone repo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    """Upload local files for review"""
    try:
        uploaded = []
        for file in files:
            content = await file.read()
            uploaded.append({
                "filename": file.filename,
                "size": len(content)
            })
        return {"uploaded": uploaded, "count": len(uploaded)}
    except Exception as e:
        logger.error(f"Failed to upload files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files/{repo_id}")
async def get_repo_files(repo_id: str):
    """Get list of files in a repository"""
    try:
        import asyncio
        files = await asyncio.to_thread(github_loader.get_file_tree, repo_id)
        return {"repo_id": repo_id, "files": files}
    except Exception as e:
        logger.error(f"Failed to get files: {e}")
        raise HTTPException(status_code=404, detail="Repository not found")


@router.get("/content/{repo_id}")
async def get_file_content(repo_id: str, path: str):
    """Get content of a file in a repository"""
    try:
        import asyncio
        content = await asyncio.to_thread(github_loader.get_file_content, repo_id, path)
        return {"repo_id": repo_id, "path": path, "content": content}
    except Exception as e:
        logger.error(f"Failed to get file content: {e}")
        raise HTTPException(status_code=404, detail=f"File {path} not found")
