# backend/services/optimized_vector_search.py
"""Optimized vector search service with caching and batch operations."""
from __future__ import annotations

import asyncio
import hashlib
from functools import lru_cache
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

import numpy as np
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.design_vector import DesignVector
from backend.services.embedding_service import EmbeddingService


@dataclass
class SearchResult:
    """Optimized search result with metadata."""
    vector_id: int
    score: float
    metadata: Dict[str, Any]
    vector: Optional[List[float]] = None


class VectorCache:
    """LRU cache for vector embeddings."""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: Dict[str, Tuple[List[float], float]] = {}  # hash -> (vector, timestamp)
        self._access_order: List[str] = []
    
    def get(self, vector_hash: str) -> Optional[List[float]]:
        """Get vector from cache."""
        if vector_hash in self._cache:
            # Move to end (most recently used)
            self._access_order.remove(vector_hash)
            self._access_order.append(vector_hash)
            return self._cache[vector_hash][0]
        return None
    
    def put(self, vector_hash: str, vector: List[float]) -> None:
        """Store vector in cache with LRU eviction."""
        import time
        
        if vector_hash in self._cache:
            # Update existing
            self._cache[vector_hash] = (vector, time.time())
            self._access_order.remove(vector_hash)
            self._access_order.append(vector_hash)
        else:
            # Add new
            if len(self._cache) >= self.max_size:
                # Evict least recently used
                lru_hash = self._access_order.pop(0)
                del self._cache[lru_hash]
            
            self._cache[vector_hash] = (vector, time.time())
            self._access_order.append(vector_hash)
    
    def clear(self) -> None:
        """Clear the cache."""
        self._cache.clear()
        self._access_order.clear()


