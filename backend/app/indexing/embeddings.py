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
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding, returning empty list")
            return []
        
        # Hard limit on text length to avoid context window errors (approx 8k tokens)
        if len(text) > 8000:
            logger.warning(f"Text too long ({len(text)} chars), truncating to 8000 chars for embedding")
            text = text[:8000]

        try:
            async with httpx.AsyncClient() as client:
                # Prefer /api/embed (newer) over /api/embeddings (legacy)
                try:
                    response = await client.post(
                        f"{self.ollama_host}/api/embed",
                        json={
                            "model": self.model,
                            "input": text
                        },
                        timeout=30.0
                    )
                    
                    if response.status_code == 404:
                        # Fallback to legacy endpoint if /api/embed is not available
                        response = await client.post(
                            f"{self.ollama_host}/api/embeddings",
                            json={
                                "model": self.model,
                                "prompt": text
                            },
                            timeout=30.0
                        )
                    
                    response.raise_for_status()
                    data = response.json()
                    
                    # Handle different response formats
                    if "embeddings" in data and data["embeddings"]:
                        return data["embeddings"][0]
                    elif "embedding" in data:
                        return data["embedding"]
                    else:
                        logger.error(f"Unexpected embedding response format: {data.keys()}")
                        raise ValueError("Unexpected embedding response format")

                except httpx.HTTPStatusError:
                    logger.exception(f"Embedding failed for text length {len(text)}")
                    raise
        except Exception:
            logger.exception(f"Embedding failed for text length {len(text)}")
            raise
    
    async def is_available(self) -> bool:
        """Check if the embedding service is available and model is pulled"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.ollama_host}/api/tags",
                    timeout=10.0
                )
                if response.status_code != 200:
                    return False
                
                # Check if model exists
                models = [m["name"] for m in response.json().get("models", [])]
                has_model = any(self.model in m for m in models)
                if not has_model:
                    logger.warning(f"Embedding model {self.model} not found in Ollama. Pull it with: ollama pull {self.model}")
                return has_model
        except Exception as e:
            logger.warning(f"Ollama availability check failed: {e}")
            return False
    
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
        except Exception:
            logger.exception("Embedding failed")
            raise
