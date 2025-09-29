"""
Configuration settings for FAISS Semantic Search System
Centralized configuration for all semantic search components
"""
import os
from typing import Dict, Any, List

class SemanticSearchConfig:
    """Configuration class for semantic search system"""
    
    # Embedding Model Configuration
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "384"))
    MAX_SEQUENCE_LENGTH = int(os.getenv("MAX_SEQUENCE_LENGTH", "512"))
    BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))
    
    # FAISS Index Configuration  
    FAISS_INDEX_TYPE = os.getenv("FAISS_INDEX_TYPE", "Flat")  # Flat, IVF, HNSW
    FAISS_NLIST = int(os.getenv("FAISS_NLIST", "100"))  # For IVF index
    FAISS_NPROBE = int(os.getenv("FAISS_NPROBE", "10"))  # For IVF search
    FAISS_M = int(os.getenv("FAISS_M", "16"))  # For HNSW index
    FAISS_EF_CONSTRUCTION = int(os.getenv("FAISS_EF_CONSTRUCTION", "200"))  # For HNSW
    FAISS_EF_SEARCH = int(os.getenv("FAISS_EF_SEARCH", "100"))  # For HNSW search
    
    # Text Processing Configuration
    MIN_CHUNK_LENGTH = int(os.getenv("MIN_CHUNK_LENGTH", "50"))
    MAX_CHUNK_LENGTH = int(os.getenv("MAX_CHUNK_LENGTH", "1000"))
    CHUNK_OVERLAP_LENGTH = int(os.getenv("CHUNK_OVERLAP_LENGTH", "50"))
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", "50000"))
    
    # Search Configuration
    DEFAULT_TOP_K = int(os.getenv("DEFAULT_TOP_K", "10"))
    DEFAULT_SIMILARITY_THRESHOLD = float(os.getenv("DEFAULT_SIMILARITY_THRESHOLD", "0.0"))
    MAX_SEARCH_RESULTS = int(os.getenv("MAX_SEARCH_RESULTS", "100"))
    
    # File Processing Configuration
    SUPPORTED_FILE_TYPES = [
        "text/plain", 
        "application/pdf", 
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/markdown", 
        "text/html", 
        "application/rtf"
    ]
    
    AUTO_EMBED_ON_UPLOAD = os.getenv("AUTO_EMBED_ON_UPLOAD", "true").lower() == "true"
    BACKGROUND_PROCESSING = os.getenv("BACKGROUND_PROCESSING", "true").lower() == "true"
    MAX_CONCURRENT_PROCESSING = int(os.getenv("MAX_CONCURRENT_PROCESSING", "3"))
    
    # Storage Configuration
    FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "data/faiss_indices")
    MODEL_CACHE_PATH = os.getenv("MODEL_CACHE_PATH", "models/sentence_transformers")
    
    # Performance Configuration
    USE_GPU = os.getenv("USE_GPU", "auto")  # auto, true, false
    MAX_MEMORY_GB = int(os.getenv("MAX_MEMORY_GB", "4"))
    ENABLE_QUANTIZATION = os.getenv("ENABLE_QUANTIZATION", "false").lower() == "true"
    
    # Monitoring and Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    ENABLE_METRICS = os.getenv("ENABLE_METRICS", "true").lower() == "true"
    METRICS_COLLECTION_INTERVAL = int(os.getenv("METRICS_COLLECTION_INTERVAL", "300"))  # seconds
    
    # API Configuration
    SEMANTIC_SEARCH_PREFIX = "/api/semantic-search"
    MAX_QUERY_LENGTH = int(os.getenv("MAX_QUERY_LENGTH", "1000"))
    RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))  # per minute
    
    @classmethod
    def get_chunk_strategy_config(cls) -> Dict[str, str]:
        """Get chunking strategy configuration by file type"""
        return {
            'text/plain': 'paragraph',
            'application/pdf': 'paragraph', 
            'application/msword': 'paragraph',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'paragraph',
            'text/markdown': 'paragraph',
            'text/html': 'sentence',
            'application/rtf': 'paragraph'
        }
    
    @classmethod
    def get_faiss_index_config(cls) -> Dict[str, Any]:
        """Get FAISS index configuration"""
        config = {
            "index_type": cls.FAISS_INDEX_TYPE,
            "dimension": cls.EMBEDDING_DIMENSION
        }
        
        if cls.FAISS_INDEX_TYPE == "IVF":
            config.update({
                "nlist": cls.FAISS_NLIST,
                "nprobe": cls.FAISS_NPROBE
            })
        elif cls.FAISS_INDEX_TYPE == "HNSW":
            config.update({
                "M": cls.FAISS_M,
                "ef_construction": cls.FAISS_EF_CONSTRUCTION,
                "ef_search": cls.FAISS_EF_SEARCH
            })
        
        return config
    
    @classmethod
    def get_embedding_config(cls) -> Dict[str, Any]:
        """Get embedding model configuration"""
        return {
            "model_name": cls.EMBEDDING_MODEL,
            "cache_dir": cls.MODEL_CACHE_PATH,
            "max_seq_length": cls.MAX_SEQUENCE_LENGTH,
            "batch_size": cls.BATCH_SIZE,
            "device": cls.USE_GPU
        }
    
    @classmethod
    def get_processing_config(cls) -> Dict[str, Any]:
        """Get document processing configuration"""
        return {
            "min_chunk_length": cls.MIN_CHUNK_LENGTH,
            "max_chunk_length": cls.MAX_CHUNK_LENGTH,
            "overlap_length": cls.CHUNK_OVERLAP_LENGTH,
            "max_content_length": cls.MAX_CONTENT_LENGTH,
            "supported_types": cls.SUPPORTED_FILE_TYPES,
            "auto_embed": cls.AUTO_EMBED_ON_UPLOAD,
            "background_processing": cls.BACKGROUND_PROCESSING,
            "max_concurrent": cls.MAX_CONCURRENT_PROCESSING
        }
    
    @classmethod
    def validate_config(cls) -> List[str]:
        """Validate configuration and return any warnings/errors"""
        warnings = []
        
        # Check critical paths
        if not os.path.exists(cls.FAISS_INDEX_PATH):
            warnings.append(f"FAISS index path does not exist: {cls.FAISS_INDEX_PATH}")
        
        if not os.path.exists(cls.MODEL_CACHE_PATH):
            warnings.append(f"Model cache path does not exist: {cls.MODEL_CACHE_PATH}")
        
        # Check parameter ranges
        if cls.EMBEDDING_DIMENSION <= 0:
            warnings.append("Invalid embedding dimension")
        
        if cls.DEFAULT_SIMILARITY_THRESHOLD < 0 or cls.DEFAULT_SIMILARITY_THRESHOLD > 1:
            warnings.append("Similarity threshold should be between 0 and 1")
        
        if cls.MAX_CHUNK_LENGTH <= cls.MIN_CHUNK_LENGTH:
            warnings.append("Max chunk length should be greater than min chunk length")
        
        # Check FAISS configuration
        if cls.FAISS_INDEX_TYPE not in ["Flat", "IVF", "HNSW"]:
            warnings.append(f"Unsupported FAISS index type: {cls.FAISS_INDEX_TYPE}")
        
        return warnings

# Global configuration instance
config = SemanticSearchConfig()

# Configuration validation
config_warnings = config.validate_config()
if config_warnings:
    import logging
    logger = logging.getLogger(__name__)
    for warning in config_warnings:
        logger.warning(f"Configuration warning: {warning}")

# Export commonly used configurations
EMBEDDING_CONFIG = config.get_embedding_config()
FAISS_CONFIG = config.get_faiss_index_config()
PROCESSING_CONFIG = config.get_processing_config()