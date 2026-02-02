# Agent Design

## Overview

The Coder system uses a multi-agent architecture where specialized AI agents analyze different aspects of the codebase in parallel.

## Agent Types

### 1. Code Analyzer Agent
**Purpose**: Detect bugs, code smells, and maintainability issues

**Focus Areas**:
- Logic errors and potential bugs
- Null/undefined reference errors
- Off-by-one errors
- Race conditions
- Resource leaks
- Dead code
- Complex conditional logic
- Magic numbers
- Missing error handling

**Severity Mapping**:
- Critical: Definite runtime failure
- High: Likely production issue
- Medium: Code smell or potential bug
- Low: Minor improvement
- Info: Best practice suggestion

### 2. Security Agent
**Purpose**: Identify security vulnerabilities

**Focus Areas** (OWASP Top 10):
- SQL Injection
- Cross-Site Scripting (XSS)
- Command Injection
- Insecure Deserialization
- Hardcoded Secrets
- Weak Cryptography
- Path Traversal
- SSRF
- XXE
- Broken Access Control

**Output Format**:
- CWE reference when applicable
- Exploitation scenario
- Remediation steps

### 3. Optimization Agent
**Purpose**: Find performance bottlenecks

**Focus Areas**:
- Algorithm complexity (O(n²) → O(n))
- N+1 database queries
- Missing indexes
- Blocking I/O
- Memory leaks
- Missing caching
- Unnecessary computations
- Inefficient data structures

## Agent Base Class

```python
class BaseAgent(ABC):
    def __init__(self, name: str, prompt_file: str):
        self.name = name
        self.llm = LLMService()
        self._load_prompt()
    
    @abstractmethod
    def _get_default_prompt(self) -> str:
        pass
    
    async def analyze(self, chunks: List[CodeChunk]) -> List[AgentFinding]:
        findings = []
        for chunk in chunks:
            chunk_findings = await self._analyze_chunk(chunk)
            findings.extend(chunk_findings)
        return findings
```

## Prompt Engineering

Each agent uses a carefully crafted system prompt that:
1. Defines the agent's expertise and role
2. Lists specific issues to look for
3. Defines severity levels
4. Specifies output format (JSON)
5. Provides examples when helpful

## Finding Schema

```python
@dataclass
class AgentFinding:
    severity: str      # critical, high, medium, low, info
    category: str      # Type of issue
    title: str         # Brief description
    description: str   # Detailed explanation
    file_path: str     # File location
    start_line: int    # Start line
    end_line: int      # End line
    suggestion: str    # How to fix
    code_snippet: str  # Relevant code
```

## Coordination

The `ReviewManager` orchestrates agents:

1. Loads and chunks the codebase
2. Indexes chunks in ChromaDB
3. Dispatches chunks to each agent in parallel
4. Collects and deduplicates findings
5. Sorts by severity
6. Returns aggregated results

## Future Improvements

- [ ] Agent specialization by language
- [ ] Cross-file analysis for dependency issues
- [ ] Auto-fix suggestions with code generation
- [ ] Learning from user feedback
- [ ] Custom agent configuration
