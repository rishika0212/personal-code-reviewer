from typing import List
import httpx

from config import settings
from utils.logger import logger


class EmbeddingService:
    """Generate embeddings for code chunks"""
    
    def __init__(self):
        self.model = settings.EMBEDDING_MODEL
        self.ollama_host = settings.OLLAMA_HOST
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ollama_host}/api/embeddings",
                    json={
                        "model": self.model,
                        "prompt": text
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()["embedding"]
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            raise
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        embeddings = []
        for text in texts:
            embedding = await self.embed_text(text)
            embeddings.append(embedding)
        return embeddings
    
    def embed_text_sync(self, text: str) -> List[float]:
        """Synchronous version of embed_text"""
        try:
            with httpx.Client() as client:
                response = client.post(
                    f"{self.ollama_host}/api/embeddings",
                    json={
                        "model": self.model,
                        "prompt": text
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()["embedding"]
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            raise
