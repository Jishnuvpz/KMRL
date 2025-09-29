"""
English Text Summarization Service
Uses BART and Pegasus models for English document summarization
"""

import logging
from typing import Dict, Optional, List
import asyncio
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import re

logger = logging.getLogger(__name__)

class EnglishSummarizationService:
    def __init__(self):
        self.models = {}
        self.tokenizers = {}
        self.pipelines = {}
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Model configurations
        self.model_configs = {
            'bart-large-cnn': {
                'name': 'facebook/bart-large-cnn',
                'max_input_length': 1024,
                'max_output_length': 150,
                'min_output_length': 30,
                'description': 'BART model fine-tuned on CNN/Daily Mail dataset'
            },
            'pegasus-cnn': {
                'name': 'google/pegasus-cnn_dailymail', 
                'max_input_length': 1024,
                'max_output_length': 128,
                'min_output_length': 32,
                'description': 'Pegasus model for news summarization'
            },
            'bart-base': {
                'name': 'facebook/bart-base',
                'max_input_length': 1024,
                'max_output_length': 142,
                'min_output_length': 28,
                'description': 'BART base model for general summarization'
            }
        }
        
        self.default_model = 'bart-large-cnn'
        self.initialized_models = set()

    async def initialize_model(self, model_key: str) -> bool:
        """Initialize a specific model"""
        if model_key in self.initialized_models:
            return True
            
        if model_key not in self.model_configs:
            logger.error(f"Unknown model key: {model_key}")
            return False
            
        try:
            config = self.model_configs[model_key]
            model_name = config['name']
            
            logger.info(f"Initializing {model_name} for English summarization...")
            
            # Initialize tokenizer and model
            self.tokenizers[model_key] = AutoTokenizer.from_pretrained(model_name)
            self.models[model_key] = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            
            # Create pipeline
            self.pipelines[model_key] = pipeline(
                'summarization',
                model=self.models[model_key],
                tokenizer=self.tokenizers[model_key],
                device=0 if self.device == "cuda" else -1
            )
            
            self.initialized_models.add(model_key)
            logger.info(f"✅ {model_name} initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize {model_key}: {e}")
            return False

    def preprocess_text(self, text: str) -> str:
        """Preprocess text for better summarization"""
        if not text:
            return ""
        
        # Remove excessive whitespace and newlines
        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        # Remove email headers and signatures
        text = re.sub(r'From:.*?Subject:', 'Subject:', text, flags=re.DOTALL)
        text = re.sub(r'--.*?(?:\n|$)', '', text)
        text = re.sub(r'Best regards.*?$', '', text, flags=re.MULTILINE)
        
        # Clean up punctuation
        text = re.sub(r'([.!?])\s*([.!?])', r'\1', text)  # Remove duplicate punctuation
        
        return text.strip()

    def chunk_text(self, text: str, max_length: int = 1000) -> List[str]:
        """Split text into manageable chunks for processing"""
        sentences = re.split(r'[.!?]+', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            if len(current_chunk + sentence) < max_length:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks

    async def summarize_with_model(
        self, 
        text: str, 
        model_key: str = None,
        max_length: int = None,
        min_length: int = None,
        role_context: str = None
    ) -> Dict[str, any]:
        """Summarize text using specified model"""
        
        model_key = model_key or self.default_model
        
        # Ensure model is initialized
        if not await self.initialize_model(model_key):
            raise Exception(f"Failed to initialize model: {model_key}")
        
        config = self.model_configs[model_key]
        max_length = max_length or config['max_output_length']
        min_length = min_length or config['min_output_length']
        
        # Preprocess text
        processed_text = self.preprocess_text(text)
        
        if len(processed_text) < 50:
            return {
                'summary': processed_text,
                'model_used': model_key,
                'confidence': 0.5,
                'method': 'passthrough',
                'chunks_processed': 0
            }
        
        try:
            # Handle long texts by chunking
            chunks = self.chunk_text(processed_text, config['max_input_length'] - 100)
            
            if len(chunks) == 1:
                # Single chunk processing
                result = self.pipelines[model_key](
                    processed_text,
                    max_length=max_length,
                    min_length=min_length,
                    do_sample=False,
                    truncation=True
                )
                summary = result[0]['summary_text']
                
            else:
                # Multi-chunk processing
                chunk_summaries = []
                for chunk in chunks:
                    result = self.pipelines[model_key](
                        chunk,
                        max_length=max_length // len(chunks) + 20,
                        min_length=max(10, min_length // len(chunks)),
                        do_sample=False,
                        truncation=True
                    )
                    chunk_summaries.append(result[0]['summary_text'])
                
                # Combine chunk summaries
                combined_text = " ".join(chunk_summaries)
                
                # Final summarization of combined chunks
                if len(combined_text) > config['max_input_length']:
                    result = self.pipelines[model_key](
                        combined_text,
                        max_length=max_length,
                        min_length=min_length,
                        do_sample=False,
                        truncation=True
                    )
                    summary = result[0]['summary_text']
                else:
                    summary = combined_text
            
            # Post-process summary for role context
            if role_context:
                summary = self.adapt_summary_for_role(summary, role_context)
            
            return {
                'summary': summary.strip(),
                'model_used': model_key,
                'confidence': 0.85,
                'method': 'multi-chunk' if len(chunks) > 1 else 'single-chunk',
                'chunks_processed': len(chunks),
                'original_length': len(text),
                'summary_length': len(summary)
            }
            
        except Exception as e:
            logger.error(f"Summarization failed with {model_key}: {e}")
            
            # Fallback to simple truncation
            words = processed_text.split()
            fallback_summary = " ".join(words[:50]) + "..." if len(words) > 50 else processed_text
            
            return {
                'summary': fallback_summary,
                'model_used': 'fallback',
                'confidence': 0.3,
                'method': 'truncation',
                'error': str(e)
            }

    def adapt_summary_for_role(self, summary: str, role: str) -> str:
        """Adapt summary based on user role"""
        role_prefixes = {
            'staff': "Action required: ",
            'manager': "Management decision needed: ",
            'director': "Strategic overview: ",
            'admin': "System notice: "
        }
        
        prefix = role_prefixes.get(role.lower(), "")
        return prefix + summary if prefix else summary

    async def get_multiple_summaries(
        self, 
        text: str, 
        models: List[str] = None,
        role_contexts: List[str] = None
    ) -> Dict[str, Dict[str, any]]:
        """Generate summaries using multiple models/contexts"""
        
        models = models or ['bart-large-cnn', 'pegasus-cnn']
        role_contexts = role_contexts or ['staff', 'manager', 'director']
        
        results = {}
        
        # Generate model-based summaries
        for model in models:
            try:
                result = await self.summarize_with_model(text, model)
                results[f'model_{model}'] = result
            except Exception as e:
                logger.error(f"Failed to generate summary with {model}: {e}")
        
        # Generate role-specific summaries
        for role in role_contexts:
            try:
                result = await self.summarize_with_model(
                    text, 
                    self.default_model,
                    role_context=role
                )
                results[f'role_{role}'] = result
            except Exception as e:
                logger.error(f"Failed to generate {role} summary: {e}")
        
        return results

    def get_model_info(self) -> Dict[str, any]:
        """Get information about available models"""
        return {
            'available_models': list(self.model_configs.keys()),
            'initialized_models': list(self.initialized_models),
            'default_model': self.default_model,
            'device': self.device,
            'model_details': self.model_configs
        }

    async def health_check(self) -> Dict[str, any]:
        """Health check for the service"""
        try:
            # Test with default model
            test_text = "This is a test document for health check. It contains some basic information to verify that the summarization service is working properly."
            result = await self.summarize_with_model(test_text)
            
            return {
                'status': 'healthy',
                'default_model': self.default_model,
                'initialized_models': len(self.initialized_models),
                'test_successful': True,
                'test_summary_length': len(result.get('summary', '')),
                'device': self.device
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'initialized_models': len(self.initialized_models),
                'device': self.device
            }

# Global service instance
english_summarizer = EnglishSummarizationService()

async def summarize_english_text(
    text: str, 
    model: str = None,
    role_context: str = None,
    **kwargs
) -> Dict[str, any]:
    """Convenience function for English summarization"""
    return await english_summarizer.summarize_with_model(text, model, role_context=role_context, **kwargs)

def get_english_summarizer() -> EnglishSummarizationService:
    """Get the English summarization service instance"""
    return english_summarizer
