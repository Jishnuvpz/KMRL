"""
Combined Summarization Service
Orchestrates language detection and appropriate model selection for document summarization
"""

import logging
from typing import Dict, Optional, List, Any
import asyncio
from .language_detection_service import get_language_detector
from .english_summarization_service import get_english_summarizer
from .malayalam_summarization_service import get_malayalam_summarizer

logger = logging.getLogger(__name__)

class CombinedSummarizationService:
    def __init__(self):
        self.language_detector = get_language_detector()
        self.english_summarizer = get_english_summarizer()
        self.malayalam_summarizer = get_malayalam_summarizer()
        
        # Service configuration
        self.config = {
            'english_threshold': 0.7,      # If English prob > 0.7, use English models only
            'malayalam_threshold': 0.5,    # If Malayalam prob > 0.5, use Malayalam models
            'bilingual_threshold': 0.25,   # If both > 0.25, treat as bilingual
            'confidence_threshold': 0.6,   # Minimum confidence for language detection
            'fallback_language': 'english' # Default fallback
        }

    async def auto_summarize(
        self,
        text: str,
        max_length: int = None,
        min_length: int = None,
        role_context: str = None,
        preferred_models: List[str] = None,
        include_analysis: bool = True
    ) -> Dict[str, Any]:
        """
        Automatically detect language and generate appropriate summary
        
        Args:
            text: Input text to summarize
            max_length: Maximum summary length
            min_length: Minimum summary length
            role_context: User role for context adaptation
            preferred_models: List of preferred model names
            include_analysis: Include language detection analysis in response
            
        Returns:
            Dictionary containing summary and metadata
        """
        
        if not text or len(text.strip()) < 10:
            return {
                'summary': {'en': '', 'ml': ''},
                'primary_language': 'unknown',
                'confidence': 0.0,
                'model_used': 'none',
                'error': 'Text too short for summarization'
            }
        
        try:
            # Step 1: Language Detection
            language_analysis = self.language_detector.detect_language(text)
            
            primary_language = language_analysis['primary_language']
            is_bilingual = language_analysis['is_bilingual']
            confidence = language_analysis['confidence']
            probabilities = language_analysis['probabilities']
            
            logger.info(f"Language detection: {primary_language}, bilingual: {is_bilingual}, confidence: {confidence}")
            
            # Step 2: Model Selection Strategy
            strategy = self._determine_summarization_strategy(
                primary_language, is_bilingual, probabilities, confidence
            )
            
            # Step 3: Generate Summaries
            summaries = await self._generate_summaries(
                text, strategy, max_length, min_length, role_context, preferred_models
            )
            
            # Step 4: Compile Results
            result = {
                'summary': summaries['primary'],
                'summaries': summaries,
                'strategy': strategy,
                'language_analysis': language_analysis if include_analysis else None,
                'model_used': strategy['primary_model'],
                'confidence': confidence,
                'processing_time': summaries.get('processing_time', 0)
            }
            
            # Add role-specific summaries if requested
            if role_context:
                result['role_specific'] = summaries.get('role_specific', {})
            
            return result
            
        except Exception as e:
            logger.error(f"Auto-summarization failed: {e}")
            return await self._fallback_summarization(text, str(e))

    def _determine_summarization_strategy(
        self, 
        primary_language: str, 
        is_bilingual: bool, 
        probabilities: Dict[str, float],
        confidence: float
    ) -> Dict[str, Any]:
        """Determine the best summarization strategy based on language analysis"""
        
        english_prob = probabilities.get('english', 0.0)
        malayalam_prob = probabilities.get('malayalam', 0.0)
        
        strategy = {
            'primary_model': None,
            'secondary_models': [],
            'approach': 'single',  # 'single', 'bilingual', 'multi-model'
            'target_languages': [],
            'confidence_level': 'high' if confidence > 0.7 else 'medium' if confidence > 0.4 else 'low'
        }
        
        # High confidence English
        if english_prob > self.config['english_threshold']:
            strategy.update({
                'primary_model': 'bart-large-cnn',
                'secondary_models': ['pegasus-cnn'],
                'approach': 'single',
                'target_languages': ['english']
            })
        
        # High confidence Malayalam
        elif malayalam_prob > self.config['malayalam_threshold']:
            strategy.update({
                'primary_model': 'indicbart',
                'secondary_models': ['mt5-small'],
                'approach': 'single',
                'target_languages': ['malayalam']
            })
        
        # Bilingual content
        elif is_bilingual:
            strategy.update({
                'primary_model': 'indicbart',  # Better for multilingual
                'secondary_models': ['mt5-base', 'bart-large-cnn'],
                'approach': 'bilingual',
                'target_languages': ['malayalam', 'english']
            })
        
        # Low confidence - use multi-model approach
        else:
            strategy.update({
                'primary_model': 'bart-large-cnn',  # Default fallback
                'secondary_models': ['indicbart', 'mt5-small'],
                'approach': 'multi-model',
                'target_languages': ['english', 'malayalam']
            })
        
        return strategy

    async def _generate_summaries(
        self,
        text: str,
        strategy: Dict[str, Any],
        max_length: int = None,
        min_length: int = None,
        role_context: str = None,
        preferred_models: List[str] = None
    ) -> Dict[str, Any]:
        """Generate summaries based on the determined strategy"""
        
        import time
        start_time = time.time()
        
        summaries = {
            'primary': {'en': '', 'ml': ''},
            'alternatives': {},
            'role_specific': {},
            'processing_time': 0
        }
        
        # Override models if preferred ones are specified
        if preferred_models:
            strategy['secondary_models'] = [m for m in preferred_models if m != strategy['primary_model']][:2]
        
        try:
            # Generate primary summary
            if strategy['approach'] == 'single':
                primary_summary = await self._generate_single_summary(
                    text, strategy, max_length, min_length, role_context
                )
                summaries['primary'] = primary_summary
            
            elif strategy['approach'] == 'bilingual':
                bilingual_summaries = await self._generate_bilingual_summaries(
                    text, strategy, max_length, min_length, role_context
                )
                summaries['primary'] = bilingual_summaries
                
            elif strategy['approach'] == 'multi-model':
                multi_summaries = await self._generate_multi_model_summaries(
                    text, strategy, max_length, min_length, role_context
                )
                summaries['primary'] = multi_summaries['best']
                summaries['alternatives'] = multi_summaries['alternatives']
            
            # Generate role-specific summaries if requested
            if role_context:
                role_summaries = await self._generate_role_specific_summaries(
                    text, strategy, role_context, max_length, min_length
                )
                summaries['role_specific'] = role_summaries
            
            summaries['processing_time'] = time.time() - start_time
            
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            summaries['error'] = str(e)
        
        return summaries

    async def _generate_single_summary(
        self, 
        text: str, 
        strategy: Dict[str, Any], 
        max_length: int = None, 
        min_length: int = None,
        role_context: str = None
    ) -> Dict[str, str]:
        """Generate summary using single best model"""
        
        model = strategy['primary_model']
        target_lang = strategy['target_languages'][0]
        
        if target_lang == 'english':
            result = await self.english_summarizer.summarize_with_model(
                text, model, max_length, min_length, role_context
            )
            return {'en': result['summary'], 'ml': ''}
        
        else:  # Malayalam
            result = await self.malayalam_summarizer.summarize_with_model(
                text, model, max_length, min_length, target_lang, role_context
            )
            return {'en': '', 'ml': result['summary']}

    async def _generate_bilingual_summaries(
        self, 
        text: str, 
        strategy: Dict[str, Any], 
        max_length: int = None, 
        min_length: int = None,
        role_context: str = None
    ) -> Dict[str, str]:
        """Generate summaries in both languages for bilingual content"""
        
        # Use multilingual model for primary summary
        malayalam_result = await self.malayalam_summarizer.summarize_with_model(
            text, strategy['primary_model'], max_length, min_length, 'malayalam', role_context
        )
        
        # Generate English summary as well
        english_result = await self.english_summarizer.summarize_with_model(
            text, 'bart-large-cnn', max_length, min_length, role_context
        )
        
        return {
            'en': english_result['summary'],
            'ml': malayalam_result['summary']
        }

    async def _generate_multi_model_summaries(
        self, 
        text: str, 
        strategy: Dict[str, Any], 
        max_length: int = None, 
        min_length: int = None,
        role_context: str = None
    ) -> Dict[str, Any]:
        """Generate summaries using multiple models and select the best"""
        
        models_to_try = [strategy['primary_model']] + strategy['secondary_models'][:2]
        summaries = {}
        
        # Try English models
        for model in models_to_try:
            try:
                if model in ['bart-large-cnn', 'pegasus-cnn', 'bart-base']:
                    result = await self.english_summarizer.summarize_with_model(
                        text, model, max_length, min_length, role_context
                    )
                    summaries[f'english_{model}'] = {
                        'summary': {'en': result['summary'], 'ml': ''},
                        'confidence': result.get('confidence', 0.5),
                        'model': model
                    }
            except Exception as e:
                logger.warning(f"Model {model} failed: {e}")
        
        # Try Malayalam models  
        for model in models_to_try:
            try:
                if model in ['indicbart', 'mt5-small', 'mt5-base', 'mbart-large']:
                    result = await self.malayalam_summarizer.summarize_with_model(
                        text, model, max_length, min_length, 'malayalam', role_context
                    )
                    summaries[f'malayalam_{model}'] = {
                        'summary': {'en': '', 'ml': result['summary']},
                        'confidence': result.get('confidence', 0.5),
                        'model': model
                    }
            except Exception as e:
                logger.warning(f"Malayalam model {model} failed: {e}")
        
        # Select best summary based on confidence and length
        if summaries:
            best_key = max(summaries.keys(), key=lambda k: summaries[k]['confidence'])
            best_summary = summaries[best_key]['summary']
            alternatives = {k: v['summary'] for k, v in summaries.items() if k != best_key}
        else:
            best_summary = {'en': '', 'ml': ''}
            alternatives = {}
        
        return {'best': best_summary, 'alternatives': alternatives}

    async def _generate_role_specific_summaries(
        self, 
        text: str, 
        strategy: Dict[str, Any], 
        role_context: str,
        max_length: int = None, 
        min_length: int = None
    ) -> Dict[str, Dict[str, str]]:
        """Generate summaries tailored for different roles"""
        
        roles = ['staff', 'manager', 'director']
        if role_context and role_context.lower() not in roles:
            roles.append(role_context.lower())
        
        role_summaries = {}
        primary_lang = strategy['target_languages'][0] if strategy['target_languages'] else 'english'
        
        for role in roles:
            try:
                if primary_lang == 'english':
                    result = await self.english_summarizer.summarize_with_model(
                        text, strategy['primary_model'], max_length, min_length, role
                    )
                    role_summaries[role] = {'en': result['summary'], 'ml': ''}
                else:
                    result = await self.malayalam_summarizer.summarize_with_model(
                        text, strategy['primary_model'], max_length, min_length, primary_lang, role
                    )
                    role_summaries[role] = {'en': '', 'ml': result['summary']}
                    
            except Exception as e:
                logger.warning(f"Role-specific summary failed for {role}: {e}")
        
        return role_summaries

    async def _fallback_summarization(self, text: str, error: str) -> Dict[str, Any]:
        """Fallback summarization using simple truncation"""
        words = text.split()
        simple_summary = " ".join(words[:50]) + "..." if len(words) > 50 else text
        
        return {
            'summary': {'en': simple_summary, 'ml': ''},
            'primary_language': 'unknown',
            'confidence': 0.1,
            'model_used': 'fallback',
            'error': error,
            'method': 'truncation'
        }

    async def get_summary_comparison(
        self, 
        text: str, 
        models: List[str] = None
    ) -> Dict[str, Any]:
        """Compare summaries from different models"""
        
        models = models or ['bart-large-cnn', 'indicbart', 'mt5-small']
        
        # Detect language first
        lang_analysis = self.language_detector.detect_language(text)
        
        comparisons = {}
        
        for model in models:
            try:
                if model in ['bart-large-cnn', 'pegasus-cnn', 'bart-base']:
                    result = await self.english_summarizer.summarize_with_model(text, model)
                    comparisons[model] = {
                        'summary': result['summary'],
                        'confidence': result.get('confidence', 0.5),
                        'language': 'english',
                        'method': result.get('method', 'unknown')
                    }
                elif model in ['indicbart', 'mt5-small', 'mt5-base', 'mbart-large']:
                    result = await self.malayalam_summarizer.summarize_with_model(text, model)
                    comparisons[model] = {
                        'summary': result['summary'],
                        'confidence': result.get('confidence', 0.5),
                        'language': 'malayalam',
                        'method': result.get('method', 'unknown')
                    }
            except Exception as e:
                comparisons[model] = {
                    'summary': '',
                    'error': str(e),
                    'confidence': 0.0
                }
        
        return {
            'language_analysis': lang_analysis,
            'model_comparisons': comparisons,
            'recommended_model': lang_analysis.get('recommended_models', [])[0] if lang_analysis.get('recommended_models') else None
        }

    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check for all summarization services"""
        
        health_status = {
            'overall_status': 'healthy',
            'services': {},
            'language_detection': {},
            'models_available': {
                'english': [],
                'malayalam': []
            }
        }
        
        try:
            # Check language detection
            test_text = "This is a test document. ഇത് ഒരു പരീക്ഷണ പ്രമാണമാണ്."
            lang_result = self.language_detector.detect_language(test_text)
            health_status['language_detection'] = {
                'status': 'healthy',
                'detected_bilingual': lang_result['is_bilingual'],
                'confidence': lang_result['confidence']
            }
            
            # Check English summarizer
            english_health = await self.english_summarizer.health_check()
            health_status['services']['english_summarizer'] = english_health
            health_status['models_available']['english'] = english_health.get('available_models', [])
            
            # Check Malayalam summarizer
            malayalam_health = await self.malayalam_summarizer.health_check()
            health_status['services']['malayalam_summarizer'] = malayalam_health
            health_status['models_available']['malayalam'] = malayalam_health.get('available_models', [])
            
            # Overall status
            if (english_health.get('status') != 'healthy' or 
                malayalam_health.get('status') != 'healthy'):
                health_status['overall_status'] = 'degraded'
            
        except Exception as e:
            health_status['overall_status'] = 'unhealthy'
            health_status['error'] = str(e)
        
        return health_status

# Global service instance
combined_summarizer = CombinedSummarizationService()

async def auto_summarize_document(
    text: str,
    role_context: str = None,
    **kwargs
) -> Dict[str, Any]:
    """Convenience function for automatic document summarization"""
    return await combined_summarizer.auto_summarize(text, role_context=role_context, **kwargs)

def get_combined_summarizer() -> CombinedSummarizationService:
    """Get the combined summarization service instance"""
    return combined_summarizer
