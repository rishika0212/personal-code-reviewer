from pydantic import BaseModel, model_validator
from typing import List, Dict, Optional, Any


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
    repo_url: Optional[str] = None
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


class PatchRequest(BaseModel):
    """Request to generate a patch for specific findings"""
    review_id: str
    finding_ids: List[str]


class FilePatch(BaseModel):
    """Patch details for a single file"""
    original: str
    modified: str
    diff: str
    line_diff: List[Dict[str, Any]]
    confidence: float = 0.0


class PatchResponse(BaseModel):
    """Response containing generated patches"""
    review_id: str
    patches: Dict[str, FilePatch]


class ApplyPatchesRequest(BaseModel):
    """Request to apply specific patches"""
    review_id: str
    patches: Dict[str, str]  # file_path -> modified_content


class PushRequest(BaseModel):
    """Request to push changes to GitHub"""
    review_id: str
    title: Optional[str] = "Apply AI fixes"
    body: Optional[str] = "This PR applies fixes suggested by Zencoder AI review."