class OptimizedVectorSearchService:
    """High-performance vector search with caching and optimization."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self._embedder = EmbeddingService()
        self._vector_cache = VectorCache(max_size=2000)
        self._similarity_cache = VectorCache(max_size=5000)
    
    @lru_cache(maxsize=100)
    def _compute_similarity(self, query_hash: str, vector_hash: str) -> float:
        """Cached cosine similarity computation."""
        # In a real implementation, you'd retrieve the actual vectors
        # This is a simplified version for demonstration
        return 0.0
    
    async def batch_similarity_search(
        self,
        queries: List[List[float]],
        k: int = 5,
        include_vectors: bool = False
    ) -> List[List[SearchResult]]:
        """Perform batch similarity search for multiple queries."""
        
        # Load all vectors once
        vectors_data = await self._load_all_vectors()
        
        # Convert to numpy for efficient computation
        query_matrix = np.array(queries)
        vector_matrix = np.array([v['vector'] for v in vectors_data])
        
        # Batch cosine similarity computation
        similarities = self._batch_cosine_similarity(query_matrix, vector_matrix)
        
        results = []
        for i, query_similarities in enumerate(similarities):
            # Get top-k results for this query
            top_k_indices = np.argsort(query_similarities)[-k:][::-1]
            
            query_results = []
            for idx in top_k_indices:
                vector_data = vectors_data[idx]
                result = SearchResult(
                    vector_id=vector_data['id'],
                    score=float(query_similarities[idx]),
                    metadata=vector_data['metadata'],
                    vector=vector_data['vector'] if include_vectors else None
                )
                query_results.append(result)
            
            results.append(query_results)
        
        return results
    
    async def similarity_search_optimized(
        self,
        query: List[float],
        k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
        min_score: float = 0.0
    ) -> List[SearchResult]:
        """Optimized similarity search with filtering."""
        
        # Generate cache key
        query_hash = self._hash_vector(query)
        cache_key = f"{query_hash}_{k}_{hash(str(filter_metadata))}_{min_score}"
        
        # Check cache first
        cached_result = self._similarity_cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # Build optimized query
        stmt = select(DesignVector).options(
            selectinload(DesignVector.metadata)  # Eager load if relation exists
        )
        
        # Apply metadata filters efficiently
        if filter_metadata:
            for key, value in filter_metadata.items():
                stmt = stmt.where(
                    DesignVector.meta[key].astext == str(value)
                )
        
        # Execute query
        result = await self.session.execute(stmt)
        vectors = result.scalars().all()
        
        # Compute similarities efficiently
        similarities = []
        for vector_obj in vectors:
            similarity = self._fast_cosine_similarity(query, vector_obj.vector)
            if similarity >= min_score:
                similarities.append((similarity, vector_obj))
        
        # Sort and take top-k
        similarities.sort(key=lambda x: x[0], reverse=True)
        top_k = similarities[:k]
        
        # Build results
        results = [
            SearchResult(
                vector_id=vector_obj.id,
                score=score,
                metadata=vector_obj.meta or {},
                vector=None
            )
            for score, vector_obj in top_k
        ]
        
        # Cache results
        self._similarity_cache.put(cache_key, results)
        
        return results
    
    async def _load_all_vectors(self) -> List[Dict[str, Any]]:
        """Load all vectors efficiently for batch operations."""
        stmt = select(DesignVector)
        result = await self.session.execute(stmt)
        vectors = result.scalars().all()
        
        return [
            {
                'id': v.id,
                'vector': v.vector,
                'metadata': v.meta or {}
            }
            for v in vectors
        ]
    
    @staticmethod
    def _batch_cosine_similarity(queries: np.ndarray, vectors: np.ndarray) -> np.ndarray:
        """Efficient batch cosine similarity computation."""
        # Normalize vectors
        queries_norm = queries / np.linalg.norm(queries, axis=1, keepdims=True)
        vectors_norm = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
        
        # Compute similarities
        similarities = np.dot(queries_norm, vectors_norm.T)
        return similarities
    
    @staticmethod
    def _fast_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Fast cosine similarity computation."""
        # Convert to numpy arrays
        a = np.array(vec1)
        b = np.array(vec2)
        
        # Compute cosine similarity
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)
    
    @staticmethod
    def _hash_vector(vector: List[float]) -> str:
        """Generate hash for vector caching."""
        vector_str = ','.join(f"{x:.6f}" for x in vector)
        return hashlib.md5(vector_str.encode()).hexdigest()
    
    async def precompute_similarities(self, batch_size: int = 100) -> None:
        """Precompute similarities for frequent queries."""
        # Load all vectors
        vectors_data = await self._load_all_vectors()
        
        # Process in batches
        for i in range(0, len(vectors_data), batch_size):
            batch = vectors_data[i:i + batch_size]
            
            # Precompute similarities within batch
            for j, vec1 in enumerate(batch):
                for k, vec2 in enumerate(batch):
                    if j != k:
                        similarity = self._fast_cosine_similarity(
                            vec1['vector'], 
                            vec2['vector']
                        )
                        # Cache the result
                        hash1 = self._hash_vector(vec1['vector'])
                        hash2 = self._hash_vector(vec2['vector'])
                        cache_key = f"{hash1}_{hash2}"
                        self._similarity_cache.put(cache_key, similarity)
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get search service statistics."""
        # Count total vectors
        count_stmt = select(DesignVector.id).count()
        total_vectors = await self.session.scalar(count_stmt)
        
        return {
            'total_vectors': total_vectors,
            'cache_size': len(self._vector_cache._cache),
            'similarity_cache_size': len(self._similarity_cache._cache),
            'cache_hit_rate': 0.0,  # Would track in production
        }


# Database optimization utilities
class DatabaseOptimizer:
    """Database query optimization utilities."""
    
    @staticmethod
    async def create_indexes(session: AsyncSession) -> None:
        """Create performance indexes."""
        
        indexes = [
            # Vector search optimization
            "CREATE INDEX IF NOT EXISTS idx_design_vector_meta ON design_vector USING GIN (meta)",
            
            # Component search optimization
            "CREATE INDEX IF NOT EXISTS idx_component_master_category_manufacturer ON component_master (category, manufacturer)",
            "CREATE INDEX IF NOT EXISTS idx_component_master_name_trgm ON component_master USING gin (name gin_trgm_ops)",
            
            # File asset optimization
            "CREATE INDEX IF NOT EXISTS idx_file_asset_parsing_status ON file_asset (parsing_status)",
            "CREATE INDEX IF NOT EXISTS idx_file_asset_uploaded_at ON file_asset (uploaded_at)",
            
            # AI action log optimization
            "CREATE INDEX IF NOT EXISTS idx_ai_action_log_timestamp ON ai_action_log (timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_ai_action_log_action_type ON ai_action_log (action_type)",
            
            # User authentication optimization
            "CREATE INDEX IF NOT EXISTS idx_users_email_active ON users (email, is_active)",
            "CREATE INDEX IF NOT EXISTS idx_users_organization ON users (organization)",
        ]
        
        for index_sql in indexes:
            try:
                await session.execute(text(index_sql))
                await session.commit()
            except Exception as e:
                print(f"Failed to create index: {e}")
                await session.rollback()
    
    @staticmethod
    async def analyze_tables(session: AsyncSession) -> None:
        """Update table statistics for query optimization."""
        
        tables = [
            'design_vector',
            'component_master', 
            'file_asset',
            'ai_action_log',
            'users'
        ]
        
        for table in tables:
            try:
                await session.execute(text(f"ANALYZE {table}"))
                await session.commit()
            except Exception as e:
                print(f"Failed to analyze table {table}: {e}")
                await session.rollback()


# Connection pooling optimization
class OptimizedSessionManager:
    """Optimized database session management."""
    
    def __init__(self, max_connections: int = 20):
        self.max_connections = max_connections
        self._connection_pool: List[AsyncSession] = []
        self._active_connections: int = 0
    
    async def get_session(self) -> AsyncSession:
        """Get optimized database session."""
        # Implementation would use proper connection pooling
        # This is a simplified version
        pass
    
    async def cleanup_idle_connections(self) -> None:
        """Clean up idle database connections."""
        # Implementation would clean up connections
        pass
