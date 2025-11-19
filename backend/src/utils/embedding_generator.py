# src/utils/embedding_generator.py
"""
Embedding生成器 - 用于RAG系统的向量化
支持Ollama API和sentence-transformers两种方式
"""
from __future__ import annotations
from typing import List, Optional
import os
import sys
from pathlib import Path

# 添加项目路径
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
    Embedding生成器
    优先使用Ollama API，如果不可用则fallback到sentence-transformers
    """
    
    def __init__(
        self,
        ollama_host: Optional[str] = None,
        ollama_model: Optional[str] = None,
        fallback_model: str = "all-MiniLM-L6-v2",
    ):
        """
        初始化Embedding生成器
        
        参数:
        - ollama_host: Ollama服务地址（默认从config读取）
        - ollama_model: Ollama模型名称（默认使用deepseek-r1或nomic-embed-text）
        - fallback_model: sentence-transformers模型名称
        """
        self.ollama_host = ollama_host or self._get_ollama_host()
        self.ollama_model = ollama_model or "nomic-embed-text"  # Ollama的embedding模型
        self.fallback_model = fallback_model
        self._fallback_transformer = None
        self._use_ollama = self._check_ollama_available()
    
    def _get_ollama_host(self) -> str:
        """从config获取Ollama host"""
        try:
            from src.utils.config_loader import load_config
            config = load_config()
            return config.get("llm", {}).get("ollama_host", "http://localhost:11434")
        except Exception:
            return "http://localhost:11434"
    
    def _check_ollama_available(self) -> bool:
        """检查Ollama是否可用"""
        if not requests:
            return False
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=2)
            return response.status_code == 200
        except Exception:
            return False
    
    def _get_fallback_transformer(self):
        """获取fallback transformer（懒加载）"""
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
        生成单个文本的embedding
        
        参数:
        - text: 输入文本
        
        返回:
        - embedding向量（List[float]）
        """
        if not text or not text.strip():
            # 返回零向量
            return [0.0] * 384  # 默认维度
        
        # 尝试使用Ollama
        if self._use_ollama:
            try:
                return self._generate_with_ollama(text)
            except Exception as e:
                print(f"[EMBEDDING WARN] Ollama failed: {e}, using fallback")
                self._use_ollama = False
        
        # Fallback到sentence-transformers
        return self._generate_with_transformer(text)
    
    def _generate_with_ollama(self, text: str) -> List[float]:
        """使用Ollama API生成embedding"""
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
        """使用sentence-transformers生成embedding"""
        transformer = self._get_fallback_transformer()
        embedding = transformer.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        批量生成embeddings
        
        参数:
        - texts: 文本列表
        
        返回:
        - embedding向量列表
        """
        if not texts:
            return []
        
        # 尝试使用Ollama（批量）
        if self._use_ollama:
            try:
                return self._generate_batch_with_ollama(texts)
            except Exception as e:
                print(f"[EMBEDDING WARN] Ollama batch failed: {e}, using fallback")
                self._use_ollama = False
        
        # Fallback到sentence-transformers（支持批量）
        transformer = self._get_fallback_transformer()
        embeddings = transformer.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return embeddings.tolist()
    
    def _generate_batch_with_ollama(self, texts: List[str]) -> List[List[float]]:
        """使用Ollama批量生成（逐个调用）"""
        embeddings = []
        for text in texts:
            embeddings.append(self._generate_with_ollama(text))
        return embeddings
    
    def get_embedding_dimension(self) -> int:
        """获取embedding维度"""
        if self._use_ollama:
            # Ollama nomic-embed-text通常是768维
            # 但为了兼容性，先测试一个样本
            try:
                test_embedding = self.generate_embedding("test")
                return len(test_embedding)
            except Exception:
                pass
        
        # sentence-transformers all-MiniLM-L6-v2是384维
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                transformer = self._get_fallback_transformer()
                test_embedding = transformer.encode("test", convert_to_numpy=True)
                return len(test_embedding)
            except Exception:
                pass
        
        # 默认维度
        return 384

