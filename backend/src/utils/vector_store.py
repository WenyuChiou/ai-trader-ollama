# src/utils/vector_store.py
"""
向量存储系统 - 用于RAG系统的语义搜索
使用numpy-based实现（轻量级，无需FAISS）
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple
import json
import numpy as np
from pathlib import Path
from datetime import datetime, date
import pickle
import gzip


class VectorStore:
    """
    向量存储系统
    使用numpy实现向量索引和相似度搜索
    """
    
    def __init__(self, root: Path, embedding_dim: int = 384):
        """
        初始化向量存储
        
        参数:
        - root: 存储根目录
        - embedding_dim: embedding维度
        """
        self.root = Path(root)
        self.embedding_dim = embedding_dim
        self.vectors_dir = self.root / "memory" / "vectors"
        self.vectors_dir.mkdir(parents=True, exist_ok=True)
        
        # 内存中的向量和元数据
        self.vectors: np.ndarray = np.array([])  # shape: (n, embedding_dim)
        self.metadata: List[Dict[str, Any]] = []  # 每个向量对应的元数据
        self.date_to_index: Dict[str, int] = {}  # 日期到索引的映射
        
        # 加载现有向量
        self._load_vectors()
    
    def _load_vectors(self) -> None:
        """从磁盘加载向量"""
        vectors_file = self.vectors_dir / "vectors.npy"
        metadata_file = self.vectors_dir / "metadata.json"
        
        if vectors_file.exists() and metadata_file.exists():
            try:
                self.vectors = np.load(vectors_file)
                with metadata_file.open("r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
                
                # 重建日期索引
                for idx, meta in enumerate(self.metadata):
                    date_str = meta.get("date")
                    if date_str:
                        self.date_to_index[date_str] = idx
                
                print(f"[VECTOR STORE] Loaded {len(self.vectors)} vectors")
            except Exception as e:
                print(f"[VECTOR STORE WARN] Failed to load vectors: {e}")
                self.vectors = np.array([])
                self.metadata = []
    
    def _save_vectors(self) -> None:
        """保存向量到磁盘"""
        if len(self.vectors) == 0:
            return
        
        try:
            vectors_file = self.vectors_dir / "vectors.npy"
            metadata_file = self.vectors_dir / "metadata.json"
            
            np.save(vectors_file, self.vectors)
            with metadata_file.open("w", encoding="utf-8") as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
            
            print(f"[VECTOR STORE] Saved {len(self.vectors)} vectors")
        except Exception as e:
            print(f"[VECTOR STORE ERROR] Failed to save vectors: {e}")
    
    def add_vector(
        self,
        embedding: List[float],
        metadata: Dict[str, Any],
        date_str: Optional[str] = None,
    ) -> int:
        """
        添加向量
        
        参数:
        - embedding: embedding向量
        - metadata: 元数据（包含date, symbol, stance等）
        - date_str: 日期字符串（如果metadata中没有）
        
        返回:
        - 向量索引
        """
        if len(embedding) != self.embedding_dim:
            raise ValueError(
                f"Embedding dimension mismatch: expected {self.embedding_dim}, "
                f"got {len(embedding)}"
            )
        
        # 检查是否已存在（基于日期）
        date_key = date_str or metadata.get("date")
        if date_key and date_key in self.date_to_index:
            # 更新现有向量
            idx = self.date_to_index[date_key]
            self.vectors[idx] = np.array(embedding)
            self.metadata[idx] = metadata
            return idx
        
        # 添加新向量
        new_vector = np.array(embedding).reshape(1, -1)
        if len(self.vectors) == 0:
            self.vectors = new_vector
        else:
            self.vectors = np.vstack([self.vectors, new_vector])
        
        self.metadata.append(metadata)
        idx = len(self.metadata) - 1
        
        if date_key:
            self.date_to_index[date_key] = idx
        
        return idx
    
    def search_similar(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        date_filter: Optional[Tuple[str, str]] = None,
        symbol_filter: Optional[str] = None,
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        搜索相似向量
        
        参数:
        - query_embedding: 查询向量
        - top_k: 返回top k结果
        - date_filter: 日期范围过滤 (start_date, end_date)
        - symbol_filter: 股票代码过滤
        
        返回:
        - (metadata, similarity_score) 列表，按相似度降序排列
        """
        if len(self.vectors) == 0:
            return []
        
        if len(query_embedding) != self.embedding_dim:
            raise ValueError(
                f"Query embedding dimension mismatch: expected {self.embedding_dim}, "
                f"got {len(query_embedding)}"
            )
        
        # 计算余弦相似度
        query_vec = np.array(query_embedding).reshape(1, -1)
        
        # 归一化向量（用于余弦相似度）
        query_norm = query_vec / (np.linalg.norm(query_vec, axis=1, keepdims=True) + 1e-8)
        vectors_norm = self.vectors / (np.linalg.norm(self.vectors, axis=1, keepdims=True) + 1e-8)
        
        # 计算相似度
        similarities = np.dot(vectors_norm, query_norm.T).flatten()
        
        # 应用过滤
        filtered_indices = []
        for idx, meta in enumerate(self.metadata):
            # 日期过滤
            if date_filter:
                meta_date = meta.get("date", "")
                start_date, end_date = date_filter
                if meta_date < start_date or meta_date > end_date:
                    continue
            
            # 股票过滤
            if symbol_filter:
                stocks = meta.get("stocks_involved", []) + meta.get("recommended_stocks", [])
                if symbol_filter.upper() not in [s.upper() for s in stocks]:
                    continue
            
            filtered_indices.append(idx)
        
        # 获取top k结果
        if not filtered_indices:
            return []
        
        filtered_similarities = similarities[filtered_indices]
        top_indices = np.argsort(filtered_similarities)[::-1][:top_k]
        
        results = []
        for top_idx in top_indices:
            original_idx = filtered_indices[top_idx]
            results.append((
                self.metadata[original_idx],
                float(filtered_similarities[top_idx])
            ))
        
        return results
    
    def remove_by_date(self, date_str: str) -> bool:
        """根据日期删除向量"""
        if date_str not in self.date_to_index:
            return False
        
        idx = self.date_to_index[date_str]
        
        # 删除向量和元数据
        self.vectors = np.delete(self.vectors, idx, axis=0)
        self.metadata.pop(idx)
        
        # 重建日期索引
        self.date_to_index = {}
        for i, meta in enumerate(self.metadata):
            meta_date = meta.get("date")
            if meta_date:
                self.date_to_index[meta_date] = i
        
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_vectors": len(self.vectors),
            "embedding_dimension": self.embedding_dim,
            "storage_size_mb": self._estimate_size(),
        }
    
    def _estimate_size(self) -> float:
        """估算存储大小（MB）"""
        if len(self.vectors) == 0:
            return 0.0
        
        # 向量大小 + 元数据大小
        vector_size = self.vectors.nbytes / 1024 / 1024
        metadata_size = len(json.dumps(self.metadata)) / 1024 / 1024
        return round(vector_size + metadata_size, 2)
    
    def save(self) -> None:
        """保存向量存储"""
        self._save_vectors()

