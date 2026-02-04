from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings

from config import settings
from indexing.chunker import CodeChunk
from utils.logger import logger


class ChromaStore:
    """ChromaDB vector store for code embeddings"""
    
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIRECTORY,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self._collections: Dict[str, Any] = {}
    
    def get_or_create_collection(self, name: str):
        """Get or create a collection"""
        if name not in self._collections:
            self._collections[name] = self.client.get_or_create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"}
            )
        return self._collections[name]
    
    def add_chunks(
        self,
        collection_name: str,
        chunks: List[CodeChunk],
        embeddings: List[List[float]]
    ):
        """Add code chunks to the vector store"""
        collection = self.get_or_create_collection(collection_name)
        
        ids = [f"{chunk.file_path}:{chunk.start_line}" for chunk in chunks]
        documents = [chunk.content for chunk in chunks]
        metadatas = [
            {
                "file_path": chunk.file_path,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "language": chunk.language,
                **chunk.metadata
            }
            for chunk in chunks
        ]
        
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        
        logger.info(f"Added {len(chunks)} chunks to collection {collection_name}")
    
    def query(
        self,
        collection_name: str,
        query_embedding: List[float],
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Query similar code chunks"""
        collection = self.get_or_create_collection(collection_name)
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            include=["documents", "metadatas", "distances"]
        )
        
        return results
    
    def get_all_chunks(
        self,
        collection_name: str,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get all chunks from a collection"""
        collection = self.get_or_create_collection(collection_name)
        
        return collection.get(
            where=where,
            include=["documents", "metadatas"]
        )
    
    def delete_collection(self, collection_name: str):
        """Delete a collection"""
        try:
            self.client.delete_collection(collection_name)
            if collection_name in self._collections:
                del self._collections[collection_name]
            logger.info(f"Deleted collection {collection_name}")
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
            raise


# Singleton instance
chroma_store = ChromaStore()
