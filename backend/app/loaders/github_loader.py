import os
import shutil
import uuid
import httpx
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional

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
        self._recover_repos()
    
    def _recover_repos(self):
        """Recover existing repositories from clone directory"""
        if not self.clone_dir.exists():
            return
            
        for item in self.clone_dir.iterdir():
            if item.is_dir() and len(item.name) == 8:
                self._repos[item.name] = item
                logger.info(f"Recovered repository: {item.name}")
    
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
            
            # Use asyncio.to_thread to avoid blocking the event loop with synchronous git clone
            import asyncio
            repo = await asyncio.to_thread(Repo.clone_from, url, target_dir, depth=1)
            
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
        return self._build_file_tree(repo_dir, repo_dir)
    
    def get_file_content(self, repo_id: str, file_path: str) -> str:
        """Get the content of a specific file"""
        if repo_id not in self._repos:
            raise ValueError(f"Repository {repo_id} not found")
        
        full_path = self._repos[repo_id] / file_path
        return full_path.read_text(encoding='utf-8')
    
    def apply_patch(self, repo_id: str, file_path: str, content: str):
        """Apply a patch by overwriting the file content"""
        if repo_id not in self._repos:
            raise ValueError(f"Repository {repo_id} not found")
            
        full_path = self._repos[repo_id] / file_path
        if not full_path.exists():
            raise ValueError(f"File {file_path} not found in repository")
            
        full_path.write_text(content, encoding='utf-8')
        logger.info(f"Applied patch to {file_path} in repo {repo_id}")

    def get_repo_url(self, repo_id: str) -> str:
        """Get the original URL for a cloned repository"""
        if repo_id not in self._repos:
            raise ValueError(f"Repository {repo_id} not found")
            
        repo = Repo(self._repos[repo_id])
        return repo.remotes.origin.url

    async def create_pull_request(
        self, 
        repo_id: str, 
        repo_url: str,
        title: str,
        body: str,
        base_branch: str = "main"
    ) -> str:
        """Create a new branch, push changes, and open a PR"""
        if repo_id not in self._repos:
            raise ValueError(f"Repository {repo_id} not found")
            
        if not settings.GITHUB_TOKEN:
            raise ValueError("GITHUB_TOKEN is not configured")
            
        repo_dir = self._repos[repo_id]
        repo = Repo(repo_dir)
        
        # 1. Create a unique branch name
        branch_name = f"zencoder-fix-{uuid.uuid4().hex[:6]}"
        new_branch = repo.create_head(branch_name)
        new_branch.checkout()
        
        # 2. Commit changes
        repo.git.add(A=True)
        repo.index.commit(title)
        
        # 3. Push to remote
        # Update remote URL to include token if not already present
        origin = repo.remote(name='origin')
        url = repo_url
        if "https://" in url and settings.GITHUB_TOKEN:
            url = url.replace("https://", f"https://{settings.GITHUB_TOKEN}@")
        
        origin.set_url(url)
        
        # Push in thread to avoid blocking
        await asyncio.to_thread(origin.push, refspec=f"{branch_name}:{branch_name}")
        
        # 4. Create PR via GitHub API
        # Extract owner/repo from URL
        # e.g., https://github.com/owner/repo.git -> owner/repo
        parts = repo_url.rstrip("/").replace(".git", "").split("/")
        if len(parts) < 2:
            raise ValueError(f"Invalid repository URL: {repo_url}")
        
        owner_repo = f"{parts[-2]}/{parts[-1]}"
        api_url = f"https://api.github.com/repos/{owner_repo}/pulls"
        
        headers = {
            "Authorization": f"token {settings.GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        payload = {
            "title": title,
            "body": body,
            "head": branch_name,
            "base": base_branch
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(api_url, headers=headers, json=payload)
            
            if response.status_code == 201:
                pr_data = response.json()
                logger.info(f"PR created successfully: {pr_data['html_url']}")
                return pr_data['html_url']
            else:
                error_detail = response.text
                logger.error(f"Failed to create PR: {response.status_code} - {error_detail}")
                raise RuntimeError(f"GitHub API error: {error_detail}")

    def _get_code_files(self, directory: Path) -> List[Path]:
        """Get all code files in directory"""
        files = []
        for path in directory.rglob("*"):
            if path.is_file() and self.file_filter.should_include(path):
                files.append(path)
        return files

    def _build_file_tree(self, directory: Path, repo_root: Path) -> List[Dict[str, Any]]:
        """Build a file tree structure"""
        tree = []
        for item in sorted(directory.iterdir()):
            if item.name.startswith("."):
                continue
            
            rel_path = str(item.relative_to(repo_root))
            
            if item.is_dir():
                if self.file_filter.should_include_dir(item):
                    tree.append({
                        "name": item.name,
                        "type": "directory",
                        "path": rel_path,
                        "children": self._build_file_tree(item, repo_root)
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


# Singleton instance
github_loader = GitHubLoader()
