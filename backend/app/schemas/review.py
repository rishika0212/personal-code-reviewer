from pydantic import BaseModel, model_validator
from typing import List, Dict, Optional


class ReviewRequest(BaseModel):
    """Request to start a code review"""
    repo_id: str
    files: Optional[List[str]] = None  # Specific files to review
    agents: Optional[List[str]] = None  # Specific agents to run


class ReviewFinding(BaseModel):
    """A single finding from the review"""
    id: str
    agent_name: str
    severity: str  # critical, high, medium, low, info
    category: str
    title: str
    description: str
    file_path: str
    start_line: int
    end_line: Optional[int] = None
    suggestion: str
    code_snippet: str

    @property
    def line(self) -> int:
        return self.start_line

    @model_validator(mode="after")
    def auto_fill_end_line(self) -> "ReviewFinding":
        if self.end_line is None:
            self.end_line = self.line
        return self


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
    message: Optional[str] = None
    error: Optional[str] = None
