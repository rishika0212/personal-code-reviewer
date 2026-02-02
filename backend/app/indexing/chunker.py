from typing import List, Dict, Any
from dataclasses import dataclass

from config import settings


@dataclass
class CodeChunk:
    """Represents a chunk of code"""
    content: str
    file_path: str
    start_line: int
    end_line: int
    language: str
    metadata: Dict[str, Any]


class CodeChunker:
    """Chunks code files for processing"""
    
    def __init__(
        self,
        chunk_size: int = settings.CHUNK_SIZE,
        chunk_overlap: int = settings.CHUNK_OVERLAP
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk_file(self, content: str, file_path: str) -> List[CodeChunk]:
        """Chunk a file into smaller pieces"""
        language = self._detect_language(file_path)
        lines = content.split("\n")
        chunks = []
        
        # Try semantic chunking first (by functions/classes)
        semantic_chunks = self._semantic_chunk(content, language)
        
        if semantic_chunks:
            for i, (start, end, chunk_content) in enumerate(semantic_chunks):
                chunks.append(CodeChunk(
                    content=chunk_content,
                    file_path=file_path,
                    start_line=start,
                    end_line=end,
                    language=language,
                    metadata={"chunk_index": i, "chunk_type": "semantic"}
                ))
        else:
            # Fall back to line-based chunking
            chunks = self._line_chunk(lines, file_path, language)
        
        return chunks
    
    def _semantic_chunk(self, content: str, language: str) -> List[tuple]:
        """Try to chunk by semantic units (functions, classes)"""
        chunks = []
        
        if language == "python":
            chunks = self._chunk_python(content)
        elif language in ("javascript", "typescript"):
            chunks = self._chunk_javascript(content)
        
        return chunks
    
    def _chunk_python(self, content: str) -> List[tuple]:
        """Chunk Python code by functions and classes"""
        import re
        
        chunks = []
        lines = content.split("\n")
        
        # Find function and class definitions
        pattern = r'^(class |def |async def )'
        current_start = 0
        
        for i, line in enumerate(lines):
            if re.match(pattern, line) and i > 0:
                # Save previous chunk
                chunk_content = "\n".join(lines[current_start:i])
                if chunk_content.strip():
                    chunks.append((current_start + 1, i, chunk_content))
                current_start = i
        
        # Add last chunk
        if current_start < len(lines):
            chunk_content = "\n".join(lines[current_start:])
            if chunk_content.strip():
                chunks.append((current_start + 1, len(lines), chunk_content))
        
        return chunks
    
    def _chunk_javascript(self, content: str) -> List[tuple]:
        """Chunk JavaScript/TypeScript code"""
        import re
        
        chunks = []
        lines = content.split("\n")
        
        # Find function, class, and const/let definitions
        pattern = r'^(export |)(class |function |const |let |async function )'
        current_start = 0
        
        for i, line in enumerate(lines):
            if re.match(pattern, line.strip()) and i > 0:
                chunk_content = "\n".join(lines[current_start:i])
                if chunk_content.strip():
                    chunks.append((current_start + 1, i, chunk_content))
                current_start = i
        
        # Add last chunk
        if current_start < len(lines):
            chunk_content = "\n".join(lines[current_start:])
            if chunk_content.strip():
                chunks.append((current_start + 1, len(lines), chunk_content))
        
        return chunks
    
    def _line_chunk(
        self,
        lines: List[str],
        file_path: str,
        language: str
    ) -> List[CodeChunk]:
        """Fall back to line-based chunking"""
        chunks = []
        total_lines = len(lines)
        
        # Calculate lines per chunk based on character size
        avg_line_length = sum(len(l) for l in lines) / max(len(lines), 1)
        lines_per_chunk = max(10, int(self.chunk_size / max(avg_line_length, 1)))
        overlap_lines = max(2, int(self.chunk_overlap / max(avg_line_length, 1)))
        
        start = 0
        chunk_index = 0
        
        while start < total_lines:
            end = min(start + lines_per_chunk, total_lines)
            chunk_content = "\n".join(lines[start:end])
            
            chunks.append(CodeChunk(
                content=chunk_content,
                file_path=file_path,
                start_line=start + 1,
                end_line=end,
                language=language,
                metadata={"chunk_index": chunk_index, "chunk_type": "line"}
            ))
            
            start = end - overlap_lines
            chunk_index += 1
        
        return chunks
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension"""
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".jsx": "javascript",
            ".java": "java",
            ".go": "go",
            ".rs": "rust",
            ".cpp": "cpp",
            ".c": "c",
            ".rb": "ruby",
            ".php": "php"
        }
        
        for ext, lang in ext_map.items():
            if file_path.endswith(ext):
                return lang
        
        return "unknown"
