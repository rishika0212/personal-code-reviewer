import uuid
import asyncio
import json
import gc
import time
from pathlib import Path
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass, field

from agents.code_analyzer import CodeAnalyzerAgent
from agents.security_agent import SecurityAgent
from agents.optimization_agent import OptimizationAgent
from agents.patch_generator import PatchGeneratorAgent
from agents.base_agent import AgentFinding
from services.llm_service import LLMService
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
        self.patch_generator = PatchGeneratorAgent()
        self.chunker = CodeChunker()
        self.embeddings = EmbeddingService()
        self.llm = LLMService()
        self.github_loader = github_loader
        self._sessions: Dict[str, ReviewSession] = {}
        self._results: Dict[str, ReviewResponse] = {}
        self.review_status: Dict[str, ReviewStatus] = {}
        self.status_path = Path(settings.STATUS_FILE)
        self.results_path = Path(settings.RESULTS_FILE)
        self._lock = asyncio.Lock()  # FIX 7: Backpressure - only one review at a time
        
        # Ensure data directory exists
        self.status_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._load_from_disk()
    
    def _save_to_disk(self, save_results: bool = True):
        """Save status and results to disk"""
        try:
            # Save status
            status_data = {k: v.model_dump() for k, v in self.review_status.items()}
            self.status_path.write_text(json.dumps(status_data), encoding='utf-8')
            
            # Save results if requested
            if save_results:
                self._ensure_results_loaded()
                results_data = {k: v.model_dump() for k, v in self._results.items()}
                self.results_path.write_text(json.dumps(results_data), encoding='utf-8')
        except Exception as e:
            logger.error(f"Failed to save to disk: {e}")

    def _load_from_disk(self):
        """Load status from disk (results loaded lazily)"""
        try:
            if self.status_path.exists():
                content = self.status_path.read_text(encoding='utf-8')
                if content.strip():
                    status_data = json.loads(content)
                    self.review_status = {k: ReviewStatus(**v) for k, v in status_data.items()}
                    
                    # Reset any "processing" or "pending" statuses to "failed" on startup
                    # since their background tasks are no longer running
                    for status in self.review_status.values():
                        if status.status in ("processing", "pending"):
                            status.status = "failed"
                            status.error = "Review interrupted by server restart"
                            status.message = "Failed (Interrupted)"
                    self._save_to_disk(save_results=False)
            
            logger.info(f"Loaded {len(self.review_status)} reviews from disk")
        except Exception as e:
            logger.error(f"Failed to load from disk: {e}")
    
    def _ensure_results_loaded(self):
        """Lazily load results from disk"""
        if self._results:
            return
            
        try:
            if self.results_path.exists():
                results_text = self.results_path.read_text(encoding='utf-8')
                if results_text:
                    results_data = json.loads(results_text)
                    self._results = {k: ReviewResponse(**v) for k, v in results_data.items()}
                    logger.info(f"Loaded {len(self._results)} review results from disk")
        except Exception as e:
            logger.error(f"Failed to load results from disk: {e}")

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
        progress_callback: Optional[Callable[[int, Optional[str]], None]] = None
    ):
        """Run the complete review process"""
        # FIX 7: Backpressure - Wait for previous review to finish
        if self._lock.locked():
            logger.info(f"[{time.strftime('%H:%M:%S')}] Review {review_id} queued, waiting for previous review...")
            if progress_callback:
                progress_callback(0, "Waiting for previous review to finish...")
        
        async with self._lock:
            logger.info(f"[{time.strftime('%H:%M:%S')}] STARTING review {review_id}")
            session = self._sessions.get(review_id)
            if not session:
                raise ValueError(f"Review session {review_id} not found")
            
            try:
                session.status = "processing"
                
                # Initial progress update (5%)
                if progress_callback:
                    progress_callback(5, "Initializing analysis...")
                
                # Check if LLM is available
                llm_available = await self.llm.is_available()
                embed_available = await self.embeddings.is_available()
                
                if not llm_available or not embed_available:
                    missing = []
                    if not llm_available: missing.append(f"LLM model ({settings.LLM_MODEL})")
                    if not embed_available: missing.append(f"Embedding model ({settings.EMBEDDING_MODEL})")
                    
                    error_msg = f"Ollama service unavailable or missing models: {', '.join(missing)}. " \
                               f"Ensure Ollama is running at {settings.OLLAMA_HOST} and models are pulled."
                    
                    logger.error(error_msg)
                    if progress_callback:
                        progress_callback(5, "Error: Ollama or models unavailable")
                    
                    # Update status to failed
                    self.review_status[review_id].status = "failed"
                    self.review_status[review_id].error = error_msg
                    self._save_to_disk()
                    raise RuntimeError(error_msg)
                
                # Step 1: Load and chunk code (25%)
                logger.info(f"[{time.strftime('%H:%M:%S')}] Step 1: Loading and chunking code for review {review_id}")
                if progress_callback:
                    progress_callback(10, "Extracting code segments...")
                
                chunks = await self._load_and_chunk(review_id, request, progress_callback)
                session.chunks = chunks
                logger.info(f"[{time.strftime('%H:%M:%S')}] Successfully created {len(chunks)} chunks from repository")
                
                if progress_callback:
                    progress_callback(25, "Preparing vector index...")
                
                # Step 2: Index in vector store (40%)
                logger.info(f"[{time.strftime('%H:%M:%S')}] Step 2: Indexing {len(chunks)} chunks for review {review_id}")
                await self._index_chunks(review_id, chunks, progress_callback)
                
                if progress_callback:
                    progress_callback(40, "Ready for agent review")
                
                # Step 3: Run agents (40-95%)
                all_findings = []
                agent_progress_start = 40
                total_agent_contribution = 55
                progress_per_agent = total_agent_contribution // len(self.agents)
                
                # FIX 1: Run agents SEQUENTIALLY (already loop, but adding logs)
                for i, agent in enumerate(self.agents):
                    logger.info(f"[{time.strftime('%H:%M:%S')}] [START] agent {agent.name}")
                    if progress_callback:
                        progress_callback(agent_progress_start + (i * progress_per_agent), f"Running {agent.name}...")
                    
                    await asyncio.sleep(0.1)  # Yield to event loop to keep system responsive
                    
                    # Get relevant chunks for this agent using vector search
                    query_text = agent._get_default_prompt()
                    try:
                        query_embedding = await self.embeddings.embed_text(query_text)
                        
                        collection_name = f"review_{review_id}"
                        results = chroma_store.query(
                            collection_name=collection_name,
                            query_embedding=query_embedding,
                            n_results=settings.MAX_CHUNKS_PER_REVIEW
                        )
                        
                        # Reconstruct CodeChunks from results
                        relevant_chunks = []
                        if results["documents"] and results["documents"][0]:
                            for j, doc in enumerate(results["documents"][0]):
                                meta = results["metadatas"][0][j]
                                relevant_chunks.append(CodeChunk(
                                    content=doc,
                                    file_path=meta["file_path"],
                                    start_line=meta["start_line"],
                                    end_line=meta["end_line"],
                                    language=meta["language"],
                                    metadata=meta
                                ))
                    except Exception as e:
                        logger.error(f"Vector search failed for agent {agent.name}: {e}")
                        relevant_chunks = []
                    
                    # If no vector search results, fallback to first few chunks
                    if not relevant_chunks:
                        relevant_chunks = chunks[:settings.MAX_CHUNKS_PER_REVIEW]
                    
                    # Create a sub-progress callback for the agent
                    def make_agent_cb(agent_idx, agent_name):
                        def cb(sub_p):
                            if progress_callback:
                                p = agent_progress_start + (agent_idx * progress_per_agent) + int(sub_p * progress_per_agent)
                                progress_callback(min(p, 95), f"Analyzing with {agent_name}...")
                        return cb

                    findings = await agent.analyze(relevant_chunks, progress_callback=make_agent_cb(i, agent.name))
                    all_findings.extend(findings)
                    
                    # FIX 4: STREAM RESULTS - Store partial findings
                    session.findings = all_findings
                    self._results[review_id] = self._compile_results(review_id, request, all_findings)
                    self._save_to_disk()
                    
                    logger.info(f"[{time.strftime('%H:%M:%S')}] [END] agent {agent.name} ({len(findings)} findings)")
                    
                    # Update progress to the end of this agent's block
                    if progress_callback:
                        progress_callback(min(agent_progress_start + (i + 1) * progress_per_agent, 95), f"Finished {agent.name}")
                    
                    # FIX 8: MEMORY CLEANUP after each agent
                    del findings
                    gc.collect()
                
                # Step 4: Compile results (100%)
                if progress_callback:
                    progress_callback(98, "Compiling final report...")
                    
                self._results[review_id] = self._compile_results(
                    review_id, request, all_findings
                )
                
                session.status = "completed"
                self._save_to_disk()
                logger.info(f"[{time.strftime('%H:%M:%S')}] COMPLETED review {review_id}")
                if progress_callback:
                    progress_callback(100)
                    
            except Exception as e:
                session.status = "failed"
                logger.error(f"[{time.strftime('%H:%M:%S')}] Review FAILED: {e}")
                self._save_to_disk()
                raise
    
    async def _load_and_chunk(
        self, 
        review_id: str,
        request: ReviewRequest,
        progress_callback: Optional[Callable[[int, Optional[str]], None]] = None
    ) -> List[CodeChunk]:
        """Load code files and chunk them"""
        chunks = []
        
        # Get files from the repository
        try:
            file_tree = self.github_loader.get_file_tree(request.repo_id)
        except Exception as e:
            logger.error(f"Failed to get file tree: {e}")
            return []
        
        all_files = self._flatten_file_tree(file_tree)
        
        # FIX 2: CAP CODE CHUNKS - Limit files and total chunks
        if len(all_files) > settings.MAX_FILES_PER_REVIEW:
            logger.warning(f"[{review_id}] Repository has {len(all_files)} files. Capping at {settings.MAX_FILES_PER_REVIEW}")
            all_files = all_files[:settings.MAX_FILES_PER_REVIEW]
            
        total_files = len(all_files)
        
        for i, file_info in enumerate(all_files):
            # FIX 2: CAP CODE CHUNKS - Hard limit on total chunks
            if len(chunks) >= settings.MAX_CHUNKS_TOTAL:
                logger.warning(f"[{review_id}] Reached max total chunks ({settings.MAX_CHUNKS_TOTAL}). Stopping indexing.")
                break

            if file_info["type"] == "file":
                try:
                    # FIX 2: Per-file timeout (5 seconds)
                    async def process_single_file():
                        content = await asyncio.to_thread(
                            self.github_loader.get_file_content,
                            request.repo_id,
                            file_info["path"]
                        )
                        
                        if not content:
                            return []

                        return self.chunker.chunk_file(
                            content,
                            file_info["path"]
                        )

                    file_chunks = await asyncio.wait_for(process_single_file(), timeout=5.0)
                    chunks.extend(file_chunks)
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout processing {file_info['path']}, skipping.")
                except Exception as e:
                    logger.warning(f"Failed to load {file_info['path']}: {e}")
        
        return chunks
    
    async def _index_chunks(
        self, 
        review_id: str, 
        chunks: List[CodeChunk],
        progress_callback: Optional[Callable[[int, Optional[str]], None]] = None
    ):
        """Index chunks in vector store"""
        if not chunks:
            return
        
        # Generate embeddings in smaller batches to avoid blocking and show progress
        batch_size = 5
        texts = [chunk.content for chunk in chunks]
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = await self.embeddings.embed_batch(batch)
            all_embeddings.extend(batch_embeddings)
            
            if progress_callback:
                # Use 25-40% range for indexing
                p = 25 + int((min(i + batch_size, len(texts)) / len(texts)) * 15)
                progress_callback(p, f"Generating embeddings ({min(i + batch_size, len(texts))}/{len(texts)})...")
            
            await asyncio.sleep(0.1)
        
        # Store in ChromaDB
        collection_name = f"review_{review_id}"
        chroma_store.add_chunks(collection_name, chunks, all_embeddings)
    
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
        
        # Try to get repo URL if available
        repo_url = None
        try:
            repo_url = self.github_loader.get_repo_url(request.repo_id)
        except:
            pass

        return ReviewResponse(
            review_id=review_id,
            repo_id=request.repo_id,
            repo_url=repo_url,
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
        self._ensure_results_loaded()
        if review_id not in self._results:
            raise ValueError(f"Results for review {review_id} not found")
        return self._results[review_id]

    async def generate_patch(
        self,
        review_id: str,
        finding_ids: List[str]
    ) -> Dict[str, Any]:
        """Generate a patch for selected findings"""
        results = self.get_review_results(review_id)
        
        # Filter findings by IDs
        selected_findings = [f for f in results.findings if f.id in finding_ids]
        if not selected_findings:
            raise ValueError("No matching findings found")
            
        # Group findings by file
        files_to_patch = {}
        for f in selected_findings:
            if f.file_path not in files_to_patch:
                files_to_patch[f.file_path] = []
            files_to_patch[f.file_path].append(f)
            
        patches = {}
        for file_path, file_findings in files_to_patch.items():
            # Load original file content
            try:
                original_code = await asyncio.to_thread(
                    self.github_loader.get_file_content,
                    results.repo_id,
                    file_path
                )
                
                if not original_code:
                    logger.error(f"Could not load content for {file_path}")
                    continue
                
                # Apply patches one by one
                current_code = original_code
                file_confidences = []
                
                for finding in file_findings:
                    # Generate patch for this specific finding
                    patch_result = await self.patch_generator.generate_patch(
                        file_path,
                        current_code,
                        finding
                    )
                    
                    patch = patch_result["patch"]
                    original_snippet = patch_result["original_snippet"]
                    confidence = patch_result["confidence"]
                    
                    if original_snippet in current_code:
                        # Replace the snippet with the patch
                        current_code = current_code.replace(original_snippet, patch, 1)
                        file_confidences.append(confidence)
                    else:
                        logger.warning(f"Could not find snippet in {file_path} for finding {finding.id}. Code might have changed.")
                
                modified_code = current_code
                
                # Compute diff
                from services.diff_service import DiffService
                diff = DiffService.compute_diff(original_code, modified_code)
                line_diff = DiffService.compute_line_diff(original_code, modified_code)
                
                # Calculate average confidence for the file
                avg_confidence = sum(file_confidences) / len(file_confidences) if file_confidences else 0.0
                
                patches[file_path] = {
                    "original": original_code,
                    "modified": modified_code,
                    "diff": diff,
                    "line_diff": line_diff,
                    "confidence": avg_confidence
                }
            except Exception as e:
                logger.error(f"Failed to generate patch for {file_path}: {e}")
                
        return {
            "review_id": review_id,
            "patches": patches
        }

    async def apply_patches(
        self,
        review_id: str,
        patches: Dict[str, str]
    ) -> bool:
        """Apply patches to the repository"""
        results = self.get_review_results(review_id)
        repo_id = results.repo_id
        
        for file_path, content in patches.items():
            try:
                await asyncio.to_thread(
                    self.github_loader.apply_patch,
                    repo_id,
                    file_path,
                    content
                )
            except Exception as e:
                logger.error(f"Failed to apply patch to {file_path}: {e}")
                return False
                
        return True

    async def push_to_github(
        self,
        review_id: str,
        title: Optional[str] = None,
        body: Optional[str] = None
    ) -> str:
        """Push applied changes to GitHub and create a PR"""
        results = self.get_review_results(review_id)
        repo_id = results.repo_id
        repo_url = results.repo_url
        
        if not repo_url:
            # Fallback if not stored
            repo_url = self.github_loader.get_repo_url(repo_id)
            
        pr_url = await self.github_loader.create_pull_request(
            repo_id=repo_id,
            repo_url=repo_url,
            title=title or "Apply AI fixes from Zencoder",
            body=body or "This PR applies fixes suggested during the AI code review."
        )
        
        return pr_url


# Singleton instance
review_manager = ReviewManager()
