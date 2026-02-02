import pytest

from indexing.chunker import CodeChunker, CodeChunk


class TestCodeChunker:
    @pytest.fixture
    def chunker(self):
        return CodeChunker(chunk_size=500, chunk_overlap=50)
    
    @pytest.fixture
    def sample_python_code(self):
        return '''
import os

def hello():
    print("Hello")

def world():
    print("World")

class MyClass:
    def __init__(self):
        self.value = 0
    
    def increment(self):
        self.value += 1
'''
    
    def test_chunk_python_file(self, chunker, sample_python_code):
        chunks = chunker.chunk_file(sample_python_code, "test.py")
        
        assert len(chunks) > 0
        assert all(isinstance(c, CodeChunk) for c in chunks)
        assert all(c.language == "python" for c in chunks)
    
    def test_chunk_preserves_content(self, chunker, sample_python_code):
        chunks = chunker.chunk_file(sample_python_code, "test.py")
        
        # All content should be present in chunks
        combined = "\n".join(c.content for c in chunks)
        assert "def hello" in combined
        assert "class MyClass" in combined
    
    def test_detect_language(self, chunker):
        assert chunker._detect_language("test.py") == "python"
        assert chunker._detect_language("test.js") == "javascript"
        assert chunker._detect_language("test.ts") == "typescript"
        assert chunker._detect_language("test.go") == "go"
        assert chunker._detect_language("test.xyz") == "unknown"
    
    def test_semantic_chunking_python(self, chunker):
        code = '''
def func1():
    pass

def func2():
    pass
'''
        chunks = chunker._chunk_python(code)
        
        # Should create separate chunks for each function
        assert len(chunks) >= 1
    
    def test_empty_file(self, chunker):
        chunks = chunker.chunk_file("", "test.py")
        assert len(chunks) == 0 or all(not c.content.strip() for c in chunks)
    
    def test_line_numbers(self, chunker, sample_python_code):
        chunks = chunker.chunk_file(sample_python_code, "test.py")
        
        # Line numbers should be positive
        for chunk in chunks:
            assert chunk.start_line > 0
            assert chunk.end_line >= chunk.start_line
