"""
Google Cloud Vision API Service
Advanced OCR and image analysis using Google's Vision API
"""
import os
import io
import json
from typing import List, Dict, Optional, Tuple, Union
from datetime import datetime
import base64


try:
    from google.cloud import vision
    from google.oauth2 import service_account
    import google.auth
    GOOGLE_VISION_AVAILABLE = True
except ImportError:
    GOOGLE_VISION_AVAILABLE = False
    print("Google Cloud Vision API not available. Install with: pip install google-cloud-vision")

from app.config import settings

class GoogleVisionService:
    """
    Google Cloud Vision API service for advanced OCR and document analysis
    """
    
    def __init__(self):
        if not GOOGLE_VISION_AVAILABLE:
            print("Google Cloud Vision API not available - falling back to Tesseract only")
            self.client = None
            self.api_enabled = False
            return
        
        self.project_id = settings.GOOGLE_CLOUD_PROJECT_ID if hasattr(settings, 'GOOGLE_CLOUD_PROJECT_ID') else None
        self.credentials_path = settings.GOOGLE_APPLICATION_CREDENTIALS if hasattr(settings, 'GOOGLE_APPLICATION_CREDENTIALS') else None
        self.api_enabled = getattr(settings, 'GOOGLE_VISION_API_ENABLED', False)
        self.max_results = getattr(settings, 'GOOGLE_VISION_MAX_RESULTS', 50)
        self.language_hints = getattr(settings, 'GOOGLE_VISION_LANGUAGE_HINTS', 'en').split(',')
        
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Google Vision API client"""
        try:
            if not self.api_enabled:
                print("Google Vision API is disabled in configuration")
                return
            
            # Try to initialize with service account credentials
            if self.credentials_path and os.path.exists(self.credentials_path):
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path
                )
                self.client = vision.ImageAnnotatorClient(credentials=credentials)
                print(f"✅ Google Vision API initialized with service account")
            else:
                # Try default credentials (for GCP environments)
                try:
                    self.client = vision.ImageAnnotatorClient()
                    print(f"✅ Google Vision API initialized with default credentials")
                except Exception as e:
                    print(f"⚠️ Could not initialize Google Vision API: {str(e)}")
                    print("Please set up service account credentials or run in GCP environment")
                    self.client = None
                    
        except Exception as e:
            print(f"❌ Failed to initialize Google Vision API: {str(e)}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if Google Vision API is available and configured"""
        return self.client is not None and self.api_enabled
    
    def detect_text(self, image_content: bytes, language_hints: Optional[List[str]] = None) -> Dict:
        """
        Detect and extract text from image using Google Vision API
        
        Args:
            image_content: Image data as bytes
            language_hints: List of language codes to hint the API
        
        Returns:
            Dictionary containing extracted text and metadata
        """
        if not self.is_available():
            return {
                'success': False,
                'error': 'Google Vision API not available',
                'text': '',
                'confidence': 0.0
            }
        
        try:
            # Create image object
            image = vision.Image(content=image_content)
            
            # Set up image context with language hints
            if language_hints is None:
                language_hints = self.language_hints
            
            image_context = vision.ImageContext(language_hints=language_hints)
            
            # Perform text detection
            response = self.client.text_detection(
                image=image, 
                image_context=image_context,
                max_results=self.max_results
            )
            
            # Check for errors
            if response.error.message:
                return {
                    'success': False,
                    'error': response.error.message,
                    'text': '',
                    'confidence': 0.0
                }
            
            # Extract text annotations
            texts = response.text_annotations
            
            if not texts:
                return {
                    'success': True,
                    'text': '',
                    'confidence': 0.0,
                    'word_count': 0,
                    'language': 'unknown'
                }
            
            # The first annotation contains the entire detected text
            full_text = texts[0].description
            
            # Calculate average confidence from individual words/characters
            total_confidence = 0
            word_count = 0
            detected_languages = set()
            
            # Get detailed word-level information
            words_info = []
            for text_annotation in texts[1:]:  # Skip the first full text annotation
                if text_annotation.description.strip():
                    words_info.append({
                        'text': text_annotation.description,
                        'bounding_box': self._extract_bounding_box(text_annotation.bounding_poly),
                        'confidence': getattr(text_annotation, 'confidence', 0.0)
                    })
                    
                    if hasattr(text_annotation, 'locale') and text_annotation.locale:
                        detected_languages.add(text_annotation.locale)
                    
                    word_count += 1
                    total_confidence += getattr(text_annotation, 'confidence', 0.0)
            
            avg_confidence = total_confidence / word_count if word_count > 0 else 0.0
            primary_language = list(detected_languages)[0] if detected_languages else 'unknown'
            
            return {
                'success': True,
                'text': full_text,
                'confidence': avg_confidence,
                'word_count': word_count,
                'language': primary_language,
                'detected_languages': list(detected_languages),
                'words_info': words_info,
                'processing_time': datetime.now().isoformat(),
                'api_used': 'google_vision'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'text': '',
                'confidence': 0.0
            }
    
    def detect_document_text(self, image_content: bytes) -> Dict:
        """
        Detect text in documents with enhanced structure analysis
        
        Args:
            image_content: Image data as bytes
        
        Returns:
            Dictionary with structured document text analysis
        """
        if not self.is_available():
            return {
                'success': False,
                'error': 'Google Vision API not available'
            }
        
        try:
            image = vision.Image(content=image_content)
            
            # Use document_text_detection for better structure understanding
            response = self.client.document_text_detection(image=image)
            
            if response.error.message:
                return {
                    'success': False,
                    'error': response.error.message
                }
            
            # Extract full text annotation with structure
            full_text_annotation = response.full_text_annotation
            
            if not full_text_annotation:
                return {
                    'success': True,
                    'text': '',
                    'pages': [],
                    'blocks': [],
                    'paragraphs': [],
                    'words': []
                }
            
            # Process document structure
            pages_info = []
            blocks_info = []
            paragraphs_info = []
            words_info = []
            
            for page in full_text_annotation.pages:
                page_info = {
                    'width': page.width,
                    'height': page.height,
                    'confidence': page.confidence
                }
                pages_info.append(page_info)
                
                for block in page.blocks:
                    block_text = ''
                    block_paragraphs = []
                    
                    for paragraph in block.paragraphs:
                        paragraph_text = ''
                        paragraph_words = []
                        
                        for word in paragraph.words:
                            word_text = ''.join([symbol.text for symbol in word.symbols])
                            paragraph_text += word_text + ' '
                            
                            word_info = {
                                'text': word_text,
                                'confidence': word.confidence,
                                'bounding_box': self._extract_bounding_box(word.bounding_box)
                            }
                            words_info.append(word_info)
                            paragraph_words.append(word_info)
                        
                        paragraph_info = {
                            'text': paragraph_text.strip(),
                            'confidence': paragraph.confidence,
                            'bounding_box': self._extract_bounding_box(paragraph.bounding_box),
                            'words': paragraph_words
                        }
                        paragraphs_info.append(paragraph_info)
                        block_paragraphs.append(paragraph_info)
                        block_text += paragraph_text
                    
                    block_info = {
                        'text': block_text.strip(),
                        'confidence': block.confidence,
                        'block_type': block.block_type.name,
                        'bounding_box': self._extract_bounding_box(block.bounding_box),
                        'paragraphs': block_paragraphs
                    }
                    blocks_info.append(block_info)
            
            return {
                'success': True,
                'text': full_text_annotation.text,
                'confidence': sum([page.confidence for page in full_text_annotation.pages]) / len(full_text_annotation.pages),
                'pages': pages_info,
                'blocks': blocks_info,
                'paragraphs': paragraphs_info,
                'words': words_info,
                'processing_time': datetime.now().isoformat(),
                'api_used': 'google_vision_document'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def analyze_document_properties(self, image_content: bytes) -> Dict:
        """
        Analyze document properties like dominant colors, image quality, etc.
        
        Args:
            image_content: Image data as bytes
        
        Returns:
            Dictionary with image analysis results
        """
        if not self.is_available():
            return {
                'success': False,
                'error': 'Google Vision API not available'
            }
        
        try:
            image = vision.Image(content=image_content)
            
            # Request multiple types of analysis
            features = [
                vision.Feature(type_=vision.Feature.Type.IMAGE_PROPERTIES),
                vision.Feature(type_=vision.Feature.Type.SAFE_SEARCH_DETECTION),
                vision.Feature(type_=vision.Feature.Type.CROP_HINTS)
            ]
            
            request = vision.AnnotateImageRequest(image=image, features=features)
            response = self.client.annotate_image(request=request)
            
            if response.error.message:
                return {
                    'success': False,
                    'error': response.error.message
                }
            
            # Extract image properties
            properties = {}
            
            if response.image_properties_annotation:
                dominant_colors = []
                for color in response.image_properties_annotation.dominant_colors.colors:
                    dominant_colors.append({
                        'red': color.color.red,
                        'green': color.color.green,
                        'blue': color.color.blue,
                        'alpha': getattr(color.color, 'alpha', 1.0),
                        'score': color.score,
                        'pixel_fraction': color.pixel_fraction
                    })
                
                properties['dominant_colors'] = dominant_colors
            
            # Safe search detection
            if response.safe_search_annotation:
                properties['safe_search'] = {
                    'adult': response.safe_search_annotation.adult.name,
                    'spoof': response.safe_search_annotation.spoof.name,
                    'medical': response.safe_search_annotation.medical.name,
                    'violence': response.safe_search_annotation.violence.name,
                    'racy': response.safe_search_annotation.racy.name
                }
            
            # Crop hints
            if response.crop_hints_annotation:
                crop_hints = []
                for hint in response.crop_hints_annotation.crop_hints:
                    crop_hints.append({
                        'bounding_box': self._extract_bounding_box(hint.bounding_poly),
                        'confidence': hint.confidence,
                        'importance_fraction': hint.importance_fraction
                    })
                properties['crop_hints'] = crop_hints
            
            return {
                'success': True,
                'properties': properties,
                'processing_time': datetime.now().isoformat(),
                'api_used': 'google_vision_properties'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def detect_objects(self, image_content: bytes) -> Dict:
        """
        Detect objects in the image (useful for document classification)
        
        Args:
            image_content: Image data as bytes
        
        Returns:
            Dictionary with detected objects
        """
        if not self.is_available():
            return {
                'success': False,
                'error': 'Google Vision API not available'
            }
        
        try:
            image = vision.Image(content=image_content)
            
            # Object detection
            response = self.client.object_localization(image=image)
            
            if response.error.message:
                return {
                    'success': False,
                    'error': response.error.message
                }
            
            objects = []
            for obj in response.localized_object_annotations:
                objects.append({
                    'name': obj.name,
                    'confidence': obj.score,
                    'bounding_box': self._extract_bounding_box(obj.bounding_poly),
                    'mid': obj.mid  # Machine-generated identifier
                })
            
            return {
                'success': True,
                'objects': objects,
                'object_count': len(objects),
                'processing_time': datetime.now().isoformat(),
                'api_used': 'google_vision_objects'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def comprehensive_analysis(self, image_content: bytes, include_objects: bool = False) -> Dict:
        """
        Perform comprehensive document analysis combining multiple Vision API features
        
        Args:
            image_content: Image data as bytes
            include_objects: Whether to include object detection
        
        Returns:
            Dictionary with comprehensive analysis results
        """
        results = {
            'timestamp': datetime.now().isoformat(),
            'api_used': 'google_vision_comprehensive',
            'success': True,
            'errors': []
        }
        
        # Text detection
        text_result = self.detect_text(image_content)
        if text_result['success']:
            results['text_detection'] = text_result
        else:
            results['errors'].append(f"Text detection failed: {text_result['error']}")
        
        # Document structure analysis
        doc_result = self.detect_document_text(image_content)
        if doc_result['success']:
            results['document_analysis'] = doc_result
        else:
            results['errors'].append(f"Document analysis failed: {doc_result['error']}")
        
        # Image properties
        props_result = self.analyze_document_properties(image_content)
        if props_result['success']:
            results['image_properties'] = props_result
        else:
            results['errors'].append(f"Properties analysis failed: {props_result['error']}")
        
        # Object detection (optional)
        if include_objects:
            obj_result = self.detect_objects(image_content)
            if obj_result['success']:
                results['object_detection'] = obj_result
            else:
                results['errors'].append(f"Object detection failed: {obj_result['error']}")
        
        # Overall success status
        results['success'] = len(results['errors']) == 0
        
        return results
    
    def _extract_bounding_box(self, bounding_poly) -> Dict:
        """Extract bounding box coordinates from Vision API response"""
        if not bounding_poly or not bounding_poly.vertices:
            return {}
        
        vertices = []
        for vertex in bounding_poly.vertices:
            vertices.append({
                'x': getattr(vertex, 'x', 0),
                'y': getattr(vertex, 'y', 0)
            })
        
        return {
            'vertices': vertices,
            'normalized': getattr(bounding_poly, 'normalized_vertices', [])
        }
    
    def process_file_from_path(self, file_path: str, analysis_type: str = 'text') -> Dict:
        """
        Process a file from local path
        
        Args:
            file_path: Path to image file
            analysis_type: Type of analysis ('text', 'document', 'comprehensive')
        
        Returns:
            Analysis results
        """
        try:
            with open(file_path, 'rb') as image_file:
                content = image_file.read()
            
            if analysis_type == 'text':
                return self.detect_text(content)
            elif analysis_type == 'document':
                return self.detect_document_text(content)
            elif analysis_type == 'comprehensive':
                return self.comprehensive_analysis(content)
            else:
                return {'success': False, 'error': f'Unknown analysis type: {analysis_type}'}
                
        except Exception as e:
            return {'success': False, 'error': f'File processing error: {str(e)}'}
    
    def get_service_info(self) -> Dict:
        """Get information about the Google Vision service configuration"""
        return {
            'service_name': 'Google Cloud Vision API',
            'available': self.is_available(),
            'project_id': self.project_id,
            'credentials_configured': self.credentials_path is not None,
            'api_enabled': self.api_enabled,
            'max_results': self.max_results,
            'language_hints': self.language_hints,
            'features': [
                'Text Detection',
                'Document Text Detection',
                'Image Properties Analysis',
                'Object Detection',
                'Safe Search Detection',
                'Crop Hints'
            ]
        }

# Create global instance with fallback
try:
    google_vision_service = GoogleVisionService()
except Exception as e:
    print(f"Google Vision API not available: {e}")
    # Create a mock service that always returns fallback responses
    class MockGoogleVisionService:
        def __init__(self):
            self.client = None
            self.api_enabled = False
            
        def is_available(self) -> bool:
            return False
            
        def detect_text(self, image_content: bytes, language_hints=None) -> Dict:
            return {
                'success': False,
                'error': 'Google Vision API not available - use Tesseract OCR instead',
                'text': '',
                'confidence': 0.0
            }
            
        def detect_document_text(self, image_content: bytes) -> Dict:
            return {
                'success': False,
                'error': 'Google Vision API not available'
            }
            
        def analyze_document_properties(self, image_content: bytes) -> Dict:
            return {
                'success': False,
                'error': 'Google Vision API not available'
            }
            
        def detect_objects(self, image_content: bytes) -> Dict:
            return {
                'success': False,
                'error': 'Google Vision API not available'
            }
            
        def comprehensive_analysis(self, image_content: bytes, include_objects: bool = False) -> Dict:
            return {
                'success': False,
                'error': 'Google Vision API not available'
            }
            
        def process_file_from_path(self, file_path: str, analysis_type: str = 'text') -> Dict:
            return {
                'success': False,
                'error': 'Google Vision API not available'
            }
            
        def get_service_info(self) -> Dict:
            return {
                'service': 'Google Cloud Vision API',
                'status': 'disabled',
                'available': False,
                'features': []
            }
    
    google_vision_service = MockGoogleVisionService()