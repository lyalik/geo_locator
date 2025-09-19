import os
import logging
from typing import Optional, Dict, Any, Tuple, List
import exifread
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from PIL import Image
import numpy as np
import cv2
import asyncio
import requests
import json
from datetime import datetime
from .maps import map_aggregator
from .cache_service import GeolocationCache, MapCache
from .yandex_maps_service import YandexMapsService
from .dgis_service import DGISService
from .dataset_search_service import DatasetSearchService
try:
    from .roscosmos_satellite_service import RoscosmosService
    from .yandex_satellite_service import YandexSatelliteService
    SATELLITE_SERVICES_AVAILABLE = True
except ImportError:
    RoscosmosService = None
    YandexSatelliteService = None
    SATELLITE_SERVICES_AVAILABLE = False

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
        self.dataset_search = DatasetSearchService()
    
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
        """Convert coordinates to human-readable address with caching."""
        # Check cache first
        cached_result = MapCache.get_cached_reverse_geocode_result(lat, lon)
        if cached_result:
            logger.debug(f"Cache hit for reverse geocoding {lat}, {lon}")
            return cached_result
        
        try:
            location = self.geolocator.reverse(f"{lat}, {lon}", exactly_one=True)
            if location:
                result = location.raw
                # Cache the result
                MapCache.cache_reverse_geocode_result(lat, lon, result)
                return result
            return None
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            logger.warning(f"Geocoding service error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error in reverse geocoding: {e}")
            return None
    
    def process_image(self, image_path: str, location_hint: str = "") -> Dict[str, Any]:
        """Process an image to extract location information.

        Args:
            image_path: Path to the image file.
            location_hint: Optional text hint for location (e.g., "Moscow, Red Square").
        """
        result = {
            'success': False,
            'coordinates': None,
            'address': None,
            'error': None,
            'has_gps': False,
            'suggest_manual_input': False
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
            if coordinates:
                # Get address from coordinates
                address = self.reverse_geocode(*coordinates)
                # Поиск похожих мест в датасете
                dataset_matches = self.dataset_search.search_by_coordinates(
                    coordinates[0], coordinates[1], radius=0.01
                )
                
                result.update({
                    'success': True,
                    'coordinates': {
                        'latitude': coordinates[0],
                        'longitude': coordinates[1]
                    },
                    'address': address,
                    'has_gps': True,
                    'dataset_matches': dataset_matches
                })
                return result

            # If no GPS in EXIF, try alternative methods
            if location_hint:
                result = self._process_with_location_hint(image_path, location_hint)
                if result['success']:
                    return result

            # If still no location, suggest manual input
            result.update({
                'error': "Unable to determine location automatically",
                'suggest_manual_input': True
            })

        except Exception as e:
            logger.error(f"Error processing image: {e}")
            result['error'] = str(e)

        return result

    def _process_with_location_hint(self, image_path: str, location_hint: str) -> Dict[str, Any]:
        """Try to determine location using location hint and satellite imagery."""
        result = {
            'success': False,
            'coordinates': None,
            'address': None,
            'error': None,
            'has_gps': False
        }

        try:
            # Step 1: Search for places using the location hint
            search_result = asyncio.run(map_aggregator.search_places(location_hint, 55.75, 37.62))  # Default: Moscow
            if not search_result or 'error' in search_result:
                result['error'] = "No places found for the given location hint"
                return result

            # Step 2: Get coordinates from the first found place
            # Note: This is a simplified example. Actual implementation depends on the API response structure.
            # For Yandex, coordinates might be in search_result['features'][0]['geometry']['coordinates']
            # For 2GIS, coordinates might be in search_result['result']['items'][0]['point']
            coordinates = None
            if 'features' in search_result and search_result['features']:
                coordinates = search_result['features'][0]['geometry']['coordinates']
            elif 'result' in search_result and 'items' in search_result['result'] and search_result['result']['items']:
                coordinates = search_result['result']['items'][0]['point'].split(',')
                coordinates = (float(coordinates[1]), float(coordinates[0]))  # lat, lon

            if not coordinates:
                result['error'] = "No coordinates found for the location hint"
                return result

            # Step 3: Get satellite image for the found coordinates
            satellite_result = asyncio.run(map_aggregator.get_satellite_image(coordinates[0], coordinates[1]))
            if not satellite_result or 'error' in satellite_result:
                result['error'] = "Failed to get satellite image for the location"
                return result

            # Step 4: Compare the uploaded image with the satellite image
            match_score = self._compare_images(image_path, satellite_result['image'])
            if match_score < 30:  # Threshold for considering images similar
                result['error'] = "Uploaded image does not match satellite imagery for the location"
                return result

            # Step 5: Success - return the found coordinates
            address = asyncio.run(map_aggregator.reverse_geocode(coordinates[0], coordinates[1]))
            result.update({
                'success': True,
                'coordinates': {
                    'latitude': coordinates[0],
                    'longitude': coordinates[1]
                },
                'address': address.get('result', {}).get('items', [{}])[0] if address else None,
                'has_gps': False,
                'method': 'location_hint_matching'
            })

        except Exception as e:
            logger.error(f"Error processing with location hint: {e}")
            result['error'] = str(e)

        return result

    def _compare_images(self, image_path: str, satellite_image_bytes: bytes) -> int:
        """Compare uploaded image with satellite image using feature matching."""
        try:
            # Load images
            img1 = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            img2 = cv2.imdecode(np.frombuffer(satellite_image_bytes, np.uint8), cv2.IMREAD_GRAYSCALE)

            # Initialize SIFT detector
            sift = cv2.SIFT_create()

            # Find keypoints and descriptors
            kp1, des1 = sift.detectAndCompute(img1, None)
            kp2, des2 = sift.detectAndCompute(img2, None)

            # Match descriptors using FLANN
            flann = cv2.FlannBasedMatcher(dict(algorithm=1, trees=5), dict(checks=50))
            matches = flann.knnMatch(des1, des2, k=2)

            # Apply Lowe's ratio test
            good_matches = []
            for m, n in matches:
                if m.distance < 0.7 * n.distance:
                    good_matches.append(m)

            # Calculate match score (percentage of good matches)
            match_score = (len(good_matches) / len(matches)) * 100 if matches else 0
            return int(match_score)

        except Exception as e:
            logger.error(f"Error comparing images: {e}")
            return 0
    
    def get_location_from_image(self, image_path: str, location_hint: str = "") -> Dict[str, Any]:
        """
        Main function to get location from image with caching.
        
        Args:
            image_path: Path to the image file
            location_hint: Optional location hint
            
        Returns:
            Dictionary with location results
        """
        # Check cache first
        cached_result = GeolocationCache.get_cached_location_result(image_path, location_hint)
        if cached_result:
            logger.debug(f"Cache hit for geolocation {image_path}")
            return cached_result
        
        # Process image
        result = self.process_image(image_path, location_hint)
        
        # Cache the result if successful
        if result.get('success'):
            GeolocationCache.cache_location_result(image_path, location_hint, result)
        
        return result


# Example usage
if __name__ == "__main__":
    service = GeoLocationService()
    result = service.process_image("path/to/your/image.jpg")
    print("Processing result:", result)
