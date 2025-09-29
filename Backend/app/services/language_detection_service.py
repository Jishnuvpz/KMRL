"""
Language Detection Service
Detects document language (English, Malayalam, or bilingual)
"""

import re
from typing import Dict, List, Tuple
from langdetect import detect, detect_langs
from langdetect.lang_detect_exception import LangDetectException
import logging

logger = logging.getLogger(__name__)

class LanguageDetectionService:
    def __init__(self):
        # Malayalam script Unicode ranges
        self.malayalam_range = (0x0D00, 0x0D7F)  # Malayalam Unicode block
        
        # Common Malayalam words for validation
        self.malayalam_indicators = [
            'ആ', 'ഇ', 'ഉ', 'എ', 'ഒ', 'കാ', 'കി', 'കു', 'കെ', 'കോ',
            'മാ', 'മി', 'മു', 'മെ', 'മോ', 'ന്', 'ണ്', 'ത്', 'ര്', 'ല്',
            'യാ', 'വാ', 'സാ', 'ഹാ', 'ഗാ', 'ദാ', 'ബാ', 'ഫാ', 'ജാ', 'ഖാ'
        ]
        
        # English indicators
        self.english_indicators = [
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'about', 'into', 'through', 'during'
        ]

    def is_malayalam_character(self, char: str) -> bool:
        """Check if character is in Malayalam Unicode range"""
        try:
            char_code = ord(char)
            return self.malayalam_range[0] <= char_code <= self.malayalam_range[1]
        except:
            return False

    def get_malayalam_ratio(self, text: str) -> float:
        """Get ratio of Malayalam characters in text"""
        if not text:
            return 0.0
            
        malayalam_chars = sum(1 for char in text if self.is_malayalam_character(char))
        total_chars = len([c for c in text if c.isalpha()])
        
        return malayalam_chars / total_chars if total_chars > 0 else 0.0

    def detect_with_langdetect(self, text: str) -> Dict[str, float]:
        """Use langdetect library for language detection"""
        try:
            # Get language probabilities
            lang_probs = detect_langs(text)
            
            result = {'english': 0.0, 'malayalam': 0.0, 'other': 0.0}
            
            for lang_prob in lang_probs:
                if lang_prob.lang == 'en':
                    result['english'] = lang_prob.prob
                elif lang_prob.lang == 'ml':
                    result['malayalam'] = lang_prob.prob
                else:
                    result['other'] += lang_prob.prob
                    
            return result
            
        except LangDetectException:
            logger.warning("langdetect failed, using fallback method")
            return {'english': 0.0, 'malayalam': 0.0, 'other': 0.0}

    def detect_with_script_analysis(self, text: str) -> Dict[str, float]:
        """Detect language using script analysis"""
        if not text or len(text.strip()) < 10:
            return {'english': 0.0, 'malayalam': 0.0, 'confidence': 0.0}
        
        # Clean text
        clean_text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = clean_text.split()
        
        malayalam_ratio = self.get_malayalam_ratio(text)
        
        # Count indicator words
        english_word_count = sum(1 for word in words if word in self.english_indicators)
        malayalam_char_presence = malayalam_ratio > 0.1
        
        # Calculate probabilities
        total_words = len(words) if words else 1
        english_prob = min(0.95, english_word_count / total_words * 2)
        malayalam_prob = min(0.95, malayalam_ratio * 1.5)
        
        # Adjust for mixed content
        if malayalam_char_presence and english_prob > 0.3:
            # Likely bilingual
            malayalam_prob = max(malayalam_prob, 0.4)
            english_prob = max(english_prob, 0.4)
        
        return {
            'english': english_prob,
            'malayalam': malayalam_prob,
            'confidence': max(english_prob, malayalam_prob)
        }

    def detect_language(self, text: str) -> Dict[str, any]:
        """
        Main language detection method
        Returns comprehensive language analysis
        """
        if not text or len(text.strip()) < 5:
            return {
                'primary_language': 'unknown',
                'languages': ['unknown'],
                'confidence': 0.0,
                'probabilities': {'english': 0.0, 'malayalam': 0.0},
                'is_bilingual': False,
                'recommended_models': []
            }
        
        # Method 1: Script analysis (more reliable for Malayalam)
        script_result = self.detect_with_script_analysis(text)
        
        # Method 2: langdetect library
        langdetect_result = self.detect_with_langdetect(text)
        
        # Combine results (weighted average, favoring script analysis for Malayalam)
        english_prob = (script_result['english'] * 0.7 + langdetect_result['english'] * 0.3)
        malayalam_prob = (script_result['malayalam'] * 0.8 + langdetect_result['malayalam'] * 0.2)
        
        # Normalize probabilities
        total_prob = english_prob + malayalam_prob
        if total_prob > 1.0:
            english_prob /= total_prob
            malayalam_prob /= total_prob
        
        # Determine primary language and bilingual status
        threshold_bilingual = 0.25  # If both languages > 25%, consider bilingual
        threshold_confident = 0.6   # If one language > 60%, it's primary
        
        is_bilingual = english_prob > threshold_bilingual and malayalam_prob > threshold_bilingual
        
        if malayalam_prob > threshold_confident:
            primary_language = 'malayalam'
            languages = ['malayalam', 'english'] if english_prob > 0.1 else ['malayalam']
        elif english_prob > threshold_confident:
            primary_language = 'english'
            languages = ['english', 'malayalam'] if malayalam_prob > 0.1 else ['english']
        elif is_bilingual:
            primary_language = 'malayalam' if malayalam_prob >= english_prob else 'english'
            languages = ['malayalam', 'english']
        else:
            primary_language = 'english'  # Default fallback
            languages = ['english']
        
        # Recommend appropriate models
        recommended_models = self._get_recommended_models(primary_language, is_bilingual, malayalam_prob)
        
        confidence = max(english_prob, malayalam_prob) if not is_bilingual else min(english_prob + malayalam_prob, 0.95)
        
        return {
            'primary_language': primary_language,
            'languages': languages,
            'confidence': round(confidence, 3),
            'probabilities': {
                'english': round(english_prob, 3),
                'malayalam': round(malayalam_prob, 3)
            },
            'is_bilingual': is_bilingual,
            'recommended_models': recommended_models,
            'text_length': len(text),
            'malayalam_script_ratio': round(self.get_malayalam_ratio(text), 3)
        }

    def _get_recommended_models(self, primary_language: str, is_bilingual: bool, malayalam_prob: float) -> List[str]:
        """Get recommended summarization models based on language detection"""
        models = []
        
        if is_bilingual or malayalam_prob > 0.3:
            # Prefer multilingual models for bilingual/Malayalam content
            models.extend(['ai4bharat/IndicBART', 'google/mt5-small', 'ai4bharat/indic-bert'])
            if primary_language == 'english':
                models.append('facebook/bart-large-cnn')
        else:
            # Primarily English
            if primary_language == 'english':
                models.extend(['facebook/bart-large-cnn', 'google/pegasus-cnn_dailymail'])
            else:
                # Primarily Malayalam
                models.extend(['ai4bharat/IndicBART', 'google/mt5-small'])
        
        return models

# Global service instance
language_detector = LanguageDetectionService()

def detect_document_language(text: str) -> Dict[str, any]:
    """Convenience function for language detection"""
    return language_detector.detect_language(text)

def get_language_detector() -> LanguageDetectionService:
    """Get the language detection service instance"""
    return language_detector
