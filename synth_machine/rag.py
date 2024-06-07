from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel


class RAGConfig(BaseModel):
    collection_name: Optional[str] = None
    filters: List[dict] = []
    n: int = 3


class RAG(ABC):
    @abstractmethod
    async def embed(self, documents: List[str], metadata: Optional[List[dict]] = None):
        raise NotImplementedError()

    @abstractmethod
    async def query(self, prompt: str, rag_config: RAGConfig = RAGConfig()):
        raise NotImplementedError()
