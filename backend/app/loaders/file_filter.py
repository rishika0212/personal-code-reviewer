from pathlib import Path
from typing import Set


class FileFilter:
    """Filter files for code review"""
    
    # Directories to ignore
    IGNORE_DIRS: Set[str] = {
        "node_modules",
        ".git",
        "__pycache__",
        ".venv",
        "venv",
        "env",
        ".idea",
        ".vscode",
        "dist",
        "build",
        "target",
        ".next",
        "coverage",
        ".pytest_cache",
        ".mypy_cache",
        "vendor",
        "packages"
    }
    
    # File extensions to include
    CODE_EXTENSIONS: Set[str] = {
        ".py", ".js", ".ts", ".tsx", ".jsx",
        ".java", ".go", ".rs", ".cpp", ".c", ".h",
        ".rb", ".php", ".swift", ".kt", ".scala",
        ".cs", ".vue", ".svelte"
    }
    
    # Files to ignore by name
    IGNORE_FILES: Set[str] = {
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "poetry.lock",
        "Pipfile.lock",
        ".DS_Store",
        "thumbs.db"
    }
    
    # Max file size in bytes (1MB)
    MAX_FILE_SIZE: int = 1024 * 1024
    
    def should_include(self, path: Path) -> bool:
        """Check if a file should be included in review"""
        # Check file name
        if path.name in self.IGNORE_FILES:
            return False
        
        # Check extension
        if path.suffix.lower() not in self.CODE_EXTENSIONS:
            return False
        
        # Check file size
        try:
            if path.stat().st_size > self.MAX_FILE_SIZE:
                return False
        except OSError:
            return False
        
        # Check parent directories
        for parent in path.parents:
            if parent.name in self.IGNORE_DIRS:
                return False
        
        return True
    
    def should_include_dir(self, path: Path) -> bool:
        """Check if a directory should be traversed"""
        return path.name not in self.IGNORE_DIRS
