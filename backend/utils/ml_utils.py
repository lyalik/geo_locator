import os
import google.generativeai as genai
from PIL import Image
import io

class GeminiProcessor:
    def __init__(self, api_key=None):
        """Initialize the Gemini API client."""
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro-vision')
    
    def analyze_image(self, image_data, prompt=None):
        """
        Analyze an image using Gemini Vision API.
        
        Args:
            image_data: Binary image data or file path
            prompt: Optional prompt to guide the analysis
            
        Returns:
            dict: Analysis results
        """
        try:
            # If image_data is a file path
            if isinstance(image_data, str) and os.path.isfile(image_data):
                img = Image.open(image_data)
            # If image_data is binary
            elif isinstance(image_data, bytes):
                img = Image.open(io.BytesIO(image_data))
            else:
                raise ValueError("Invalid image data. Provide either a file path or binary data.")
            
            # Default prompt if none provided
            if not prompt:
                prompt = """
                Analyze this image and provide the following information:
                1. Description of the location
                2. Any recognizable landmarks or features
                3. Estimated geographical location (if possible)
                4. Any text visible in the image
                """
            
            # Generate content
            response = self.model.generate_content([prompt, img])
            
            return {
                'success': True,
                'analysis': response.text,
                'raw_response': response._raw_response
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def compare_locations(self, image1_data, image2_data):
        """
        Compare two locations from images and determine if they match.
        
        Args:
            image1_data: First image data (file path or binary)
            image2_data: Second image data (file path or binary)
            
        Returns:
            dict: Comparison results with confidence score
        """
        try:
            # Process first image
            img1 = self._load_image(image1_data)
            # Process second image
            img2 = self._load_image(image2_data)
            
            prompt = """
            Compare these two images and determine if they show the same location.
            Provide a confidence score (0-100) and a brief explanation.
            Focus on architectural features, natural landmarks, and overall scene composition.
            """
            
            response = self.model.generate_content([prompt, img1, img2])
            
            return {
                'success': True,
                'comparison': response.text,
                'raw_response': response._raw_response
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _load_image(self, image_data):
        """Helper method to load image from path or binary data."""
        if isinstance(image_data, str) and os.path.isfile(image_data):
            return Image.open(image_data)
        elif isinstance(image_data, bytes):
            return Image.open(io.BytesIO(image_data))
        else:
            raise ValueError("Invalid image data. Provide either a file path or binary data.")

def extract_geolocation_from_text(text):
    """
    Extract potential location information from text using Gemini.
    
    Args:
        text: Input text to analyze
        
    Returns:
        dict: Extracted location information
    """
    try:
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""
        Extract location information from the following text. 
        Return a JSON object with the following structure:
        {{
            "city": "city name or null",
            "country": "country name or null",
            "landmark": "specific landmark or null",
            "coordinates": {{"lat": float, "lng": float}} or null,
            "confidence": 0-100
        }}
        
        Text: {text}
        """
        
        response = model.generate_content(prompt)
        
        # Parse the response (assuming it's valid JSON)
        try:
            import json
            result = json.loads(response.text.strip())
            return {
                'success': True,
                'location': result
            }
        except json.JSONDecodeError:
            return {
                'success': False,
                'error': 'Failed to parse location information',
                'raw_response': response.text
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
