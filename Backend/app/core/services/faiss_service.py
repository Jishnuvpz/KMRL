"""
FAISS Vector Database Service for Semantic Search
Provides high-performance semantic search capabilities using Facebook's FAISS library
"""
import os
import json
import pickle
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import logging
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    faiss = None
    
    # Create a mock faiss module to prevent import-time type annotation errors
    class MockFAISS:
        class Index:
            pass
    faiss = MockFAISS()

logger = logging.getLogger(__name__)

class FAISSVectorDB:
    """
    FAISS-based vector database for semantic search
    Supports both flat and hierarchical clustering for different use cases
    """
    
    def __init__(
        self, 
        dimension: int = 384,  # Default for all-MiniLM-L6-v2
        index_type: str = "flat",  # "flat", "ivf", "hnsw"
        index_path: str = "data/faiss_indices",
        max_vectors: int = 1000000
    ):
        if not FAISS_AVAILABLE:
            raise ImportError("FAISS not available. Install with: pip install faiss-cpu faiss-gpu")
        
        self.dimension = dimension
        self.index_type = index_type
        self.index_path = Path(index_path)
        self.max_vectors = max_vectors
        
        # Create directories
        self.index_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize indices
        self.document_index = None
        self.chunk_index = None
        
        # Metadata storage
        self.document_metadata = {}  # doc_id -> metadata
        self.chunk_metadata = {}     # chunk_id -> metadata
        
        # Thread pool for async operations
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Load existing indices
        self._load_indices()
        
        logger.info(f"FAISS Vector DB initialized with dimension={dimension}, type={index_type}")
    
    def _create_index(self, index_name: str) -> faiss.Index:
        """Create a new FAISS index based on configuration"""
        
        if self.index_type == "flat":
            # Flat index - exact search, good for smaller datasets
            index = faiss.IndexFlatIP(self.dimension)  # Inner Product (cosine similarity)
            
        elif self.index_type == "ivf":
            # IVF (Inverted File) - approximate search, good for large datasets
            nlist = min(100, max(1, self.max_vectors // 10000))  # Number of clusters
            quantizer = faiss.IndexFlatIP(self.dimension)
            index = faiss.IndexIVFFlat(quantizer, self.dimension, nlist)
            
        elif self.index_type == "hnsw":
            # HNSW - hierarchical navigable small world, very fast approximate search
            index = faiss.IndexHNSWFlat(self.dimension, 32)  # 32 connections per node
            index.hnsw.efSearch = 64  # Search parameter
            
        else:
            raise ValueError(f"Unsupported index type: {self.index_type}")
        
        logger.info(f"Created {self.index_type} index for {index_name}")
        return index
    
    def _load_indices(self):
        """Load existing FAISS indices and metadata"""
        try:
            # Load document index
            doc_index_file = self.index_path / "documents.index"
            doc_metadata_file = self.index_path / "documents_metadata.json"
            
            if doc_index_file.exists() and doc_metadata_file.exists():
                self.document_index = faiss.read_index(str(doc_index_file))
                with open(doc_metadata_file, 'r') as f:
                    self.document_metadata = json.load(f)
                logger.info(f"Loaded document index with {self.document_index.ntotal} vectors")
            else:
                self.document_index = self._create_index("documents")
            
            # Load chunk index
            chunk_index_file = self.index_path / "chunks.index"
            chunk_metadata_file = self.index_path / "chunks_metadata.json"
            
            if chunk_index_file.exists() and chunk_metadata_file.exists():
                self.chunk_index = faiss.read_index(str(chunk_index_file))
                with open(chunk_metadata_file, 'r') as f:
                    self.chunk_metadata = json.load(f)
                logger.info(f"Loaded chunk index with {self.chunk_index.ntotal} vectors")
            else:
                self.chunk_index = self._create_index("chunks")
                
        except Exception as e:
            logger.error(f"Error loading indices: {e}")
            # Create new indices if loading fails
            self.document_index = self._create_index("documents")
            self.chunk_index = self._create_index("chunks")
    
    def _save_indices(self):
        """Save FAISS indices and metadata to disk"""
        try:
            # Save document index
            doc_index_file = self.index_path / "documents.index"
            doc_metadata_file = self.index_path / "documents_metadata.json"
            
            faiss.write_index(self.document_index, str(doc_index_file))
            with open(doc_metadata_file, 'w') as f:
                json.dump(self.document_metadata, f, indent=2, default=str)
            
            # Save chunk index
            chunk_index_file = self.index_path / "chunks.index"
            chunk_metadata_file = self.index_path / "chunks_metadata.json"
            
            faiss.write_index(self.chunk_index, str(chunk_index_file))
            with open(chunk_metadata_file, 'w') as f:
                json.dump(self.chunk_metadata, f, indent=2, default=str)
            
            logger.info("FAISS indices saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving indices: {e}")
    
    async def add_document_embedding(
        self, 
        document_id: str, 
        embedding: np.ndarray, 
        metadata: Dict[str, Any]
    ) -> bool:
        """Add a document embedding to the FAISS index"""
        try:
            # Ensure embedding is correct shape
            if embedding.ndim == 1:
                embedding = embedding.reshape(1, -1)
            
            if embedding.shape[1] != self.dimension:
                raise ValueError(f"Embedding dimension {embedding.shape[1]} doesn't match index dimension {self.dimension}")
            
            # Normalize for cosine similarity
            faiss.normalize_L2(embedding)
            
            # Add to index
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor, 
                self.document_index.add, 
                embedding.astype(np.float32)
            )
            
            # Store metadata
            vector_id = self.document_index.ntotal - 1
            self.document_metadata[str(vector_id)] = {
                "document_id": document_id,
                "timestamp": time.time(),
                **metadata
            }
            
            logger.debug(f"Added document {document_id} to FAISS index at position {vector_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding document embedding {document_id}: {e}")
            return False
    
    async def add_chunk_embedding(
        self, 
        document_id: str, 
        chunk_id: str, 
        embedding: np.ndarray, 
        metadata: Dict[str, Any]
    ) -> bool:
        """Add a document chunk embedding to the FAISS index"""
        try:
            # Ensure embedding is correct shape
            if embedding.ndim == 1:
                embedding = embedding.reshape(1, -1)
            
            if embedding.shape[1] != self.dimension:
                raise ValueError(f"Embedding dimension {embedding.shape[1]} doesn't match index dimension {self.dimension}")
            
            # Normalize for cosine similarity
            faiss.normalize_L2(embedding)
            
            # Add to index
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor, 
                self.chunk_index.add, 
                embedding.astype(np.float32)
            )
            
            # Store metadata
            vector_id = self.chunk_index.ntotal - 1
            self.chunk_metadata[str(vector_id)] = {
                "document_id": document_id,
                "chunk_id": chunk_id,
                "timestamp": time.time(),
                **metadata
            }
            
            logger.debug(f"Added chunk {chunk_id} to FAISS index at position {vector_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding chunk embedding {chunk_id}: {e}")
            return False
    
    async def search_documents(
        self, 
        query_embedding: np.ndarray, 
        k: int = 10,
        score_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """Search for similar documents using FAISS"""
        try:
            if self.document_index.ntotal == 0:
                return []
            
            # Ensure query embedding is correct shape
            if query_embedding.ndim == 1:
                query_embedding = query_embedding.reshape(1, -1)
            
            # Normalize for cosine similarity
            faiss.normalize_L2(query_embedding)
            
            # Perform search
            loop = asyncio.get_event_loop()
            scores, indices = await loop.run_in_executor(
                self.executor,
                self.document_index.search,
                query_embedding.astype(np.float32),
                min(k, self.document_index.ntotal)
            )
            
            # Process results
            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx >= 0 and score >= score_threshold:  # Valid result
                    metadata = self.document_metadata.get(str(idx), {})
                    results.append({
                        "rank": i + 1,
                        "score": float(score),
                        "vector_id": int(idx),
                        "document_id": metadata.get("document_id"),
                        "metadata": metadata
                    })
            
            logger.debug(f"Document search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    async def search_chunks(
        self, 
        query_embedding: np.ndarray, 
        k: int = 20,
        score_threshold: float = 0.0,
        document_filter: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar document chunks using FAISS"""
        try:
            if self.chunk_index.ntotal == 0:
                return []
            
            # Ensure query embedding is correct shape
            if query_embedding.ndim == 1:
                query_embedding = query_embedding.reshape(1, -1)
            
            # Normalize for cosine similarity
            faiss.normalize_L2(query_embedding)
            
            # Perform search (get more results for filtering)
            search_k = min(k * 3, self.chunk_index.ntotal) if document_filter else min(k, self.chunk_index.ntotal)
            
            loop = asyncio.get_event_loop()
            scores, indices = await loop.run_in_executor(
                self.executor,
                self.chunk_index.search,
                query_embedding.astype(np.float32),
                search_k
            )
            
            # Process and filter results
            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx >= 0 and score >= score_threshold:  # Valid result
                    metadata = self.chunk_metadata.get(str(idx), {})
                    document_id = metadata.get("document_id")
                    
                    # Apply document filter if specified
                    if document_filter and document_id not in document_filter:
                        continue
                    
                    results.append({
                        "rank": len(results) + 1,
                        "score": float(score),
                        "vector_id": int(idx),
                        "document_id": document_id,
                        "chunk_id": metadata.get("chunk_id"),
                        "metadata": metadata
                    })
                    
                    # Stop when we have enough results
                    if len(results) >= k:
                        break
            
            logger.debug(f"Chunk search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error searching chunks: {e}")
            return []
    
    async def remove_document(self, document_id: str) -> bool:
        """Remove all embeddings for a document"""
        try:
            # Note: FAISS doesn't support efficient deletion
            # In production, you'd need to rebuild the index periodically
            # For now, we'll mark as deleted in metadata
            
            removed_count = 0
            
            # Mark document embeddings as deleted
            for vector_id, metadata in self.document_metadata.items():
                if metadata.get("document_id") == document_id:
                    metadata["deleted"] = True
                    removed_count += 1
            
            # Mark chunk embeddings as deleted
            for vector_id, metadata in self.chunk_metadata.items():
                if metadata.get("document_id") == document_id:
                    metadata["deleted"] = True
                    removed_count += 1
            
            logger.info(f"Marked {removed_count} embeddings as deleted for document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing document {document_id}: {e}")
            return False
    
    async def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the FAISS indices"""
        try:
            # Count active (non-deleted) embeddings
            active_docs = sum(1 for m in self.document_metadata.values() if not m.get("deleted", False))
            active_chunks = sum(1 for m in self.chunk_metadata.values() if not m.get("deleted", False))
            
            return {
                "document_index": {
                    "total_vectors": self.document_index.ntotal,
                    "active_vectors": active_docs,
                    "dimension": self.dimension,
                    "index_type": self.index_type
                },
                "chunk_index": {
                    "total_vectors": self.chunk_index.ntotal,
                    "active_vectors": active_chunks,
                    "dimension": self.dimension,
                    "index_type": self.index_type
                },
                "storage_path": str(self.index_path),
                "max_vectors": self.max_vectors
            }
            
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            return {}
    
    async def rebuild_indices(self) -> bool:
        """Rebuild indices to remove deleted embeddings"""
        try:
            logger.info("Starting index rebuild to remove deleted embeddings...")
            
            # This is a simplified rebuild - in production you'd want more sophisticated logic
            old_doc_count = self.document_index.ntotal
            old_chunk_count = self.chunk_index.ntotal
            
            # For now, just clean up metadata
            self.document_metadata = {
                vid: meta for vid, meta in self.document_metadata.items() 
                if not meta.get("deleted", False)
            }
            self.chunk_metadata = {
                vid: meta for vid, meta in self.chunk_metadata.items() 
                if not meta.get("deleted", False)
            }
            
            # Save cleaned indices
            self._save_indices()
            
            logger.info(f"Index rebuild completed. Docs: {old_doc_count} -> {len(self.document_metadata)}, "
                       f"Chunks: {old_chunk_count} -> {len(self.chunk_metadata)}")
            return True
            
        except Exception as e:
            logger.error(f"Error rebuilding indices: {e}")
            return False
    
    def save(self):
        """Synchronous save method"""
        self._save_indices()
    
    async def close(self):
        """Close the vector database and save indices"""
        try:
            self._save_indices()
            self.executor.shutdown(wait=True)
            logger.info("FAISS Vector DB closed successfully")
        except Exception as e:
            logger.error(f"Error closing FAISS Vector DB: {e}")

# Global FAISS service instance
faiss_vector_db = None

def get_faiss_service(
    dimension: int = 384,
    index_type: str = "flat",
    index_path: str = "data/faiss_indices"
) -> FAISSVectorDB:
    """Get or create global FAISS service instance"""
    global faiss_vector_db
    
    if faiss_vector_db is None:
        faiss_vector_db = FAISSVectorDB(
            dimension=dimension,
            index_type=index_type,
            index_path=index_path
        )
    
    return faiss_vector_db

# Utility functions for different search strategies

async def hybrid_search(
    query_embedding: np.ndarray,
    document_embeddings_weight: float = 0.3,
    chunk_embeddings_weight: float = 0.7,
    k: int = 10
) -> List[Dict[str, Any]]:
    """
    Perform hybrid search combining document-level and chunk-level results
    """
    faiss_service = get_faiss_service()
    
    # Search both indices
    doc_results = await faiss_service.search_documents(query_embedding, k=k//2)
    chunk_results = await faiss_service.search_chunks(query_embedding, k=k)
    
    # Combine and rerank results
    combined_results = []
    
    # Add document results with weight
    for result in doc_results:
        result["final_score"] = result["score"] * document_embeddings_weight
        result["search_type"] = "document"
        combined_results.append(result)
    
    # Add chunk results with weight
    for result in chunk_results:
        result["final_score"] = result["score"] * chunk_embeddings_weight
        result["search_type"] = "chunk"
        combined_results.append(result)
    
    # Sort by final score and deduplicate by document_id
    combined_results.sort(key=lambda x: x["final_score"], reverse=True)
    
    # Deduplicate while preserving best score per document
    seen_docs = set()
    final_results = []
    
    for result in combined_results:
        doc_id = result.get("document_id")
        if doc_id and doc_id not in seen_docs:
            seen_docs.add(doc_id)
            final_results.append(result)
            
            if len(final_results) >= k:
                break
    
    return final_results