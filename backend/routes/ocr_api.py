"""
OCR API endpoints for text extraction and multimodal analysis
"""

from flask import Blueprint, request, jsonify
import logging
import os
from werkzeug.utils import secure_filename
from ..services.ocr_service import OCRService

logger = logging.getLogger(__name__)

ocr_api = Blueprint('ocr_api', __name__)
ocr_service = OCRService()

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@ocr_api.route('/analyze-document', methods=['POST'])
def analyze_document():
    """Analyze uploaded document image for OCR"""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Read file data
        file_data = file.read()
        
        # Analyze document
        analysis = ocr_service.analyze_uploaded_image(file_data)
        
        return jsonify({
            'success': True,
            'data': {
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
        })
        
    except Exception as e:
        logger.error(f"Error analyzing document: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@ocr_api.route('/extract-text', methods=['POST'])
def extract_text():
    """Extract text from uploaded image"""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Read file data and analyze
        file_data = file.read()
        analysis = ocr_service.analyze_uploaded_image(file_data)
        
        return jsonify({
            'success': True,
            'data': {
                'text': analysis.full_text,
                'confidence': analysis.metadata.get('avg_confidence', 0),
                'languages': analysis.detected_languages,
                'word_count': len(analysis.full_text.split()) if analysis.full_text else 0
            }
        })
        
    except Exception as e:
        logger.error(f"Error extracting text: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@ocr_api.route('/analyze-address', methods=['POST'])
def analyze_address():
    """Analyze text for addresses and building information from signage"""
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({'error': 'Text is required'}), 400
        
        text = data['text']
        
        # Analyze address text
        address_analysis = ocr_service.analyze_address_text(text)
        
        return jsonify({
            'success': True,
            'data': {
                'addresses': address_analysis.addresses,
                'building_names': address_analysis.building_names,
                'street_numbers': address_analysis.street_numbers,
                'organization_names': address_analysis.organization_names,
                'phone_numbers': address_analysis.phone_numbers,
                'confidence_score': address_analysis.confidence_score,
                'detected_language': address_analysis.detected_language
            }
        })
        
    except Exception as e:
        logger.error(f"Error analyzing address: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@ocr_api.route('/analyze-address-image', methods=['POST'])
def analyze_address_image():
    """Analyze uploaded image for address and building information"""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Read file data and analyze document
        file_data = file.read()
        document_analysis = ocr_service.analyze_uploaded_image(file_data)
        
        # Analyze extracted text for violations
        violation_analysis = ocr_service.analyze_violation_text(document_analysis.full_text)
        
        return jsonify({
            'success': True,
            'data': {
                'document_analysis': {
                    'full_text': document_analysis.full_text,
                    'document_type': document_analysis.document_type,
                    'detected_languages': document_analysis.detected_languages,
                    'key_information': document_analysis.key_information,
                    'text_regions_count': len(document_analysis.text_regions),
                    'avg_confidence': document_analysis.metadata.get('avg_confidence', 0)
                },
                'violation_analysis': {
                    'violation_keywords': violation_analysis.violation_keywords,
                    'addresses': violation_analysis.addresses,
                    'dates': violation_analysis.dates,
                    'legal_references': violation_analysis.legal_references,
                    'severity_indicators': violation_analysis.severity_indicators,
                    'confidence_score': violation_analysis.confidence_score,
                    'is_violation_related': violation_analysis.confidence_score > 0.3
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error analyzing violation image: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@ocr_api.route('/detect-text-regions', methods=['POST'])
def detect_text_regions():
    """Detect and return text regions with coordinates"""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Read file data and analyze
        file_data = file.read()
        analysis = ocr_service.analyze_uploaded_image(file_data)
        
        # Format text regions for response
        regions = []
        for region in analysis.text_regions:
            regions.append({
                'text': region.text,
                'confidence': region.confidence,
                'bbox': {
                    'x': region.bbox[0],
                    'y': region.bbox[1],
                    'width': region.bbox[2],
                    'height': region.bbox[3]
                },
                'language': region.language
            })
        
        return jsonify({
            'success': True,
            'data': {
                'regions': regions,
                'total_regions': len(regions),
                'image_dimensions': {
                    'width': analysis.metadata.get('image_shape', [0, 0, 0])[1],
                    'height': analysis.metadata.get('image_shape', [0, 0, 0])[0]
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error detecting text regions: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@ocr_api.route('/batch-analyze', methods=['POST'])
def batch_analyze():
    """Analyze multiple images in batch"""
    try:
        # Check if files are present
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        
        if not files or len(files) == 0:
            return jsonify({'error': 'No files selected'}), 400
        
        # Limit batch size
        if len(files) > 10:
            return jsonify({'error': 'Maximum 10 files allowed per batch'}), 400
        
        results = []
        
        for file in files:
            if file.filename == '' or not allowed_file(file.filename):
                results.append({
                    'filename': file.filename,
                    'success': False,
                    'error': 'Invalid file'
                })
                continue
            
            try:
                # Read file data and analyze
                file_data = file.read()
                analysis = ocr_service.analyze_uploaded_image(file_data)
                
                results.append({
                    'filename': file.filename,
                    'success': True,
                    'data': {
                        'full_text': analysis.full_text,
                        'document_type': analysis.document_type,
                        'detected_languages': analysis.detected_languages,
                        'text_regions_count': len(analysis.text_regions),
                        'avg_confidence': analysis.metadata.get('avg_confidence', 0),
                        'key_information': analysis.key_information
                    }
                })
                
            except Exception as e:
                logger.error(f"Error analyzing file {file.filename}: {e}")
                results.append({
                    'filename': file.filename,
                    'success': False,
                    'error': 'Analysis failed'
                })
        
        # Calculate summary statistics
        successful_analyses = [r for r in results if r['success']]
        summary = {
            'total_files': len(files),
            'successful_analyses': len(successful_analyses),
            'failed_analyses': len(files) - len(successful_analyses),
            'avg_confidence': sum(r['data']['avg_confidence'] for r in successful_analyses) / len(successful_analyses) if successful_analyses else 0,
            'detected_languages': list(set(lang for r in successful_analyses for lang in r['data']['detected_languages']))
        }
        
        return jsonify({
            'success': True,
            'data': {
                'results': results,
                'summary': summary
            }
        })
        
    except Exception as e:
        logger.error(f"Error in batch analysis: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@ocr_api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        return jsonify({
            'success': True,
            'service': 'OCR Service',
            'status': 'healthy',
            'supported_formats': list(ALLOWED_EXTENSIONS),
            'endpoints': [
                '/api/ocr/analyze-document',
                '/api/ocr/extract-text',
                '/api/ocr/analyze-address',
                '/api/ocr/analyze-address-image',
                '/api/ocr/detect-text-regions',
                '/api/ocr/batch-analyze'
            ]
        })
        
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return jsonify({'error': 'Internal server error'}), 500
