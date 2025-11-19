# src/utils/embedding_generator.py
"""
Embedding Generator for RAG System Vectorization
Supports Ollama API and sentence-transformers as fallback
"""
from __future__ import annotations
from typing import List, Optional
import os
import sys
from pathlib import Path

# Add project path
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    import requests
except ImportError:
    requests = None

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None


class EmbeddingGenerator:
    """
    Embedding Generator
    
    Priority: Ollama API, fallback to sentence-transformers if unavailable
    """
    
    def __init__(
        self,
        ollama_host: Optional[str] = None,
        ollama_model: Optional[str] = None,
        fallback_model: str = "all-MiniLM-L6-v2",
    ):
        """
        Initialize Embedding Generator
        
        Args:
        - ollama_host: Ollama service URL (default: read from config)
        - ollama_model: Ollama model name (default: nomic-embed-text)
        - fallback_model: sentence-transformers model name
        """
        self.ollama_host = ollama_host or self._get_ollama_host()
        self.ollama_model = ollama_model or "nomic-embed-text"  # Ollama embedding model
        self.fallback_model = fallback_model
        self._fallback_transformer = None
        self._use_ollama = self._check_ollama_available()
    
    def _get_ollama_host(self) -> str:
        """Get Ollama host from config"""
        try:
            from src.utils.config_loader import load_config
            config = load_config()
            return config.get("llm", {}).get("ollama_host", "http://localhost:11434")
        except Exception:
            return "http://localhost:11434"
    
    def _check_ollama_available(self) -> bool:
        """Check if Ollama is available"""
        if not requests:
            return False
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=2)
            return response.status_code == 200
        except Exception:
            return False
    
    def _get_fallback_transformer(self):
        """Get fallback transformer (lazy loading)"""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers not available. "
                "Install with: pip install sentence-transformers"
            )
        if self._fallback_transformer is None:
            print(f"[EMBEDDING] Loading fallback model: {self.fallback_model}")
            self._fallback_transformer = SentenceTransformer(self.fallback_model)
        return self._fallback_transformer
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
        - text: Input text
        
        Returns:
        - Embedding vector (List[float])
        """
        if not text or not text.strip():
            # Return zero vector
            return [0.0] * 384  # Default dimension
        
        # Try Ollama first
        if self._use_ollama:
            try:
                return self._generate_with_ollama(text)
            except Exception as e:
                print(f"[EMBEDDING WARN] Ollama failed: {e}, using fallback")
                self._use_ollama = False
        
        # Fallback to sentence-transformers
        return self._generate_with_transformer(text)
    
    def _generate_with_ollama(self, text: str) -> List[float]:
        """Generate embedding using Ollama API"""
        if not requests:
            raise RuntimeError("requests library not available")
        
        # Ollama embedding API
        url = f"{self.ollama_host}/api/embeddings"
        payload = {
            "model": self.ollama_model,
            "prompt": text,
        }
        
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            raise RuntimeError(f"Ollama API error: {response.status_code}")
        
        data = response.json()
        if "embedding" not in data:
            raise RuntimeError("Ollama API did not return embedding")
        
        return data["embedding"]
    
    def _generate_with_transformer(self, text: str) -> List[float]:
        """Generate embedding using sentence-transformers"""
        transformer = self._get_fallback_transformer()
        embedding = transformer.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings in batch
        
        Args:
        - texts: List of texts
        
        Returns:
        - List of embedding vectors
        """
        if not texts:
            return []
        
        # Try Ollama (batch)
        if self._use_ollama:
            try:
                return self._generate_batch_with_ollama(texts)
            except Exception as e:
                print(f"[EMBEDDING WARN] Ollama batch failed: {e}, using fallback")
                self._use_ollama = False
        
        # Fallback to sentence-transformers (supports batch)
        transformer = self._get_fallback_transformer()
        embeddings = transformer.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return embeddings.tolist()
    
    def _generate_batch_with_ollama(self, texts: List[str]) -> List[List[float]]:
        """Generate batch embeddings using Ollama (sequential calls)"""
        embeddings = []
        for text in texts:
            embeddings.append(self._generate_with_ollama(text))
        return embeddings
    
    def get_embedding_dimension(self) -> int:
        """Get embedding dimension"""
        if self._use_ollama:
            # Ollama nomic-embed-text is typically 768 dimensions
            # But for compatibility, test with a sample first
            try:
                test_embedding = self.generate_embedding("test")
                return len(test_embedding)
            except Exception:
                pass
        
        # sentence-transformers all-MiniLM-L6-v2 is 384 dimensions
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                transformer = self._get_fallback_transformer()
                test_embedding = transformer.encode("test", convert_to_numpy=True)
                return len(test_embedding)
            except Exception:
                pass
        
        # Default dimension
        return 384
