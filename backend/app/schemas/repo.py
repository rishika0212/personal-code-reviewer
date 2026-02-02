from pydantic import BaseModel, HttpUrl
from typing import List, Optional


class RepoInput(BaseModel):
    """Input for repository upload"""
    url: str
    branch: Optional[str] = "main"


class RepoInfo(BaseModel):
    """Information about an uploaded repository"""
    repo_id: str
    name: str
    url: str
    files_count: int
    languages: List[str]


class FileInfo(BaseModel):
    """Information about a file in the repository"""
    name: str
    path: str
    type: str  # file or directory
    size: Optional[int] = None
    language: Optional[str] = None
