from pydantic import BaseModel
from typing import List, Dict, Optional


class ReviewRequest(BaseModel):
    """Request to start a code review"""
    repo_id: str
    files: Optional[List[str]] = None  # Specific files to review
    agents: Optional[List[str]] = None  # Specific agents to run


class ReviewFinding(BaseModel):
    """A single finding from the review"""
    id: str
    severity: str  # critical, high, medium, low, info
    category: str
    title: str
    description: str
    file_path: str
    start_line: int
    end_line: int
    suggestion: str
    code_snippet: str


class ReviewResponse(BaseModel):
    """Complete review response"""
    review_id: str
    repo_id: str
    status: str
    total_findings: int
    severity_counts: Dict[str, int]
    findings: List[ReviewFinding]


class ReviewStatus(BaseModel):
    """Status of an ongoing review"""
    review_id: str
    status: str  # pending, processing, completed, failed
    progress: int  # 0-100
    error: Optional[str] = None
