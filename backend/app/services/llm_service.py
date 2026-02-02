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
        temperature: float = 0.1,
        max_tokens: int = 2048
    ) -> str:
        """Generate a response from the LLM"""
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
                            "num_predict": max_tokens
                        }
                    },
                    timeout=120.0
                )
                response.raise_for_status()
                return response.json()["response"]
        except httpx.TimeoutException:
            logger.error("LLM request timed out")
            raise
        except Exception as e:
            logger.error(f"LLM request failed: {e}")
            raise
    
    async def chat(
        self,
        messages: list,
        temperature: float = 0.1,
        max_tokens: int = 2048
    ) -> str:
        """Chat completion with message history"""
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
                            "num_predict": max_tokens
                        }
                    },
                    timeout=120.0
                )
                response.raise_for_status()
                return response.json()["message"]["content"]
        except Exception as e:
            logger.error(f"Chat request failed: {e}")
            raise
    
    def generate_sync(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1
    ) -> str:
        """Synchronous version of generate"""
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
                            "temperature": temperature
                        }
                    },
                    timeout=120.0
                )
                response.raise_for_status()
                return response.json()["response"]
        except Exception as e:
            logger.error(f"LLM request failed: {e}")
            raise
    
    async def is_available(self) -> bool:
        """Check if the LLM service is available"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.host}/api/tags",
                    timeout=5.0
                )
                return response.status_code == 200
        except Exception:
            return False
