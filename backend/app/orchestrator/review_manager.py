import uuid
import asyncio
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass, field

from agents.code_analyzer import CodeAnalyzerAgent
from agents.security_agent import SecurityAgent
from agents.optimization_agent import OptimizationAgent
from agents.base_agent import AgentFinding
from indexing.chunker import CodeChunker, CodeChunk
from indexing.embeddings import EmbeddingService
from vectorstore.chroma_store import chroma_store
from loaders.github_loader import GitHubLoader
from schemas.review import ReviewRequest, ReviewResponse, ReviewFinding
from config import settings
from utils.logger import logger


@dataclass
class ReviewSession:
    """Represents an active review session"""
    review_id: str
    repo_id: str
    chunks: List[CodeChunk] = field(default_factory=list)
    findings: List[AgentFinding] = field(default_factory=list)
    status: str = "pending"


class ReviewManager:
    """Orchestrates the review process across multiple agents"""
    
    def __init__(self):
        self.agents = [
            CodeAnalyzerAgent(),
            SecurityAgent(),
            OptimizationAgent()
        ]
        self.chunker = CodeChunker()
        self.embeddings = EmbeddingService()
        self.github_loader = GitHubLoader()
        self._sessions: Dict[str, ReviewSession] = {}
        self._results: Dict[str, ReviewResponse] = {}
    
    def create_review(self, request: ReviewRequest) -> str:
        """Create a new review session"""
        review_id = str(uuid.uuid4())[:8]
        
        self._sessions[review_id] = ReviewSession(
            review_id=review_id,
            repo_id=request.repo_id
        )
        
        return review_id
    
    async def run_review(
        self,
        review_id: str,
        request: ReviewRequest,
        progress_callback: Optional[Callable[[int], None]] = None
    ):
        """Run the complete review process"""
        session = self._sessions.get(review_id)
        if not session:
            raise ValueError(f"Review session {review_id} not found")
        
        try:
            session.status = "processing"
            
            # Step 1: Load and chunk code (20%)
            if progress_callback:
                progress_callback(10)
            
            chunks = await self._load_and_chunk(request)
            session.chunks = chunks
            
            if progress_callback:
                progress_callback(20)
            
            # Step 2: Index in vector store (30%)
            await self._index_chunks(review_id, chunks)
            
            if progress_callback:
                progress_callback(30)
            
            # Step 3: Run agents (30-90%)
            all_findings = []
            agent_progress = 30
            progress_per_agent = 60 // len(self.agents)
            
            for agent in self.agents:
                logger.info(f"Running agent: {agent.name}")
                
                # Get relevant chunks for this agent
                relevant_chunks = chunks[:settings.MAX_CHUNKS_PER_REVIEW]
                
                findings = await agent.analyze(relevant_chunks)
                all_findings.extend(findings)
                
                agent_progress += progress_per_agent
                if progress_callback:
                    progress_callback(agent_progress)
            
            session.findings = all_findings
            
            # Step 4: Compile results (100%)
            self._results[review_id] = self._compile_results(
                review_id, request, all_findings
            )
            
            session.status = "completed"
            if progress_callback:
                progress_callback(100)
                
        except Exception as e:
            session.status = "failed"
            logger.error(f"Review failed: {e}")
            raise
    
    async def _load_and_chunk(self, request: ReviewRequest) -> List[CodeChunk]:
        """Load code files and chunk them"""
        chunks = []
        
        # Get files from the repository
        file_tree = self.github_loader.get_file_tree(request.repo_id)
        
        for file_info in self._flatten_file_tree(file_tree):
            if file_info["type"] == "file":
                try:
                    content = self.github_loader.get_file_content(
                        request.repo_id,
                        file_info["path"]
                    )
                    file_chunks = self.chunker.chunk_file(
                        content,
                        file_info["path"]
                    )
                    chunks.extend(file_chunks)
                except Exception as e:
                    logger.warning(f"Failed to load {file_info['path']}: {e}")
        
        return chunks
    
    async def _index_chunks(self, review_id: str, chunks: List[CodeChunk]):
        """Index chunks in vector store"""
        if not chunks:
            return
        
        # Generate embeddings
        texts = [chunk.content for chunk in chunks]
        embeddings = await self.embeddings.embed_batch(texts)
        
        # Store in ChromaDB
        collection_name = f"review_{review_id}"
        chroma_store.add_chunks(collection_name, chunks, embeddings)
    
    def _compile_results(
        self,
        review_id: str,
        request: ReviewRequest,
        findings: List[AgentFinding]
    ) -> ReviewResponse:
        """Compile findings into a review response"""
        # Count by severity
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        
        review_findings = []
        for finding in findings:
            severity_counts[finding.severity] = severity_counts.get(finding.severity, 0) + 1
            
            review_findings.append(ReviewFinding(
                id=str(uuid.uuid4())[:8],
                severity=finding.severity,
                category=finding.category,
                title=finding.title,
                description=finding.description,
                file_path=finding.file_path,
                start_line=finding.start_line,
                end_line=finding.end_line,
                suggestion=finding.suggestion,
                code_snippet=finding.code_snippet
            ))
        
        return ReviewResponse(
            review_id=review_id,
            repo_id=request.repo_id,
            status="completed",
            total_findings=len(findings),
            severity_counts=severity_counts,
            findings=review_findings
        )
    
    def _flatten_file_tree(self, tree: List[Dict]) -> List[Dict]:
        """Flatten a nested file tree"""
        files = []
        for item in tree:
            if item["type"] == "file":
                files.append(item)
            elif item["type"] == "directory":
                files.extend(self._flatten_file_tree(item.get("children", [])))
        return files
    
    def get_review_results(self, review_id: str) -> ReviewResponse:
        """Get the results of a completed review"""
        if review_id not in self._results:
            raise ValueError(f"Results for review {review_id} not found")
        return self._results[review_id]
