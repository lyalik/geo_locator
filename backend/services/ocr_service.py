"""
OCR Service for text extraction and multimodal analysis
Provides OCR capabilities, text detection, and document analysis
"""

import asyncio
import cv2
import numpy as np
import pytesseract
import logging
from PIL import Image, ImageEnhance, ImageFilter
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import re
import json
from .cache_service import CacheService

logger = logging.getLogger(__name__)

@dataclass
class TextRegion:
    """Detected text region with coordinates and content"""
    text: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x, y, width, height
    language: str = "rus"

@dataclass
class DocumentAnalysis:
    """Document analysis results"""
    text_regions: List[TextRegion]
    full_text: str
    detected_languages: List[str]
    document_type: str
    key_information: Dict[str, Any]
    metadata: Dict[str, Any]

@dataclass
class AddressAnalysis:
    """Address and building name analysis from signage"""
    addresses: List[str]
    building_names: List[str]
    street_numbers: List[str]
    organization_names: List[str]
    phone_numbers: List[str]
    confidence_score: float
    detected_language: str

class OCRService:
    """Service for OCR and multimodal text analysis"""
    
    def __init__(self, cache_service: Optional[CacheService] = None):
        """Initialize OCR service with optional caching"""
        self.cache_service = cache_service
        
        # Configure Tesseract for Russian and English
        self.tesseract_config = r'--oem 3 --psm 6 -l rus+eng'
        
        # Address and building name patterns
        self.address_patterns = [
            r'ул\.?\s+[А-Яа-я\s]+,?\s*\d+[а-я]?',
            r'улица\s+[А-Яа-я\s]+,?\s*\d+[а-я]?',
            r'пр\.?\s+[А-Яа-я\s]+,?\s*\d+[а-я]?',
            r'проспект\s+[А-Яа-я\s]+,?\s*\d+[а-я]?',
            r'пер\.?\s+[А-Яа-я\s]+,?\s*\d+[а-я]?',
            r'переулок\s+[А-Яа-я\s]+,?\s*\d+[а-я]?',
            r'\d+[а-я]?\s+[А-Яа-я\s]+\s+ул\.?',
            r'\d+[а-я]?\s+[А-Яа-я\s]+\s+улица'
        ]
        
        # Phone number patterns
        self.phone_patterns = [
            r'\+7\s*\(?\d{3}\)?\s*\d{3}[-\s]?\d{2}[-\s]?\d{2}',
            r'8\s*\(?\d{3}\)?\s*\d{3}[-\s]?\d{2}[-\s]?\d{2}',
            r'\(?\d{3}\)?\s*\d{3}[-\s]?\d{2}[-\s]?\d{2}'
        ]
        
        # Violation-related keywords
        self.violation_keywords = [
            'нарушение', 'незаконный', 'самовольный', 'строительство',
            'снос', 'реконструкция', 'перепланировка', 'административный',
            'штраф', 'предписание', 'постановление', 'протокол',
            'градостроительный', 'земельный', 'кодекс', 'закон'
        ]
        
        # Document type patterns
        self.document_patterns = {
            'постановление': r'постановлени[ея]',
            'предписание': r'предписани[ея]',
            'протокол': r'протокол',
            'жалоба': r'жалоб[ауы]',
            'заявление': r'заявлени[ея]',
            'справка': r'справк[ауи]'
        }
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR results"""
        try:
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # Noise reduction
            denoised = cv2.medianBlur(gray, 3)
            
            # Enhance contrast
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(denoised)
            
            # Adaptive thresholding
            binary = cv2.adaptiveThreshold(
                enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Morphological operations to clean up
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            return cleaned
            
        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            return image
    
    def detect_text_regions(self, image: np.ndarray) -> List[TextRegion]:
        """Detect text regions in image using Tesseract"""
        try:
            # Preprocess image
            processed_image = self.preprocess_image(image)
            
            # Get detailed OCR data
            data = pytesseract.image_to_data(
                processed_image,
                config=self.tesseract_config['default'],
                lang='rus+eng',
                output_type=pytesseract.Output.DICT
            )
            
            text_regions = []
            n_boxes = len(data['level'])
            
            for i in range(n_boxes):
                confidence = int(data['conf'][i])
                text = data['text'][i].strip()
                
                # Filter out low confidence and empty text
                if confidence > 30 and text:
                    x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                    
                    text_region = TextRegion(
                        text=text,
                        confidence=confidence / 100.0,
                        bbox=(x, y, w, h),
                        language='rus' if self._is_cyrillic(text) else 'eng'
                    )
                    text_regions.append(text_region)
            
            return text_regions
            
        except Exception as e:
            logger.error(f"Error detecting text regions: {e}")
            return []
    
    def _is_cyrillic(self, text: str) -> bool:
        """Check if text contains Cyrillic characters"""
        cyrillic_pattern = re.compile(r'[а-яё]', re.IGNORECASE)
        return bool(cyrillic_pattern.search(text))
    
    def extract_full_text(self, image: np.ndarray) -> str:
        """Extract full text from image"""
        try:
            processed_image = self.preprocess_image(image)
            
            # Extract text with Russian and English support
            text = pytesseract.image_to_string(
                processed_image,
                config=self.tesseract_config['default'],
                lang='rus+eng'
            )
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error extracting full text: {e}")
            return ""
    
    def analyze_document(self, image: np.ndarray) -> DocumentAnalysis:
        """Comprehensive document analysis"""
        try:
            # Extract text regions and full text
            text_regions = self.detect_text_regions(image)
            full_text = self.extract_full_text(image)
            
            # Detect languages
            detected_languages = []
            if any(self._is_cyrillic(region.text) for region in text_regions):
                detected_languages.append('rus')
            if any(not self._is_cyrillic(region.text) and region.text.isalpha() for region in text_regions):
                detected_languages.append('eng')
            
            # Determine document type
            document_type = self._classify_document_type(full_text)
            
            # Extract key information
            key_information = self._extract_key_information(full_text)
            
            # Metadata
            metadata = {
                'total_regions': len(text_regions),
                'avg_confidence': np.mean([r.confidence for r in text_regions]) if text_regions else 0,
                'text_length': len(full_text),
                'image_shape': image.shape
            }
            
            return DocumentAnalysis(
                text_regions=text_regions,
                full_text=full_text,
                detected_languages=detected_languages,
                document_type=document_type,
                key_information=key_information,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error analyzing document: {e}")
            return DocumentAnalysis([], "", [], "unknown", {}, {})
    
    def _classify_document_type(self, text: str) -> str:
        """Classify document type based on text content"""
        text_lower = text.lower()
        
        for doc_type, pattern in self.document_patterns.items():
            if re.search(pattern, text_lower):
                return doc_type
        
        return "document"
    
    def _extract_key_information(self, text: str) -> Dict[str, Any]:
        """Extract key information from text"""
        key_info = {}
        
        # Extract dates
        date_patterns = [
            r'\d{1,2}\.\d{1,2}\.\d{4}',  # DD.MM.YYYY
            r'\d{1,2}/\d{1,2}/\d{4}',   # DD/MM/YYYY
            r'\d{4}-\d{1,2}-\d{1,2}'    # YYYY-MM-DD
        ]
        
        dates = []
        for pattern in date_patterns:
            dates.extend(re.findall(pattern, text))
        key_info['dates'] = list(set(dates))
        
        # Extract addresses (simplified)
        address_patterns = [
            r'г\.\s*[А-Я][а-я]+',  # г. Москва
            r'ул\.\s*[А-Я][а-я\s]+',  # ул. Название
            r'пр\.\s*[А-Я][а-я\s]+',  # пр. Название
            r'д\.\s*\d+',  # д. 123
        ]
        
        addresses = []
        for pattern in address_patterns:
            addresses.extend(re.findall(pattern, text))
        key_info['addresses'] = addresses
        
        # Extract numbers (potentially case numbers, amounts, etc.)
        numbers = re.findall(r'\d+', text)
        key_info['numbers'] = numbers[:10]  # Limit to first 10 numbers
        
        # Extract legal references
        legal_refs = []
        legal_patterns = [
            r'ст\.\s*\d+',  # ст. 123
            r'статья\s*\d+',  # статья 123
            r'п\.\s*\d+',  # п. 123
            r'пункт\s*\d+'  # пункт 123
        ]
        
        for pattern in legal_patterns:
            legal_refs.extend(re.findall(pattern, text, re.IGNORECASE))
        key_info['legal_references'] = legal_refs
        
        return key_info
    
    def analyze_address_text(self, text: str) -> AddressAnalysis:
        """Analyze text for addresses and building information from signage"""
        try:
            # Extract addresses using improved patterns
            addresses = []
            
            # Улучшенные паттерны для адресов
            address_patterns = [
                r'г\.?\s*([А-Я][а-я]+(?:-[А-Я][а-я]+)?)',  # г. Краснодар
                r'([А-Я][а-я]+(?:-[А-Я][а-я]+)?),?\s*ул\.?\s*([А-Я][а-я\s]+)',  # Краснодар, ул. Красная
                r'ул\.?\s*([А-Я][а-я\s]+),?\s*(\d+(?:/\d+)?)',  # ул. Красная, 176/2
                r'([А-Я][а-я\s]+\s+улица),?\s*(\d+(?:/\d+)?)',  # Красная улица, 176/2
                r'([А-Я][а-я]+(?:-[А-Я][а-я]+)?)[,\s]+([А-Я][а-я\s]+\s+улица)[,\s]+(\d+(?:/\d+)?)'  # Краснодар, Красная улица, 176/2
            ]
            
            for pattern in address_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        address_parts = [part.strip() for part in match if part.strip()]
                        if address_parts:
                            addresses.append(' '.join(address_parts))
                    else:
                        addresses.append(match.strip())
            
            # Extract building names and organizations
            building_names = []
            organization_names = []
            
            # Паттерны для названий зданий и организаций
            org_patterns = [
                r'(ООО\s+[А-Я][а-я\s"]+)',
                r'(ЗАО\s+[А-Я][а-я\s"]+)',
                r'(ИП\s+[А-Я][а-я\s]+)',
                r'([А-Я][а-я]+\s+центр)',
                r'([А-Я][а-я]+\s+магазин)',
                r'([А-Я][а-я]+\s+офис)'
            ]
            
            for pattern in org_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                organization_names.extend([match.strip() for match in matches])
            
            # Extract street numbers
            street_numbers = re.findall(r'\b(\d+(?:/\d+)?)\b', text)
            
            # Extract phone numbers
            phone_numbers = []
            for pattern in self.phone_patterns:
                matches = re.findall(pattern, text)
                phone_numbers.extend(matches)
            
            # Extract building names and organization names
            lines = text.split('\n')
            building_names = []
            organization_names = []
            street_numbers = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Check for building/organization names (usually in uppercase or title case)
                if len(line) > 3 and (line.isupper() or line.istitle()):
                    # Skip if it's just an address
                    if not any(re.search(pattern, line, re.IGNORECASE) for pattern in self.address_patterns):
                        if any(word in line.lower() for word in ['магазин', 'кафе', 'ресторан', 'банк', 'аптека', 'салон', 'центр', 'офис']):
                            organization_names.append(line)
                        else:
                            building_names.append(line)
                
                # Extract street numbers
                number_match = re.search(r'\b\d+[а-я]?\b', line)
                if number_match:
                    street_numbers.append(number_match.group())
            
            # Detect language
            russian_chars = len(re.findall(r'[а-яё]', text.lower()))
            english_chars = len(re.findall(r'[a-z]', text.lower()))
            detected_language = 'rus' if russian_chars > english_chars else 'eng'
            
            return AddressAnalysis(
                addresses=list(set(addresses)),
                building_names=list(set(building_names)),
                street_numbers=list(set(street_numbers)),
                organization_names=list(set(organization_names)),
                phone_numbers=list(set(phone_numbers)),
                confidence_score=max(0.1, (len(addresses) + len(organization_names) + len(phone_numbers)) / max(1, len(text.split()) / 5)),
                detected_language='rus' if self._is_cyrillic(text) else 'eng'
            )
            
        except Exception as e:
            logger.error(f"Error analyzing address text: {e}")
            return AddressAnalysis([], [], [], [], [], 0.0, 'rus')
    
    async def process_image_async(self, image_path: str) -> DocumentAnalysis:
        """Asynchronously process image for OCR analysis"""
        cache_key = f"ocr_analysis:{image_path}"
        
        # Check cache first
        cached_result = await self.cache_service.get(cache_key)
        if cached_result:
            # Reconstruct TextRegion objects
            text_regions = [
                TextRegion(
                    text=region['text'],
                    confidence=region['confidence'],
                    bbox=tuple(region['bbox']),
                    language=region['language']
                )
                for region in cached_result['text_regions']
            ]
            
            return DocumentAnalysis(
                text_regions=text_regions,
                full_text=cached_result['full_text'],
                detected_languages=cached_result['detected_languages'],
                document_type=cached_result['document_type'],
                key_information=cached_result['key_information'],
                metadata=cached_result['metadata']
            )
        
        try:
            # Load and process image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Perform analysis
            analysis = self.analyze_document(image)
            
            # Cache the result
            cache_data = {
                'text_regions': [
                    {
                        'text': region.text,
                        'confidence': region.confidence,
                        'bbox': region.bbox,
                        'language': region.language
                    }
                    for region in analysis.text_regions
                ],
                'full_text': analysis.full_text,
                'detected_languages': analysis.detected_languages,
                'document_type': analysis.document_type,
                'key_information': analysis.key_information,
                'metadata': analysis.metadata
            }
            
            await self.cache_service.set(cache_key, cache_data, ttl=3600)  # 1 hour
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error processing image async: {e}")
            return DocumentAnalysis([], "", [], "unknown", {}, {})
    
    # Synchronous wrappers for Flask compatibility
    def process_image_sync(self, image_path: str) -> DocumentAnalysis:
        """Synchronous wrapper for process_image_async"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.process_image_async(image_path))
        finally:
            loop.close()
    
    def analyze_uploaded_image(self, image_data: bytes) -> DocumentAnalysis:
        """Analyze image from uploaded bytes"""
        try:
            # Convert bytes to numpy array
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                raise ValueError("Could not decode image data")
            
            return self.analyze_document(image)
            
        except Exception as e:
            logger.error(f"Error analyzing uploaded image: {e}")
            return DocumentAnalysis([], "", [], "unknown", {}, {})
