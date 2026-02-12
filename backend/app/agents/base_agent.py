from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass

from services.llm_service import LLMService
from services.llm_output_parser import repair_and_parse
from indexing.chunker import CodeChunk
from utils.logger import logger


@dataclass
class AgentFinding:
    """Represents a single finding from an agent"""
    agent_name: str
    severity: str  # critical, high, medium, low, info
    category: str
    title: str
    description: str
    file_path: str
    start_line: int
    end_line: int
    suggestion: str
    code_snippet: str


class BaseAgent(ABC):
    """Base class for all review agents"""
    
    def __init__(self, name: str, prompt_file: str):
        self.name = name
        self.prompt_file = prompt_file
        self.llm = LLMService()
        self.stats = {"parsed": 0, "failed": 0}
        self._load_prompt()
    
    def _load_prompt(self):
        """Load the system prompt from file"""
        try:
            with open(f"prompts/{self.prompt_file}", "r") as f:
                self.system_prompt = f.read()
        except FileNotFoundError:
            logger.warning(f"Prompt file not found: {self.prompt_file}")
            self.system_prompt = self._get_default_prompt()
    
    @abstractmethod
    def _get_default_prompt(self) -> str:
        """Return a default prompt if file not found"""
        pass
    
    async def analyze(
        self, 
        chunks: List[CodeChunk], 
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> List[AgentFinding]:
        """Analyze code chunks and return findings concurrently"""
        import asyncio
        findings = []
        
        if not chunks:
            return []

        # Limit concurrency to 1 to avoid overloading the laptop's CPU/GPU
        semaphore = asyncio.Semaphore(1)
        total_chunks = len(chunks)
        completed_chunks = 0

        async def _analyze_with_semaphore(chunk):
            nonlocal completed_chunks
            async with semaphore:
                try:
                    result = await self._analyze_chunk(chunk)
                    completed_chunks += 1
                    if progress_callback:
                        # Call with sub-progress (0.0 to 1.0)
                        progress_callback(completed_chunks / total_chunks)
                    return result
                except Exception:
                    logger.exception(f"Error analyzing chunk {chunk.file_path}:{chunk.start_line}")
                    completed_chunks += 1
                    if progress_callback:
                        progress_callback(completed_chunks / total_chunks)
                    return []

        # Run all chunks concurrently with limited concurrency
        tasks = [_analyze_with_semaphore(chunk) for chunk in chunks]
        results = await asyncio.gather(*tasks)
        
        for chunk_findings in results:
            findings.extend(chunk_findings)
        
        logger.info(
            f"[END] {self.name}: {self.stats['parsed']} parsed, {self.stats['failed']} dropped"
        )
        
        return findings
    
    async def _analyze_chunk(self, chunk: CodeChunk) -> List[AgentFinding]:
        """Analyze a single code chunk"""
        prompt = self._build_prompt(chunk)
        
        response = await self.llm.generate(
            system_prompt=self.system_prompt,
            user_prompt=prompt
        )
        
        parsed_data = await repair_and_parse(response, self.llm)
        
        if parsed_data:
            self.stats["parsed"] += 1
            return self._process_findings(parsed_data, chunk)
        else:
            self.stats["failed"] += 1
            logger.warning(f"[{self.name}] Failed to parse chunk {chunk.file_path}:{chunk.start_line}")
            return []
    
    def _process_findings(
        self,
        data: Dict[str, Any],
        chunk: CodeChunk
    ) -> List[AgentFinding]:
        """Convert parsed JSON data into AgentFinding objects"""
        findings = []
        
        for f in data.get("findings", []):
            findings.append(AgentFinding(
                agent_name=self.name,
                severity=f.get("severity", "info"),
                category=f.get("category", "general"),
                title=f.get("title", "Untitled"),
                description=f.get("description", ""),
                file_path=chunk.file_path,
                start_line=f.get("start_line", chunk.start_line),
                end_line=f.get("end_line", chunk.end_line),
                suggestion=f.get("suggestion", ""),
                code_snippet=f.get("code_snippet", "")
            ))
        
        return findings

    def _build_prompt(self, chunk: CodeChunk) -> str:
        """Build the analysis prompt for a chunk"""
        return f"""
Analyze the following {chunk.language} code from {chunk.file_path} (lines {chunk.start_line}-{chunk.end_line}):

```{chunk.language}
{chunk.content}
```

Return ONLY a JSON object.
Do NOT include explanations.
Do NOT include markdown.
Do NOT include comments.

The JSON must strictly follow this schema:
{{
    "findings": [
        {{
            "severity": "critical" | "high" | "medium" | "low" | "info",
            "category": string,
            "title": string,
            "description": string,
            "start_line": {chunk.start_line},
            "end_line": number,
            "suggestion": string,
            "code_snippet": string
        }}
    ]
}}

If no issues found, return {{"findings": []}}
"""
