from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = True
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # Ollama / LLM
    OLLAMA_HOST: str = "http://127.0.0.1:11434"
    LLM_MODEL: str = "llama3"
    EMBEDDING_MODEL: str = "nomic-embed-text"
    LLM_CONTEXT_WINDOW: int = 4096
    LLM_TEMPERATURE: float = 0.2
    
    # Storage
    DATA_DIR: str = "../data"
    CHROMA_PERSIST_DIRECTORY: str = "../data/chroma_db"
    CLONE_DIR: str = "../data/repos"
    STATUS_FILE: str = "../data/status.json"
    RESULTS_FILE: str = "../data/results.json"
    REVIEWS_FILE: str = "../data/reviews.json"
    
    # GitHub
    GITHUB_TOKEN: str = ""
    
    # Agent Settings
    MAX_CHUNKS_PER_REVIEW: int = 20
    MAX_CHUNKS_TOTAL: int = 100
    MAX_FILES_PER_REVIEW: int = 30
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    class Config:
        env_file = ".env"


settings = Settings()
