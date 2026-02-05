"""
Embedding provider interface and implementations.

Provides text embedding generation for semantic skill matching.
"""
import logging
import os
from abc import ABC, abstractmethod
from typing import List, Protocol
from openai import AzureOpenAI, OpenAI

logger = logging.getLogger(__name__)


class EmbeddingProvider(Protocol):
    """Protocol for embedding providers."""
    
    def embed(self, text: str) -> List[float]:
        """
        Generate embedding vector for text.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of floats representing the embedding vector
            
        Raises:
            Exception: If embedding generation fails
        """
        ...


class OpenAIEmbeddingProvider:
    """OpenAI embedding provider implementation."""
    
    def __init__(self, api_key: str = None, model: str = "text-embedding-3-small"):
        """
        Initialize OpenAI embedding provider.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model name for embeddings
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        
        if not self.api_key:
            raise ValueError("OpenAI API key not provided and OPENAI_API_KEY env var not set")
        
        self.client = OpenAI(api_key=self.api_key)
        logger.info(f"Initialized OpenAI embedding provider with model: {self.model}")
    
    def embed(self, text: str) -> List[float]:
        """Generate embedding using OpenAI API."""
        try:
            response = self.client.embeddings.create(
                input=text,
                model=self.model
            )
            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding for text: '{text[:50]}...' (dim={len(embedding)})")
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding for text '{text[:50]}...': {e}")
            raise


class AzureOpenAIEmbeddingProvider:
    """Azure OpenAI embedding provider implementation."""
    
    def __init__(
        self,
        api_key: str = None,
        endpoint: str = None,
        deployment: str = None,
        api_version: str = "2024-02-01"
    ):
        """
        Initialize Azure OpenAI embedding provider.
        
        Args:
            api_key: Azure OpenAI API key (defaults to AZURE_OPENAI_API_KEY env var)
            endpoint: Azure OpenAI endpoint (defaults to AZURE_OPENAI_ENDPOINT env var)
            deployment: Deployment name (defaults to AZURE_OPENAI_EMBEDDING_DEPLOYMENT env var)
            api_version: API version
        """
        self.api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY")
        self.endpoint = endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
        self.deployment = deployment or os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small")
        self.api_version = api_version
        
        if not self.api_key:
            raise ValueError("Azure OpenAI API key not provided and AZURE_OPENAI_API_KEY env var not set")
        if not self.endpoint:
            raise ValueError("Azure OpenAI endpoint not provided and AZURE_OPENAI_ENDPOINT env var not set")
        
        self.client = AzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.endpoint
        )
        logger.info(f"Initialized Azure OpenAI embedding provider with deployment: {self.deployment}")
    
    def embed(self, text: str) -> List[float]:
        """Generate embedding using Azure OpenAI API."""
        try:
            response = self.client.embeddings.create(
                input=text,
                model=self.deployment
            )
            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding for text: '{text[:50]}...' (dim={len(embedding)})")
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding for text '{text[:50]}...': {e}")
            raise


class FakeEmbeddingProvider:
    """Fake embedding provider for testing."""
    
    def __init__(self, dimension: int = 1536, deterministic: bool = True):
        """
        Initialize fake embedding provider.
        
        Args:
            dimension: Embedding vector dimension
            deterministic: If True, same text always returns same embedding
        """
        self.dimension = dimension
        self.deterministic = deterministic
        self._cache = {}
        logger.info(f"Initialized fake embedding provider (dim={dimension}, deterministic={deterministic})")
    
    def embed(self, text: str) -> List[float]:
        """Generate fake embedding (for testing only)."""
        if self.deterministic and text in self._cache:
            return self._cache[text]
        
        # Generate deterministic embedding based on text hash
        if self.deterministic:
            import hashlib
            hash_value = int(hashlib.md5(text.encode()).hexdigest(), 16)
            # Use hash to seed a simple generator
            embedding = [(hash_value * (i + 1)) % 1000 / 1000.0 for i in range(self.dimension)]
        else:
            import random
            embedding = [random.random() for _ in range(self.dimension)]
        
        if self.deterministic:
            self._cache[text] = embedding
        
        logger.debug(f"Generated fake embedding for text: '{text[:50]}...' (dim={len(embedding)})")
        return embedding


def create_embedding_provider(
    provider_type: str = None,
    **kwargs
) -> EmbeddingProvider:
    """
    Factory function to create embedding provider.
    
    Args:
        provider_type: Type of provider ("openai", "azure_openai", "fake")
                      Defaults to EMBEDDING_PROVIDER env var or "azure_openai"
        **kwargs: Additional arguments for provider initialization
        
    Returns:
        EmbeddingProvider instance
        
    Raises:
        ValueError: If provider_type is unknown
    """
    provider_type = provider_type or os.getenv("EMBEDDING_PROVIDER", "azure_openai")
    
    if provider_type == "openai":
        return OpenAIEmbeddingProvider(**kwargs)
    elif provider_type == "azure_openai":
        return AzureOpenAIEmbeddingProvider(**kwargs)
    elif provider_type == "fake":
        return FakeEmbeddingProvider(**kwargs)
    else:
        raise ValueError(f"Unknown embedding provider type: {provider_type}")
