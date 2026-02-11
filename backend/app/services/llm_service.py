from typing import Optional, Dict, Any
import httpx

from config import settings
from utils.logger import logger


class LLMService:
    """Service for interacting with Ollama/Llama 3"""
    
    def __init__(self):
        self.host = settings.OLLAMA_HOST
        self.model = settings.LLM_MODEL
    
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: int = 2048
    ) -> str:
        """Generate a response from the LLM"""
        if temperature is None:
            temperature = settings.LLM_TEMPERATURE
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.host}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": user_prompt,
                        "system": system_prompt,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens,
                            "num_ctx": settings.LLM_CONTEXT_WINDOW
                        }
                    },
                    timeout=60.0
                )
                response.raise_for_status()
                return response.json()["response"]
        except httpx.TimeoutException:
            logger.error("LLM request timed out")
            raise
        except Exception:
            logger.exception("LLM request failed")
            raise
    
    async def chat(
        self,
        messages: list,
        temperature: Optional[float] = None,
        max_tokens: int = 2048
    ) -> str:
        """Chat completion with message history"""
        if temperature is None:
            temperature = settings.LLM_TEMPERATURE
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.host}/api/chat",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens,
                            "num_ctx": settings.LLM_CONTEXT_WINDOW
                        }
                    },
                    timeout=60.0
                )
                response.raise_for_status()
                return response.json()["message"]["content"]
        except Exception:
            logger.exception("Chat request failed")
            raise
    
    def generate_sync(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None
    ) -> str:
        """Synchronous version of generate"""
        if temperature is None:
            temperature = settings.LLM_TEMPERATURE
            
        try:
            with httpx.Client() as client:
                response = client.post(
                    f"{self.host}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": user_prompt,
                        "system": system_prompt,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_ctx": settings.LLM_CONTEXT_WINDOW
                        }
                    },
                    timeout=60.0
                )
                response.raise_for_status()
                return response.json()["response"]
        except Exception:
            logger.exception("LLM request failed")
            raise
    
    async def is_available(self) -> bool:
        """Check if the LLM service is available and model is pulled"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.host}/api/tags",
                    timeout=10.0
                )
                if response.status_code != 200:
                    return False
                
                # Check if model exists
                models = [m["name"] for m in response.json().get("models", [])]
                # Some versions of ollama return "model:latest", others just "model"
                has_model = any(self.model in m for m in models)
                if not has_model:
                    logger.warning(f"Model {self.model} not found in Ollama. Pull it with: ollama pull {self.model}")
                return has_model
        except Exception as e:
            logger.warning(f"Ollama connection check failed: {e}")
            return False
