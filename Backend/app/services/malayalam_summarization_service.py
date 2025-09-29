"""
Malayalam Text Summarization Service
Uses IndicBART and mT5 models for Malayalam and bilingual document summarization
"""

import logging
from typing import Dict, Optional, List
import asyncio
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM, MBart50TokenizerFast, MBartForConditionalGeneration
import torch
import re

logger = logging.getLogger(__name__)

class MalayalamSummarizationService:
    def __init__(self):
        self.models = {}
        self.tokenizers = {}
        self.pipelines = {}
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Model configurations for Malayalam/Multilingual models
        self.model_configs = {
            'indicbart': {
                'name': 'ai4bharat/IndicBARTSS',
                'max_input_length': 1024,
                'max_output_length': 150,
                'min_output_length': 30,
                'description': 'IndicBART model for Indian language summarization',
                'languages': ['malayalam', 'hindi', 'english']
            },
            'mt5-small': {
                'name': 'google/mt5-small',
                'max_input_length': 512,
                'max_output_length': 128,
                'min_output_length': 25,
                'description': 'Multilingual T5 model',
                'languages': ['malayalam', 'english', 'multilingual']
            },
            'mt5-base': {
                'name': 'google/mt5-base',
                'max_input_length': 512,
                'max_output_length': 150,
                'min_output_length': 30,
                'description': 'Multilingual T5 base model',
                'languages': ['malayalam', 'english', 'multilingual']
            },
            'mbart-large': {
                'name': 'facebook/mbart-large-50-many-to-many-mmt',
                'max_input_length': 1024,
                'max_output_length': 150,
                'min_output_length': 30,
                'description': 'mBART model for multilingual summarization',
                'languages': ['malayalam', 'english', 'multilingual']
            }
        }
        
        self.default_model = 'indicbart'
        self.initialized_models = set()
        
        # Malayalam language processing patterns
        self.malayalam_patterns = {
            'sentence_endings': r'[.!?।]',
            'word_boundaries': r'[\s\u0D4D]+',  # Malayalam virama and spaces
            'numbers': r'[\u0D66-\u0D6F]',      # Malayalam numerals
            'punctuation': r'[\u0D4D\u0D3E-\u0D4C]'  # Malayalam vowel signs
        }

    async def initialize_model(self, model_key: str) -> bool:
        """Initialize a specific model for Malayalam/multilingual summarization"""
        if model_key in self.initialized_models:
            return True
            
        if model_key not in self.model_configs:
            logger.error(f"Unknown model key: {model_key}")
            return False
            
        try:
            config = self.model_configs[model_key]
            model_name = config['name']
            
            logger.info(f"Initializing {model_name} for Malayalam summarization...")
            
            if model_key == 'mbart-large':
                # Special handling for mBART
                self.tokenizers[model_key] = MBart50TokenizerFast.from_pretrained(model_name)
                self.models[model_key] = MBartForConditionalGeneration.from_pretrained(model_name)
            else:
                # Standard handling for other models
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

    def preprocess_malayalam_text(self, text: str) -> str:
        """Preprocess Malayalam text for better summarization"""
        if not text:
            return ""
        
        # Remove excessive whitespace and newlines
        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        # Handle Malayalam-English mixed content
        # Preserve Malayalam script while cleaning English parts
        text = re.sub(r'([a-zA-Z]+)(\u0D00-\u0D7F)', r'\1 \2', text)  # Add space between English and Malayalam
        
        # Remove email headers in English
        text = re.sub(r'From:.*?Subject:', 'വിഷയം:', text, flags=re.DOTALL)
        text = re.sub(r'--.*?(?:\n|$)', '', text)
        
        # Clean up punctuation
        text = re.sub(r'([.!?।])\s*([.!?।])', r'\1', text)
        
        return text.strip()

    def chunk_malayalam_text(self, text: str, max_length: int = 800) -> List[str]:
        """Split Malayalam text into manageable chunks"""
        # Split by Malayalam sentence endings
        sentences = re.split(self.malayalam_patterns['sentence_endings'], text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            if len(current_chunk + sentence) < max_length:
                current_chunk += sentence + "। "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + "। "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks

    async def summarize_with_model(
        self, 
        text: str, 
        model_key: str = None,
        max_length: int = None,
        min_length: int = None,
        language_hint: str = 'malayalam',
        role_context: str = None
    ) -> Dict[str, any]:
        """Summarize Malayalam/multilingual text using specified model"""
        
        model_key = model_key or self.default_model
        
        # Ensure model is initialized
        if not await self.initialize_model(model_key):
            raise Exception(f"Failed to initialize model: {model_key}")
        
        config = self.model_configs[model_key]
        max_length = max_length or config['max_output_length']
        min_length = min_length or config['min_output_length']
        
        # Preprocess text
        processed_text = self.preprocess_malayalam_text(text)
        
        if len(processed_text) < 30:
            return {
                'summary': processed_text,
                'model_used': model_key,
                'confidence': 0.5,
                'method': 'passthrough',
                'language': language_hint
            }
        
        try:
            # Handle long texts by chunking
            chunks = self.chunk_malayalam_text(processed_text, config['max_input_length'] - 100)
            
            if len(chunks) == 1:
                # Single chunk processing
                if model_key == 'mbart-large':
                    # Special handling for mBART with language codes
                    summary = await self._summarize_with_mbart(processed_text, max_length, min_length, language_hint)
                else:
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
                    if model_key == 'mbart-large':
                        chunk_summary = await self._summarize_with_mbart(
                            chunk, 
                            max_length // len(chunks) + 20, 
                            max(10, min_length // len(chunks)),
                            language_hint
                        )
                    else:
                        result = self.pipelines[model_key](
                            chunk,
                            max_length=max_length // len(chunks) + 20,
                            min_length=max(10, min_length // len(chunks)),
                            do_sample=False,
                            truncation=True
                        )
                        chunk_summary = result[0]['summary_text']
                    
                    chunk_summaries.append(chunk_summary)
                
                # Combine chunk summaries
                combined_text = " ".join(chunk_summaries)
                
                # Final summarization if needed
                if len(combined_text) > config['max_input_length']:
                    if model_key == 'mbart-large':
                        summary = await self._summarize_with_mbart(combined_text, max_length, min_length, language_hint)
                    else:
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
                summary = self.adapt_malayalam_summary_for_role(summary, role_context)
            
            return {
                'summary': summary.strip(),
                'model_used': model_key,
                'confidence': 0.80,  # Slightly lower confidence for multilingual
                'method': 'multi-chunk' if len(chunks) > 1 else 'single-chunk',
                'chunks_processed': len(chunks),
                'language': language_hint,
                'original_length': len(text),
                'summary_length': len(summary)
            }
            
        except Exception as e:
            logger.error(f"Malayalam summarization failed with {model_key}: {e}")
            
            # Fallback to simple truncation with Malayalam awareness
            words = processed_text.split()
            fallback_summary = " ".join(words[:30]) + "..." if len(words) > 30 else processed_text
            
            return {
                'summary': fallback_summary,
                'model_used': 'fallback',
                'confidence': 0.3,
                'method': 'truncation',
                'language': language_hint,
                'error': str(e)
            }

    async def _summarize_with_mbart(
        self, 
        text: str, 
        max_length: int, 
        min_length: int, 
        language_hint: str
    ) -> str:
        """Special handling for mBART model with language codes"""
        tokenizer = self.tokenizers['mbart-large']
        model = self.models['mbart-large']
        
        # Set language codes for mBART
        if language_hint == 'malayalam':
            src_lang = 'ml_IN'
            tgt_lang = 'ml_IN'
        else:
            src_lang = 'en_XX'
            tgt_lang = 'en_XX'
        
        # Tokenize with language code
        tokenizer.src_lang = src_lang
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=1024)
        
        # Generate summary
        summary_ids = model.generate(
            inputs["input_ids"],
            max_length=max_length,
            min_length=min_length,
            forced_bos_token_id=tokenizer.lang_code_to_id[tgt_lang],
            no_repeat_ngram_size=2,
            num_beams=4,
            early_stopping=True
        )
        
        summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        return summary

    def adapt_malayalam_summary_for_role(self, summary: str, role: str) -> str:
        """Adapt Malayalam summary based on user role"""
        role_prefixes = {
            'staff': "നടപടി ആവശ്യം: ",
            'manager': "മാനേജ്മെന്റ് തീരുമാനം ആവശ്യം: ",
            'director': "തന്ത്രപരമായ അവലോകനം: ",
            'admin': "സിസ്റ്റം അറിയിപ്പ്: "
        }
        
        prefix = role_prefixes.get(role.lower(), "")
        return prefix + summary if prefix else summary

    async def get_multiple_summaries(
        self, 
        text: str, 
        models: List[str] = None,
        language_hint: str = 'malayalam',
        role_contexts: List[str] = None
    ) -> Dict[str, Dict[str, any]]:
        """Generate summaries using multiple models/contexts for Malayalam"""
        
        models = models or ['indicbart', 'mt5-small']
        role_contexts = role_contexts or ['staff', 'manager', 'director']
        
        results = {}
        
        # Generate model-based summaries
        for model in models:
            try:
                result = await self.summarize_with_model(text, model, language_hint=language_hint)
                results[f'model_{model}'] = result
            except Exception as e:
                logger.error(f"Failed to generate Malayalam summary with {model}: {e}")
        
        # Generate role-specific summaries
        for role in role_contexts:
            try:
                result = await self.summarize_with_model(
                    text, 
                    self.default_model,
                    language_hint=language_hint,
                    role_context=role
                )
                results[f'role_{role}'] = result
            except Exception as e:
                logger.error(f"Failed to generate {role} summary in Malayalam: {e}")
        
        return results

    def detect_malayalam_content_ratio(self, text: str) -> float:
        """Detect ratio of Malayalam content in text"""
        malayalam_chars = sum(1 for char in text if '\u0D00' <= char <= '\u0D7F')
        total_chars = len([c for c in text if c.isalpha()])
        return malayalam_chars / total_chars if total_chars > 0 else 0.0

    def get_model_info(self) -> Dict[str, any]:
        """Get information about available Malayalam models"""
        return {
            'available_models': list(self.model_configs.keys()),
            'initialized_models': list(self.initialized_models),
            'default_model': self.default_model,
            'device': self.device,
            'supported_languages': ['malayalam', 'english', 'multilingual'],
            'model_details': self.model_configs
        }

    async def health_check(self) -> Dict[str, any]:
        """Health check for Malayalam summarization service"""
        try:
            # Test with Malayalam text
            test_text = "ഇത് ഒരു പരീക്ഷണ പ്രമാണമാണ്. മലയാളം സംഗ്രഹ സേവനം ശരിയായി പ്രവർത്തിക്കുന്നുണ്ടെന്ന് പരിശോധിക്കാൻ ഇത് ഉപയോഗിക്കുന്നു. സിസ്റ്റം എല്ലാ ഭാഷകളിലും പ്രവർത്തിക്കണം."
            result = await self.summarize_with_model(test_text)
            
            return {
                'status': 'healthy',
                'default_model': self.default_model,
                'initialized_models': len(self.initialized_models),
                'test_successful': True,
                'test_summary_length': len(result.get('summary', '')),
                'malayalam_support': True,
                'device': self.device
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'initialized_models': len(self.initialized_models),
                'malayalam_support': False,
                'device': self.device
            }

# Global service instance
malayalam_summarizer = MalayalamSummarizationService()

async def summarize_malayalam_text(
    text: str, 
    model: str = None,
    language_hint: str = 'malayalam',
    role_context: str = None,
    **kwargs
) -> Dict[str, any]:
    """Convenience function for Malayalam summarization"""
    return await malayalam_summarizer.summarize_with_model(
        text, 
        model, 
        language_hint=language_hint,
        role_context=role_context, 
        **kwargs
    )

def get_malayalam_summarizer() -> MalayalamSummarizationService:
    """Get the Malayalam summarization service instance"""
    return malayalam_summarizer
