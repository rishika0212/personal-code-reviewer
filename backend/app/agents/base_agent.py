from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass

from services.llm_service import LLMService
from indexing.chunker import CodeChunk
from utils.logger import logger


@dataclass
class AgentFinding:
    """Represents a single finding from an agent"""
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
    
    async def analyze(self, chunks: List[CodeChunk]) -> List[AgentFinding]:
        """Analyze code chunks and return findings"""
        findings = []
        
        for chunk in chunks:
            try:
                chunk_findings = await self._analyze_chunk(chunk)
                findings.extend(chunk_findings)
            except Exception as e:
                logger.error(f"Error analyzing chunk: {e}")
        
        return findings
    
    async def _analyze_chunk(self, chunk: CodeChunk) -> List[AgentFinding]:
        """Analyze a single code chunk"""
        prompt = self._build_prompt(chunk)
        
        response = await self.llm.generate(
            system_prompt=self.system_prompt,
            user_prompt=prompt
        )
        
        return self._parse_response(response, chunk)
    
    def _build_prompt(self, chunk: CodeChunk) -> str:
        """Build the analysis prompt for a chunk"""
        return f"""
Analyze the following {chunk.language} code from {chunk.file_path} (lines {chunk.start_line}-{chunk.end_line}):

```{chunk.language}
{chunk.content}
```

Provide your analysis in the following JSON format:
{{
    "findings": [
        {{
            "severity": "critical|high|medium|low|info",
            "category": "category name",
            "title": "brief title",
            "description": "detailed description",
            "start_line": {chunk.start_line},
            "end_line": line number,
            "suggestion": "how to fix",
            "code_snippet": "relevant code"
        }}
    ]
}}

If no issues found, return {{"findings": []}}
"""
    
    def _parse_response(
        self,
        response: str,
        chunk: CodeChunk
    ) -> List[AgentFinding]:
        """Parse LLM response into findings"""
        import json
        
        try:
            # Try to extract JSON from response
            start = response.find("{")
            end = response.rfind("}") + 1
            
            if start >= 0 and end > start:
                data = json.loads(response[start:end])
                findings = []
                
                for f in data.get("findings", []):
                    findings.append(AgentFinding(
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
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse response: {e}")
        
        return []
