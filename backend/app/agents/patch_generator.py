import json
from typing import List, Dict, Any, Optional
from agents.base_agent import BaseAgent
from schemas.review import ReviewFinding
from services.llm_service import LLMService
from utils.logger import logger
from utils.file_utils import extract_context

class PatchGeneratorAgent:
    """Agent that generates code patches based on review findings"""
    
    def __init__(self):
        self.name = "Patch Generator"
        self.prompt_file = "patch_generation.txt"
        self.llm = LLMService()
        self._load_prompt()
    
    def _load_prompt(self):
        """Load the system prompt from file"""
        try:
            with open(f"prompts/{self.prompt_file}", "r") as f:
                self.system_prompt = f.read()
        except FileNotFoundError:
            logger.warning(f"Prompt file not found: {self.prompt_file}")
            self.system_prompt = "You are an expert coder. Fix the following issue in the code snippet."
    
    async def generate_patch(
        self,
        file_path: str,
        original_code: str,
        finding: ReviewFinding
    ) -> Dict[str, Any]:
        """Generate a patch for a specific finding using context window"""
        
        # Extract context around the finding (±5 lines to keep prompt small)
        context = extract_context(original_code, finding.start_line, window=5)
        
        user_prompt = f"""
Issue: {finding.title} - {finding.description}
Fix: {finding.suggestion}
File: {file_path} (lines {finding.start_line}-{finding.end_line})

Code:
```
{context}
```
Return ONLY the full modified code snippet. No JSON, no markdown, no explanation.
"""
        
        response = await self.llm.generate(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            max_tokens=600  # Limit output length
        )
        
        try:
            # Clean response (remove markdown blocks if LLM ignores instructions)
            content = response.strip()
            if "```" in content:
                # Extract content between triple backticks if present
                if "```" in content:
                    parts = content.split("```")
                    if len(parts) >= 3:
                        content = parts[1]
                        # Remove language tag if present (e.g., ```python)
                        if "\n" in content:
                            content = content.split("\n", 1)[1]
            
            # Construct the final result (Raw string mode)
            return {
                "patch": content,
                "original_snippet": context,
                "confidence": 0.95,
                "explanation": "Applied AI fix",
                "finding_id": finding.id
            }
        except Exception as e:
            logger.error(f"Failed to parse patch generator response: {e}")
            return {
                "patch": context,
                "original_snippet": context,
                "confidence": 0.0,
                "explanation": f"Failed to generate patch: {str(e)}",
                "finding_id": finding.id
            }
