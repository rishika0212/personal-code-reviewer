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
        "packages",
        "tmp",
        "temp",
        "logs",
        "obj",
        "bin"
    }
    
    # File extensions to include
    CODE_EXTENSIONS: Set[str] = {
        ".py", ".js", ".ts", ".tsx", ".jsx",
        ".java", ".go", ".rs", ".cpp", ".c", ".h",
        ".rb", ".php", ".swift", ".kt", ".scala",
        ".cs", ".vue", ".svelte"
    }

    # Patterns to ignore
    IGNORE_PATTERNS: Set[str] = {
        ".test.",
        ".spec.",
        ".min.js",
        ".lock",
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
    
    # Min file size in characters/bytes to avoid processing tiny/empty files
    MIN_FILE_SIZE: int = 50
    
    # Directories to exclude from analysis (e.g., the backend itself)
    EXCLUDED_PATHS: Set[str] = {
        "backend/app/agents",
        "backend/app/vectorstore",
        "backend/app/services",
        "backend/app/orchestrator",
        "backend/app/indexing",
        "backend/app/api",
        "backend/app/utils",
        "backend/app/loaders",
        "backend/app/schemas",
        "backend/app/prompts",
        "node_modules",
        "venv",
        ".venv"
    }
    
    # Keywords in paths that indicate infrastructure or boilerplate
    SKIP_KEYWORDS: Set[str] = {
        "/api/", "/services/", "/vectorstore/", "/agents/", 
        "\\api\\", "\\services\\", "\\vectorstore\\", "\\agents\\"
    }
    
    def should_include(self, path: Path) -> bool:
        """Check if a file should be included in review"""
        # Check patterns
        path_str = str(path).lower()
        for pattern in self.IGNORE_PATTERNS:
            if pattern in path_str:
                return False

        # Check keywords (Fix 1: More aggressive skipping)
        for keyword in self.SKIP_KEYWORDS:
            if keyword.lower() in path_str:
                return False

        # Check excluded paths (to avoid analyzing our own backend infra)
        path_posix = path.as_posix().lower()
        for excluded in self.EXCLUDED_PATHS:
            if excluded.lower() in path_posix:
                return False

        # Check file name
        if path.name in self.IGNORE_FILES:
            return False
        
        # Check extension
        ext = path.suffix.lower()
        if ext not in self.CODE_EXTENSIONS:
            # Only allow .json if it's not a lock file and it's small (added logic below)
            if ext == ".json":
                # Skip large json or common lock/config that we don't need
                if path.name in ("package.json", "tsconfig.json", "composer.json"):
                    pass # Keep these small configs
                else:
                    return False
            else:
                return False
        
        # Check file size
        try:
            file_size = path.stat().st_size
            if file_size > self.MAX_FILE_SIZE or file_size < self.MIN_FILE_SIZE:
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
