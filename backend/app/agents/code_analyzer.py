from typing import List

from agents.base_agent import BaseAgent, AgentFinding
from indexing.chunker import CodeChunk


class CodeAnalyzerAgent(BaseAgent):
    """Agent for detecting bugs and code smells"""
    
    def __init__(self):
        super().__init__(
            name="Code Analyzer",
            prompt_file="code_analysis.txt"
        )
    
    def _get_default_prompt(self) -> str:
        return """You are an expert code reviewer specializing in finding bugs, code smells, and maintainability issues.

Your responsibilities:
1. Identify potential bugs and logic errors
2. Detect code smells (long methods, duplicated code, etc.)
3. Check for proper error handling
4. Evaluate code readability and maintainability
5. Identify anti-patterns and bad practices

Focus on:
- Null/undefined reference errors
- Off-by-one errors
- Race conditions
- Resource leaks
- Improper exception handling
- Dead code
- Complex conditional logic
- Magic numbers and hardcoded values

Be specific about the issue location and provide actionable suggestions."""


class CodeAnalyzer(CodeAnalyzerAgent):
    """Alias for backward compatibility"""
    pass
