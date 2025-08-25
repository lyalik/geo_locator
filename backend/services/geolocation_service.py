import os
import logging
from typing import Optional, Dict, Any, Tuple
import exifread
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from PIL import Image
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeoLocationService:
    """
    Service for extracting and processing geolocation data from images.
    Handles EXIF data extraction, coordinate conversion, and reverse geocoding.
    """
    
    def __init__(self):
        self.geolocator = Nominatim(user_agent="geo_locator_app")
    
    def get_exif_data(self, image_path: str) -> Optional[Dict]:
        """Extract EXIF data from an image."""
        try:
            with open(image_path, 'rb') as f:
                tags = exifread.process_file(f, details=False)
                return {tag: str(value) for tag, value in tags.items()}
        except Exception as e:
            logger.error(f"Error extracting EXIF data: {e}")
            return None
    
    def get_gps_coordinates(self, exif_data: Dict) -> Optional[Tuple[float, float]]:
        """Extract GPS coordinates from EXIF data."""
        try:
            # Check if GPS data exists in EXIF
            if not all(k in exif_data for k in ['GPS GPSLatitude', 'GPS GPSLongitude', 'GPS GPSLatitudeRef', 'GPS GPSLongitudeRef']):
                return None
                
            # Get latitude
            lat = self._convert_to_degrees(exif_data['GPS GPSLatitude'])
            if exif_data['GPS GPSLatitudeRef'] == 'S':
                lat = -lat
                
            # Get longitude
            lon = self._convert_to_degrees(exif_data['GPS GPSLongitude'])
            if exif_data['GPS GPSLongitudeRef'] == 'W':
                lon = -lon
                
            return (lat, lon)
        except Exception as e:
            logger.error(f"Error parsing GPS coordinates: {e}")
            return None
    
    def _convert_to_degrees(self, value: str) -> float:
        """Convert GPS coordinates to decimal degrees."""
        try:
            # Handle different GPS coordinate formats
            if isinstance(value, str):
                # Format: "[degrees, minutes, seconds]"
                parts = value.strip('[]').replace("'", '').replace('"', '').split(',')
                d = float(parts[0].strip())
                m = float(parts[1].strip()) if len(parts) > 1 else 0.0
                s = float(parts[2].strip()) if len(parts) > 2 else 0.0
                return d + (m / 60.0) + (s / 3600.0)
            return float(value)
        except Exception as e:
            logger.error(f"Error converting GPS coordinate: {e}")
            raise ValueError("Invalid GPS coordinate format")
    
    def reverse_geocode(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Convert coordinates to human-readable address."""
        try:
            location = self.geolocator.reverse(f"{lat}, {lon}", exactly_one=True)
            if location:
                return location.raw
            return None
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.warning(f"Geocoding service error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error in reverse geocoding: {e}")
            return None
    
    def process_image(self, image_path: str) -> Dict[str, Any]:
        """Process an image to extract location information."""
        result = {
            'success': False,
            'coordinates': None,
            'address': None,
            'error': None,
            'has_gps': False
        }
        
        try:
            # Check if file exists
            if not os.path.exists(image_path):
                result['error'] = "Image file not found"
                return result
            
            # Extract EXIF data
            exif_data = self.get_exif_data(image_path)
            if not exif_data:
                result['error'] = "No EXIF data found in image"
                return result
            
            # Get GPS coordinates
            coordinates = self.get_gps_coordinates(exif_data)
            if not coordinates:
                result['error'] = "No GPS coordinates found in EXIF data"
                return result
            
            # Get address from coordinates
            address = self.reverse_geocode(*coordinates)
            
            result.update({
                'success': True,
                'coordinates': {
                    'latitude': coordinates[0],
                    'longitude': coordinates[1]
                },
                'address': address,
                'has_gps': True
            })
            
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            result['error'] = str(e)
        
        return result


# Example usage
if __name__ == "__main__":
    service = GeoLocationService()
    result = service.process_image("path/to/your/image.jpg")
    print("Processing result:", result)
