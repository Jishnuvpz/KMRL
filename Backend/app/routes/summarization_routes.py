"""
Summarization API Routes
Provides endpoints for document summarization with automatic language detection
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import logging
from ..services.combined_summarization_service import get_combined_summarizer
from ..services.language_detection_service import get_language_detector
from ..services.english_summarization_service import get_english_summarizer
from ..services.malayalam_summarization_service import get_malayalam_summarizer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/summarization", tags=["📝 Summarization"])

# Request/Response Models
class SummarizationRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=50000, description="Text to summarize")
    max_length: Optional[int] = Field(150, ge=50, le=500, description="Maximum summary length")
    min_length: Optional[int] = Field(30, ge=10, le=200, description="Minimum summary length") 
    role_context: Optional[str] = Field(None, description="User role for context (staff, manager, director, admin)")
    preferred_models: Optional[List[str]] = Field(None, description="Preferred model names")
    include_analysis: bool = Field(True, description="Include language detection analysis")

class LanguageDetectionRequest(BaseModel):
    text: str = Field(..., min_length=5, max_length=50000)

class ModelComparisonRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=50000)
    models: Optional[List[str]] = Field(None, description="Models to compare")

class SummarizationResponse(BaseModel):
    summary: Dict[str, str] = Field(..., description="Summary in available languages (en/ml)")
    primary_language: str = Field(..., description="Detected primary language")
    confidence: float = Field(..., description="Confidence score")
    model_used: str = Field(..., description="Primary model used")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    language_analysis: Optional[Dict[str, Any]] = Field(None, description="Language detection details")

# Dependency to get summarization services
async def get_summarization_services():
    return {
        'combined': get_combined_summarizer(),
        'english': get_english_summarizer(),
        'malayalam': get_malayalam_summarizer(),
        'language_detector': get_language_detector()
    }

@router.post("/auto", response_model=SummarizationResponse)
async def auto_summarize(
    request: SummarizationRequest,
    services: dict = Depends(get_summarization_services)
) -> SummarizationResponse:
    """
    **Automatic Document Summarization**
    
    Automatically detects document language and applies the most appropriate summarization model:
    - **English documents** → BART or Pegasus models
    - **Malayalam documents** → IndicBART or mT5 models  
    - **Bilingual documents** → Multilingual models with dual output
    
    The system intelligently routes content to the best model based on language detection confidence.
    """
    try:
        combined_service = services['combined']
        
        result = await combined_service.auto_summarize(
            text=request.text,
            max_length=request.max_length,
            min_length=request.min_length,
            role_context=request.role_context,
            preferred_models=request.preferred_models,
            include_analysis=request.include_analysis
        )
        
        if 'error' in result:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return SummarizationResponse(
            summary=result['summary'],
            primary_language=result.get('language_analysis', {}).get('primary_language', 'unknown'),
            confidence=result['confidence'],
            model_used=result['model_used'],
            processing_time=result.get('processing_time'),
            language_analysis=result.get('language_analysis') if request.include_analysis else None
        )
        
    except Exception as e:
        logger.error(f"Auto-summarization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")

@router.post("/english")
async def summarize_english(
    request: SummarizationRequest,
    model: Optional[str] = Query(None, description="Specific English model to use"),
    services: dict = Depends(get_summarization_services)
):
    """
    **English Text Summarization**
    
    Summarize English documents using specialized English models:
    - `bart-large-cnn` (default): Fine-tuned for news and formal documents
    - `pegasus-cnn`: Optimized for news summarization
    - `bart-base`: General-purpose summarization
    """
    try:
        english_service = services['english']
        
        result = await english_service.summarize_with_model(
            text=request.text,
            model_key=model,
            max_length=request.max_length,
            min_length=request.min_length,
            role_context=request.role_context
        )
        
        return {
            'summary': {'en': result['summary'], 'ml': ''},
            'model_used': result['model_used'],
            'confidence': result['confidence'],
            'method': result.get('method'),
            'chunks_processed': result.get('chunks_processed', 1)
        }
        
    except Exception as e:
        logger.error(f"English summarization failed: {e}")
        raise HTTPException(status_code=500, detail=f"English summarization failed: {str(e)}")

@router.post("/malayalam")
async def summarize_malayalam(
    request: SummarizationRequest,
    model: Optional[str] = Query(None, description="Specific Malayalam model to use"),
    services: dict = Depends(get_summarization_services)
):
    """
    **Malayalam Text Summarization**
    
    Summarize Malayalam and multilingual documents using specialized models:
    - `indicbart` (default): IndicBART model for Indian languages
    - `mt5-small`: Multilingual T5 model
    - `mt5-base`: Larger multilingual T5 model
    - `mbart-large`: Multilingual BART model
    """
    try:
        malayalam_service = services['malayalam']
        
        result = await malayalam_service.summarize_with_model(
            text=request.text,
            model_key=model,
            max_length=request.max_length,
            min_length=request.min_length,
            language_hint='malayalam',
            role_context=request.role_context
        )
        
        return {
            'summary': {'en': '', 'ml': result['summary']},
            'model_used': result['model_used'],
            'confidence': result['confidence'],
            'method': result.get('method'),
            'chunks_processed': result.get('chunks_processed', 1)
        }
        
    except Exception as e:
        logger.error(f"Malayalam summarization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Malayalam summarization failed: {str(e)}")

@router.post("/detect-language")
async def detect_language(
    request: LanguageDetectionRequest,
    services: dict = Depends(get_summarization_services)
):
    """
    **Language Detection**
    
    Analyzes text to determine:
    - Primary language (English, Malayalam, or mixed)
    - Language probabilities and confidence scores
    - Whether content is bilingual
    - Recommended summarization models
    """
    try:
        language_detector = services['language_detector']
        
        result = language_detector.detect_language(request.text)
        
        return {
            'primary_language': result['primary_language'],
            'languages': result['languages'],
            'confidence': result['confidence'],
            'probabilities': result['probabilities'],
            'is_bilingual': result['is_bilingual'],
            'recommended_models': result['recommended_models'],
            'malayalam_script_ratio': result['malayalam_script_ratio'],
            'text_length': result['text_length']
        }
        
    except Exception as e:
        logger.error(f"Language detection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Language detection failed: {str(e)}")

@router.post("/compare-models")
async def compare_models(
    request: ModelComparisonRequest,
    services: dict = Depends(get_summarization_services)
):
    """
    **Model Comparison**
    
    Generate summaries using multiple models for comparison and quality assessment.
    Useful for:
    - Evaluating different model performance
    - Choosing the best model for specific content types
    - A/B testing summarization quality
    """
    try:
        combined_service = services['combined']
        
        result = await combined_service.get_summary_comparison(
            text=request.text,
            models=request.models
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Model comparison failed: {e}")
        raise HTTPException(status_code=500, detail=f"Model comparison failed: {str(e)}")

@router.get("/models")
async def get_available_models(services: dict = Depends(get_summarization_services)):
    """
    **Available Models**
    
    Get information about all available summarization models, their capabilities,
    and current initialization status.
    """
    try:
        english_service = services['english']
        malayalam_service = services['malayalam']
        
        return {
            'english_models': english_service.get_model_info(),
            'malayalam_models': malayalam_service.get_model_info(),
            'language_support': {
                'english': ['bart-large-cnn', 'pegasus-cnn', 'bart-base'],
                'malayalam': ['indicbart', 'mt5-small', 'mt5-base', 'mbart-large'],
                'multilingual': ['indicbart', 'mt5-small', 'mt5-base', 'mbart-large']
            },
            'recommended_combinations': {
                'english_documents': ['bart-large-cnn', 'pegasus-cnn'],
                'malayalam_documents': ['indicbart', 'mt5-small'],
                'bilingual_documents': ['indicbart', 'mt5-base'],
                'formal_documents': ['bart-large-cnn', 'indicbart'],
                'news_articles': ['pegasus-cnn', 'bart-large-cnn'],
                'general_purpose': ['bart-large-cnn', 'indicbart']
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get model information: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get model information: {str(e)}")

@router.get("/health")
async def summarization_health_check(services: dict = Depends(get_summarization_services)):
    """
    **Summarization Service Health Check**
    
    Comprehensive health check for all summarization services:
    - Language detection functionality
    - Model initialization status  
    - Service availability and performance
    """
    try:
        combined_service = services['combined']
        health_status = await combined_service.health_check()
        
        # Determine HTTP status code
        if health_status['overall_status'] == 'unhealthy':
            raise HTTPException(status_code=503, detail=health_status)
        
        return health_status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=500, 
            detail={
                'overall_status': 'error',
                'error': str(e)
            }
        )

@router.get("/demo")
async def summarization_demo():
    """
    **Summarization Demo**
    
    Quick demonstration of the summarization capabilities with sample text
    in both English and Malayalam.
    """
    demo_texts = {
        'english': """
        The Kochi Metro Rail Limited (KMRL) is implementing a comprehensive document management system
        to streamline operations and improve efficiency. The system includes advanced OCR capabilities
        for processing scanned documents, AI-powered summarization for quick document review, and
        role-based access control to ensure information security. This initiative will significantly
        reduce manual document processing time and improve decision-making across all departments.
        """,
        'malayalam': """
        കൊച്ചി മെട്രോ റെയിൽ ലിമിറ്റഡ് (KMRL) പ്രവർത്തനങ്ങൾ സുഗമമാക്കാനും കാര്യക്ഷമത മെച്ചപ്പെടുത്താനും
        ഒരു സമഗ്ര ഡോക്യുമെന്റ് മാനേജ്മെന്റ് സിസ്റ്റം നടപ്പിലാക്കുന്നു. സ്കാൻ ചെയ്ത ഡോക്യുമെന്റുകൾ പ്രോസസ്സ് ചെയ്യുന്നതിനുള്ള
        വിപുലമായ OCR കഴിവുകൾ, വേഗത്തിലുള്ള ഡോക്യുമെന്റ് അവലോകനത്തിനായി AI-പവർഡ് സംഗ്രഹം, വിവര സുരക്ഷ
        ഉറപ്പാക്കുന്നതിന് റോൾ അധിഷ്ഠിത ആക്സസ് കൺട്രോൾ എന്നിവ സിസ്റ്റത്തിൽ ഉൾപ്പെടുന്നു.
        """
    }
    
    return {
        'service_status': 'operational',
        'demo_texts': demo_texts,
        'features': [
            'Automatic language detection',
            'English text summarization (BART, Pegasus)',
            'Malayalam text summarization (IndicBART, mT5)',
            'Bilingual document processing',
            'Role-based summary adaptation',
            'Multi-model comparison',
            'Confidence scoring'
        ],
        'usage_examples': {
            'auto_summarize': '/api/summarization/auto',
            'english_only': '/api/summarization/english',
            'malayalam_only': '/api/summarization/malayalam',
            'detect_language': '/api/summarization/detect-language',
            'compare_models': '/api/summarization/compare-models'
        }
    }

# Additional utility routes
@router.post("/bulk")
async def bulk_summarize(
    documents: List[Dict[str, str]] = Field(..., description="List of documents with text and optional metadata"),
    services: dict = Depends(get_summarization_services)
):
    """
    **Bulk Summarization**
    
    Process multiple documents in a single request. Useful for batch processing
    of large document sets.
    """
    if len(documents) > 50:  # Limit for performance
        raise HTTPException(status_code=400, detail="Maximum 50 documents per batch request")
    
    try:
        combined_service = services['combined']
        results = []
        
        for i, doc in enumerate(documents):
            if 'text' not in doc:
                results.append({
                    'index': i,
                    'error': 'Missing text field',
                    'summary': {'en': '', 'ml': ''}
                })
                continue
            
            try:
                result = await combined_service.auto_summarize(
                    text=doc['text'],
                    role_context=doc.get('role_context'),
                    include_analysis=False  # Skip analysis for bulk processing
                )
                
                results.append({
                    'index': i,
                    'summary': result['summary'],
                    'primary_language': result.get('language_analysis', {}).get('primary_language', 'unknown'),
                    'model_used': result['model_used'],
                    'confidence': result['confidence']
                })
                
            except Exception as e:
                results.append({
                    'index': i,
                    'error': str(e),
                    'summary': {'en': '', 'ml': ''}
                })
        
        return {
            'total_processed': len(documents),
            'successful': len([r for r in results if 'error' not in r]),
            'failed': len([r for r in results if 'error' in r]),
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Bulk summarization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Bulk summarization failed: {str(e)}")
