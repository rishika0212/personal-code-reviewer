import uuid
import asyncio
import json
from pathlib import Path
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass, field

from agents.code_analyzer import CodeAnalyzerAgent
from agents.security_agent import SecurityAgent
from agents.optimization_agent import OptimizationAgent
from agents.base_agent import AgentFinding
from indexing.chunker import CodeChunker, CodeChunk
from indexing.embeddings import EmbeddingService
from vectorstore.chroma_store import chroma_store
from loaders.github_loader import github_loader
from schemas.review import ReviewRequest, ReviewResponse, ReviewFinding, ReviewStatus
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
        self.github_loader = github_loader
        self._sessions: Dict[str, ReviewSession] = {}
        self._results: Dict[str, ReviewResponse] = {}
        self.review_status: Dict[str, ReviewStatus] = {}
        self.storage_path = Path("reviews.json")
        self._load_from_disk()
    
    def _save_to_disk(self):
        """Save status and results to disk"""
        try:
            data = {
                "status": {k: v.model_dump() for k, v in self.review_status.items()},
                "results": {k: v.model_dump() for k, v in self._results.items()}
            }
            self.storage_path.write_text(json.dumps(data), encoding='utf-8')
        except Exception as e:
            logger.error(f"Failed to save to disk: {e}")

    def _load_from_disk(self):
        """Load status and results from disk"""
        if not self.storage_path.exists():
            return
        try:
            data = json.loads(self.storage_path.read_text(encoding='utf-8'))
            self.review_status = {k: ReviewStatus(**v) for k, v in data.get("status", {}).items()}
            self._results = {k: ReviewResponse(**v) for k, v in data.get("results", {}).items()}
            logger.info(f"Loaded {len(self.review_status)} reviews from disk")
        except Exception as e:
            logger.error(f"Failed to load from disk: {e}")
    
    def create_review(self, request: ReviewRequest) -> str:
        """Create a new review session"""
        review_id = str(uuid.uuid4())[:8]
        
        self._sessions[review_id] = ReviewSession(
            review_id=review_id,
            repo_id=request.repo_id
        )
        
        self.review_status[review_id] = ReviewStatus(
            review_id=review_id,
            status="pending",
            progress=0
        )
        self._save_to_disk()
        
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
                
                # Get relevant chunks for this agent using vector search
                query_text = agent._get_default_prompt()
                query_embedding = await self.embeddings.embed_text(query_text)
                
                collection_name = f"review_{review_id}"
                results = chroma_store.query(
                    collection_name=collection_name,
                    query_embedding=query_embedding,
                    n_results=settings.MAX_CHUNKS_PER_REVIEW
                )
                
                # Reconstruct CodeChunks from results
                relevant_chunks = []
                if results["documents"]:
                    for i, doc in enumerate(results["documents"][0]):
                        meta = results["metadatas"][0][i]
                        relevant_chunks.append(CodeChunk(
                            content=doc,
                            file_path=meta["file_path"],
                            start_line=meta["start_line"],
                            end_line=meta["end_line"],
                            language=meta["language"],
                            metadata=meta
                        ))
                
                # If no vector search results, fallback to first few chunks
                if not relevant_chunks:
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
            self._save_to_disk()
            if progress_callback:
                progress_callback(100)
                
        except Exception as e:
            session.status = "failed"
            logger.error(f"Review failed: {e}")
            self._save_to_disk()
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
                agent_name=finding.agent_name,
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


# Singleton instance
review_manager = ReviewManager()
