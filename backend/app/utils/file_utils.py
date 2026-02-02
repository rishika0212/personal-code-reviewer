import os
import shutil
from pathlib import Path
from typing import Optional


def ensure_dir(path: str) -> Path:
    """Ensure a directory exists, creating it if necessary"""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def safe_delete(path: str) -> bool:
    """Safely delete a file or directory"""
    try:
        p = Path(path)
        if p.is_file():
            p.unlink()
        elif p.is_dir():
            shutil.rmtree(p)
        return True
    except Exception:
        return False


def get_file_extension(filename: str) -> str:
    """Get the file extension (lowercase, with dot)"""
    return Path(filename).suffix.lower()


def get_file_size(path: str) -> Optional[int]:
    """Get file size in bytes, or None if file doesn't exist"""
    try:
        return os.path.getsize(path)
    except OSError:
        return None


def read_file_safe(path: str, encoding: str = 'utf-8') -> Optional[str]:
    """Read file content, returning None on error"""
    try:
        with open(path, 'r', encoding=encoding) as f:
            return f.read()
    except Exception:
        return None


def write_file_safe(
    path: str,
    content: str,
    encoding: str = 'utf-8'
) -> bool:
    """Write content to file, returning success status"""
    try:
        ensure_dir(str(Path(path).parent))
        with open(path, 'w', encoding=encoding) as f:
            f.write(content)
        return True
    except Exception:
        return False


def list_files_recursive(
    directory: str,
    extensions: Optional[set] = None
) -> list:
    """List all files in directory recursively"""
    files = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            if extensions is None or get_file_extension(filename) in extensions:
                files.append(os.path.join(root, filename))
    return files
