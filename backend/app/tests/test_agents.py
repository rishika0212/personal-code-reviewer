import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agents.code_analyzer import CodeAnalyzerAgent
from agents.security_agent import SecurityAgent
from agents.optimization_agent import OptimizationAgent
from agents.base_agent import AgentFinding
from indexing.chunker import CodeChunk


@pytest.fixture
def sample_chunk():
    return CodeChunk(
        content="""
def calculate_total(items):
    total = 0
    for item in items:
        total += item.price
    return total
""",
        file_path="test.py",
        start_line=1,
        end_line=6,
        language="python",
        metadata={"chunk_index": 0}
    )


@pytest.fixture
def mock_llm_response():
    return '''
{
    "findings": [
        {
            "severity": "medium",
            "category": "error-handling",
            "title": "Missing null check",
            "description": "The function does not check if items is None",
            "start_line": 1,
            "end_line": 2,
            "suggestion": "Add a null check at the start of the function",
            "code_snippet": "def calculate_total(items):"
        }
    ]
}
'''


class TestCodeAnalyzer:
    @pytest.mark.asyncio
    async def test_analyze_returns_findings(self, sample_chunk, mock_llm_response):
        agent = CodeAnalyzerAgent()
        
        with patch.object(agent.llm, 'generate', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = mock_llm_response
            
            findings = await agent.analyze([sample_chunk])
            
            assert len(findings) == 1
            assert findings[0].severity == "medium"
            assert findings[0].category == "error-handling"


class TestSecurityAgent:
    @pytest.mark.asyncio
    async def test_security_analysis(self, sample_chunk):
        agent = SecurityAgent()
        
        mock_response = '''
{
    "findings": []
}
'''
        
        with patch.object(agent.llm, 'generate', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = mock_response
            
            findings = await agent.analyze([sample_chunk])
            
            assert len(findings) == 0


class TestOptimizationAgent:
    def test_default_prompt_exists(self):
        agent = OptimizationAgent()
        assert agent.system_prompt is not None
        assert "performance" in agent.system_prompt.lower()
