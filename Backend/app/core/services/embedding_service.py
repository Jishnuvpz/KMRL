"""
Embedding Service for generating text embeddings using Sentence Transformers
Supports multiple models and embedding strategies for semantic search
"""
import asyncio
import logging
import time
from typing import List, Dict, Any, Optional, Tuple, Union
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import re
from pathlib import Path

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None

logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    Service for generating text embeddings using Sentence Transformers
    Supports multiple models and chunking strategies
    """
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",  # Fast, good quality model
        cache_dir: str = "models/sentence_transformers",
        max_seq_length: int = 512,
        batch_size: int = 32,
        device: str = "auto"
    ):
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError("sentence-transformers not available. Install with: pip install sentence-transformers")
        
        self.model_name = model_name
        self.cache_dir = Path(cache_dir)
        self.max_seq_length = max_seq_length
        self.batch_size = batch_size
        self.device = device
        
        # Create cache directory
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize model
        self.model = None
        self.model_dimension = None
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # Text preprocessing settings
        self.min_chunk_length = 50
        self.max_chunk_length = 1000
        self.overlap_length = 50
        
        logger.info(f"Embedding service initialized with model: {model_name}")
    
    async def load_model(self) -> bool:
        """Load the sentence transformer model"""
        try:
            if self.model is not None:
                return True
            
            logger.info(f"Loading embedding model: {self.model_name}")
            start_time = time.time()
            
            # Load model in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                self.executor,
                self._load_model_sync
            )
            
            # Set model properties
            self.model_dimension = self.model.get_sentence_embedding_dimension()
            
            load_time = time.time() - start_time
            logger.info(f"Model {self.model_name} loaded successfully in {load_time:.2f}s, dimension: {self.model_dimension}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading embedding model: {e}")
            return False
    
    def _load_model_sync(self) -> SentenceTransformer:
        """Synchronous model loading"""
        # Determine device
        if self.device == "auto":
            if TORCH_AVAILABLE and torch.cuda.is_available():
                device = "cuda"
            else:
                device = "cpu"
        else:
            device = self.device
        
        # Load model
        model = SentenceTransformer(
            self.model_name,
            cache_folder=str(self.cache_dir),
            device=device
        )
        
        # Set max sequence length
        if hasattr(model, 'max_seq_length'):
            model.max_seq_length = self.max_seq_length
        
        return model
    
    async def generate_embedding(
        self, 
        text: str, 
        normalize: bool = True
    ) -> Optional[np.ndarray]:
        """Generate embedding for a single text"""
        try:
            if not await self.load_model():
                return None
            
            if not text or not text.strip():
                return None
            
            # Preprocess text
            text = self._preprocess_text(text)
            
            # Generate embedding
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                self.executor,
                self._encode_text,
                [text],
                normalize
            )
            
            return embedding[0] if embedding is not None and len(embedding) > 0 else None
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    async def generate_embeddings_batch(
        self, 
        texts: List[str], 
        normalize: bool = True,
        show_progress: bool = False
    ) -> List[Optional[np.ndarray]]:
        """Generate embeddings for multiple texts in batches"""
        try:
            if not await self.load_model():
                return [None] * len(texts)
            
            if not texts:
                return []
            
            # Preprocess texts
            processed_texts = [self._preprocess_text(text) for text in texts]
            
            # Filter out empty texts but keep track of indices
            valid_texts = []
            valid_indices = []
            for i, text in enumerate(processed_texts):
                if text and text.strip():
                    valid_texts.append(text)
                    valid_indices.append(i)
            
            if not valid_texts:
                return [None] * len(texts)
            
            # Generate embeddings in batches
            all_embeddings = []
            for i in range(0, len(valid_texts), self.batch_size):
                batch_texts = valid_texts[i:i + self.batch_size]
                
                loop = asyncio.get_event_loop()
                batch_embeddings = await loop.run_in_executor(
                    self.executor,
                    self._encode_text,
                    batch_texts,
                    normalize
                )
                
                if batch_embeddings is not None:
                    all_embeddings.extend(batch_embeddings)
                else:
                    all_embeddings.extend([None] * len(batch_texts))
                
                if show_progress:
                    logger.info(f"Processed {min(i + self.batch_size, len(valid_texts))}/{len(valid_texts)} embeddings")
            
            # Map back to original indices
            result = [None] * len(texts)
            for i, embedding in enumerate(all_embeddings):
                if i < len(valid_indices):
                    result[valid_indices[i]] = embedding
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            return [None] * len(texts)
    
    def _encode_text(self, texts: List[str], normalize: bool = True) -> Optional[List[np.ndarray]]:
        """Synchronous text encoding"""
        try:
            embeddings = self.model.encode(
                texts,
                normalize_embeddings=normalize,
                convert_to_numpy=True,
                show_progress_bar=False
            )
            
            # Ensure proper shape (2D array)
            if embeddings.ndim == 1:
                embeddings = embeddings.reshape(1, -1)
            
            return [embeddings[i] for i in range(embeddings.shape[0])]
            
        except Exception as e:
            logger.error(f"Error encoding texts: {e}")
            return None
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text before embedding generation"""
        if not text:
            return ""
        
        # Basic text cleaning
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        text = text.strip()
        
        # Truncate if too long (model will handle this, but good to be explicit)
        max_chars = self.max_seq_length * 4  # Rough estimate: 4 chars per token
        if len(text) > max_chars:
            text = text[:max_chars]
        
        return text
    
    async def chunk_and_embed_document(
        self, 
        document_text: str,
        chunk_strategy: str = "paragraph",
        include_overlap: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Split document into chunks and generate embeddings for each chunk
        
        Args:
            document_text: Full document text
            chunk_strategy: "paragraph", "sentence", "fixed_size", or "semantic"
            include_overlap: Whether to include overlapping content between chunks
        
        Returns:
            List of dictionaries with chunk text, embeddings, and metadata
        """
        try:
            if not document_text or not document_text.strip():
                return []
            
            # Generate chunks based on strategy
            chunks = self._create_chunks(document_text, chunk_strategy, include_overlap)
            
            if not chunks:
                return []
            
            # Generate embeddings for all chunks
            chunk_texts = [chunk['text'] for chunk in chunks]
            embeddings = await self.generate_embeddings_batch(chunk_texts, show_progress=True)
            
            # Combine chunks with embeddings
            result = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                if embedding is not None:
                    result.append({
                        "chunk_index": i,
                        "chunk_id": f"chunk_{i}",
                        "text": chunk['text'],
                        "embedding": embedding,
                        "start_position": chunk['start_position'],
                        "end_position": chunk['end_position'],
                        "chunk_type": chunk_strategy,
                        "confidence_score": self._calculate_confidence_score(chunk['text'])
                    })
            
            logger.info(f"Generated {len(result)} chunk embeddings from {len(chunks)} chunks")
            return result
            
        except Exception as e:
            logger.error(f"Error chunking and embedding document: {e}")
            return []
    
    def _create_chunks(
        self, 
        text: str, 
        strategy: str, 
        include_overlap: bool
    ) -> List[Dict[str, Any]]:
        """Create text chunks based on the specified strategy"""
        
        if strategy == "paragraph":
            return self._chunk_by_paragraph(text)
        elif strategy == "sentence":
            return self._chunk_by_sentence(text)
        elif strategy == "fixed_size":
            return self._chunk_by_fixed_size(text, include_overlap)
        elif strategy == "semantic":
            # For now, fallback to paragraph-based chunking
            # In a full implementation, you'd use more sophisticated semantic segmentation
            return self._chunk_by_paragraph(text)
        else:
            raise ValueError(f"Unknown chunk strategy: {strategy}")
    
    def _chunk_by_paragraph(self, text: str) -> List[Dict[str, Any]]:
        """Split text by paragraphs"""
        chunks = []
        paragraphs = re.split(r'\n\s*\n', text)
        
        current_position = 0
        for i, paragraph in enumerate(paragraphs):
            paragraph = paragraph.strip()
            if len(paragraph) >= self.min_chunk_length:
                start_pos = text.find(paragraph, current_position)
                end_pos = start_pos + len(paragraph)
                
                chunks.append({
                    "text": paragraph,
                    "start_position": start_pos,
                    "end_position": end_pos,
                    "chunk_type": "paragraph"
                })
                
                current_position = end_pos
        
        return chunks
    
    def _chunk_by_sentence(self, text: str) -> List[Dict[str, Any]]:
        """Split text by sentences, combining small sentences"""
        # Simple sentence splitting (in production, use spaCy or nltk)
        sentences = re.split(r'[.!?]+', text)
        
        chunks = []
        current_chunk = ""
        current_start = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # If adding this sentence would make chunk too long, finalize current chunk
            if current_chunk and len(current_chunk + sentence) > self.max_chunk_length:
                if len(current_chunk) >= self.min_chunk_length:
                    end_pos = current_start + len(current_chunk)
                    chunks.append({
                        "text": current_chunk.strip(),
                        "start_position": current_start,
                        "end_position": end_pos,
                        "chunk_type": "sentence_group"
                    })
                
                current_start = text.find(sentence, current_start)
                current_chunk = sentence
            else:
                if not current_chunk:
                    current_start = text.find(sentence, current_start)
                current_chunk += " " + sentence if current_chunk else sentence
        
        # Add final chunk
        if current_chunk and len(current_chunk) >= self.min_chunk_length:
            chunks.append({
                "text": current_chunk.strip(),
                "start_position": current_start,
                "end_position": current_start + len(current_chunk),
                "chunk_type": "sentence_group"
            })
        
        return chunks
    
    def _chunk_by_fixed_size(self, text: str, include_overlap: bool) -> List[Dict[str, Any]]:
        """Split text into fixed-size chunks with optional overlap"""
        chunks = []
        step_size = self.max_chunk_length - (self.overlap_length if include_overlap else 0)
        
        for i in range(0, len(text), step_size):
            end_pos = min(i + self.max_chunk_length, len(text))
            chunk_text = text[i:end_pos]
            
            if len(chunk_text) >= self.min_chunk_length:
                chunks.append({
                    "text": chunk_text,
                    "start_position": i,
                    "end_position": end_pos,
                    "chunk_type": "fixed_size"
                })
        
        return chunks
    
    def _calculate_confidence_score(self, text: str) -> float:
        """Calculate a confidence score for the text embedding quality"""
        if not text:
            return 0.0
        
        # Simple heuristic based on text length and content
        length_score = min(len(text) / 500, 1.0)  # Normalize by 500 chars
        
        # Check for meaningful content (not just numbers or special chars)
        word_count = len(re.findall(r'\b\w+\b', text))
        content_score = min(word_count / 50, 1.0)  # Normalize by 50 words
        
        # Combine scores
        confidence = (length_score * 0.3 + content_score * 0.7)
        return round(confidence, 3)
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current embedding model"""
        await self.load_model()
        
        return {
            "model_name": self.model_name,
            "dimension": self.model_dimension,
            "max_seq_length": self.max_seq_length,
            "device": str(self.model.device) if self.model else "unknown",
            "batch_size": self.batch_size,
            "cache_dir": str(self.cache_dir),
            "torch_available": TORCH_AVAILABLE,
            "cuda_available": TORCH_AVAILABLE and torch.cuda.is_available() if torch else False
        }
    
    async def similarity_search(
        self, 
        query_embedding: np.ndarray, 
        candidate_embeddings: List[np.ndarray],
        top_k: int = 10
    ) -> List[Tuple[int, float]]:
        """
        Perform similarity search between query and candidate embeddings
        Returns list of (index, similarity_score) tuples
        """
        try:
            if not candidate_embeddings:
                return []
            
            # Stack embeddings
            candidates = np.vstack(candidate_embeddings)
            
            # Normalize embeddings
            query_norm = query_embedding / np.linalg.norm(query_embedding)
            candidates_norm = candidates / np.linalg.norm(candidates, axis=1, keepdims=True)
            
            # Calculate cosine similarities
            similarities = np.dot(candidates_norm, query_norm.T).flatten()
            
            # Get top-k results
            top_indices = np.argsort(similarities)[-top_k:][::-1]
            
            results = [(int(idx), float(similarities[idx])) for idx in top_indices]
            return results
            
        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            return []
    
    async def close(self):
        """Close the embedding service and cleanup resources"""
        try:
            self.executor.shutdown(wait=True)
            # Clear model from memory
            self.model = None
            logger.info("Embedding service closed successfully")
        except Exception as e:
            logger.error(f"Error closing embedding service: {e}")

# Global embedding service instance
embedding_service = None

def get_embedding_service(
    model_name: str = "all-MiniLM-L6-v2",
    **kwargs
) -> EmbeddingService:
    """Get or create global embedding service instance"""
    global embedding_service
    
    if embedding_service is None or embedding_service.model_name != model_name:
        embedding_service = EmbeddingService(model_name=model_name, **kwargs)
    
    return embedding_service

# Utility functions for common embedding tasks

async def embed_query(query: str) -> Optional[np.ndarray]:
    """Quick function to embed a search query"""
    service = get_embedding_service()
    return await service.generate_embedding(query)

async def embed_document_content(
    title: str, 
    content: str, 
    summary: str = None
) -> Optional[np.ndarray]:
    """Embed document using title, content, and optionally summary"""
    service = get_embedding_service()
    
    # Combine different parts of the document
    parts = [title] if title else []
    if summary:
        parts.append(summary)
    if content:
        parts.append(content[:2000])  # Limit content length
    
    combined_text = " ".join(parts)
    return await service.generate_embedding(combined_text)

async def get_text_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two texts"""
    service = get_embedding_service()
    
    embeddings = await service.generate_embeddings_batch([text1, text2])
    
    if embeddings[0] is not None and embeddings[1] is not None:
        # Calculate cosine similarity
        similarity = np.dot(embeddings[0], embeddings[1].T) / (
            np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
        )
        return float(similarity)
    
    return 0.0