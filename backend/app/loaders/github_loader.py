import os
import shutil
import uuid
from pathlib import Path
from typing import List, Dict, Any

from git import Repo
from config import settings
from schemas.repo import RepoInfo
from loaders.file_filter import FileFilter
from utils.logger import logger


class GitHubLoader:
    """Handles cloning and loading GitHub repositories"""
    
    def __init__(self):
        self.clone_dir = Path(settings.CLONE_DIR)
        self.clone_dir.mkdir(parents=True, exist_ok=True)
        self.file_filter = FileFilter()
        self._repos: Dict[str, Path] = {}
    
    async def clone_repo(self, url: str) -> RepoInfo:
        """Clone a GitHub repository"""
        repo_id = str(uuid.uuid4())[:8]
        target_dir = self.clone_dir / repo_id
        
        try:
            logger.info(f"Cloning {url} to {target_dir}")
            
            # Clone the repository
            if settings.GITHUB_TOKEN:
                # Insert token for private repos
                url = url.replace("https://", f"https://{settings.GITHUB_TOKEN}@")
            
            repo = Repo.clone_from(url, target_dir, depth=1)
            
            # Get file list
            files = self._get_code_files(target_dir)
            
            self._repos[repo_id] = target_dir
            
            return RepoInfo(
                repo_id=repo_id,
                name=url.split("/")[-1].replace(".git", ""),
                url=url,
                files_count=len(files),
                languages=self._detect_languages(files)
            )
        except Exception as e:
            logger.error(f"Clone failed: {e}")
            if target_dir.exists():
                shutil.rmtree(target_dir)
            raise
    
    def get_file_tree(self, repo_id: str) -> List[Dict[str, Any]]:
        """Get the file tree for a repository"""
        if repo_id not in self._repos:
            raise ValueError(f"Repository {repo_id} not found")
        
        repo_dir = self._repos[repo_id]
        return self._build_file_tree(repo_dir)
    
    def get_file_content(self, repo_id: str, file_path: str) -> str:
        """Get the content of a specific file"""
        if repo_id not in self._repos:
            raise ValueError(f"Repository {repo_id} not found")
        
        full_path = self._repos[repo_id] / file_path
        return full_path.read_text(encoding='utf-8')
    
    def _get_code_files(self, directory: Path) -> List[Path]:
        """Get all code files in directory"""
        files = []
        for path in directory.rglob("*"):
            if path.is_file() and self.file_filter.should_include(path):
                files.append(path)
        return files
    
    def _build_file_tree(self, directory: Path, prefix: str = "") -> List[Dict[str, Any]]:
        """Build a file tree structure"""
        tree = []
        for item in sorted(directory.iterdir()):
            if item.name.startswith("."):
                continue
            
            rel_path = str(item.relative_to(self._repos.get(prefix, directory)))
            
            if item.is_dir():
                if self.file_filter.should_include_dir(item):
                    tree.append({
                        "name": item.name,
                        "type": "directory",
                        "path": rel_path,
                        "children": self._build_file_tree(item, prefix)
                    })
            elif self.file_filter.should_include(item):
                tree.append({
                    "name": item.name,
                    "type": "file",
                    "path": rel_path
                })
        return tree
    
    def _detect_languages(self, files: List[Path]) -> List[str]:
        """Detect programming languages from file extensions"""
        extensions = {f.suffix.lower() for f in files}
        
        lang_map = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".tsx": "TypeScript",
            ".jsx": "JavaScript",
            ".java": "Java",
            ".go": "Go",
            ".rs": "Rust",
            ".cpp": "C++",
            ".c": "C",
            ".rb": "Ruby",
            ".php": "PHP"
        }
        
        return list({lang_map.get(ext) for ext in extensions if ext in lang_map})
    
    def cleanup(self, repo_id: str):
        """Clean up a cloned repository"""
        if repo_id in self._repos:
            shutil.rmtree(self._repos[repo_id], ignore_errors=True)
            del self._repos[repo_id]
