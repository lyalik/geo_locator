import os
import requests
from typing import Dict, Optional, Union, List, Tuple
import json
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YandexMapsAPI:
    """Wrapper for Yandex Maps API."""
    
    BASE_URL = "https://search-maps.yandex.ru/v1/"
    GEOCODE_URL = "https://geocode-maps.yandex.ru/1.x/"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('YANDEX_MAPS_API_KEY')
        if not self.api_key:
            logger.warning("Yandex Maps API key not provided")
    
    def search(self, query: str, lang: str = 'ru_RU', results: int = 5) -> Dict:
        """Search for locations using Yandex Maps API."""
        if not self.api_key:
            return {"error": "Yandex Maps API key not configured"}
            
        params = {
            'apikey': self.api_key,
            'text': query,
            'lang': lang,
            'type': 'geo',
            'results': results
        }
        
        try:
            response = requests.get(self.BASE_URL, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Yandex Maps API error: {str(e)}")
            return {"error": f"Yandex Maps API request failed: {str(e)}"}
    
    def reverse_geocode(self, lat: float, lon: float, kind: str = None) -> Dict:
        """Get address information from coordinates."""
        params = {
            'apikey': self.api_key,
            'geocode': f"{lon},{lat}",
            'format': 'json',
            'results': 1
        }
        
        if kind:
            params['kind'] = kind
            
        try:
            response = requests.get(self.GEOCODE_URL, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Yandex Geocoding API error: {str(e)}")
            return {"error": f"Geocoding API request failed: {str(e)}"}


class DgisAPI:
    """Wrapper for 2GIS API."""
    
    BASE_URL = "https://catalog.api.2gis.com/3.0/"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('DGIS_API_KEY')
        if not self.api_key:
            logger.warning("2GIS API key not provided")
    
    def search(self, query: str, region_id: int = None, fields: str = 'items.point') -> Dict:
        """Search for locations using 2GIS API."""
        if not self.api_key:
            return {"error": "2GIS API key not configured"}
            
        headers = {
            'Authorization': f'Key {self.api_key}'
        }
        
        params = {
            'q': query,
            'fields': fields
        }
        
        if region_id:
            params['region_id'] = region_id
            
        try:
            response = requests.get(
                f"{self.BASE_URL}items/geocode",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"2GIS API error: {str(e)}")
            return {"error": f"2GIS API request failed: {str(e)}"}
    
    def get_building_info(self, point: str, fields: str = 'items.building') -> Dict:
        """Get building information from coordinates."""
        if not self.api_key:
            return {"error": "2GIS API key not configured"}
            
        headers = {
            'Authorization': f'Key {self.api_key}'
        }
        
        params = {
            'point': point,
            'fields': fields
        }
        
        try:
            response = requests.get(
                f"{self.BASE_URL}items/geocode",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"2GIS Building API error: {str(e)}")
            return {"error": f"2GIS Building API request failed: {str(e)}"}


class SentinelAPI:
    """Wrapper for Sentinel Hub API."""
    
    BASE_URL = "https://services.sentinel-hub.com/api/v1/"
    
    def __init__(self, client_id: str = None, client_secret: str = None):
        self.client_id = client_id or os.getenv('SENTINEL_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('SENTINEL_CLIENT_SECRET')
        self.token = None
        self.token_expiry = None
        
        if not self.client_id or not self.client_secret:
            logger.warning("Sentinel Hub credentials not fully provided")
    
    def _get_token(self) -> Optional[str]:
        """Get or refresh OAuth token."""
        if self.token and self.token_expiry and datetime.utcnow() < self.token_expiry:
            return self.token
            
        if not self.client_id or not self.client_secret:
            return None
            
        auth_url = "https://services.sentinel-hub.com/oauth/token"
        
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        try:
            response = requests.post(auth_url, data=data)
            response.raise_for_status()
            token_data = response.json()
            
            self.token = token_data['access_token']
            # Set token expiry 5 minutes before actual expiry to be safe
            self.token_expiry = datetime.utcnow() + timedelta(seconds=token_data['expires_in'] - 300)
            
            return self.token
        except requests.exceptions.RequestException as e:
            logger.error(f"Sentinel Hub auth error: {str(e)}")
            return None
    
    def get_satellite_image(self, bbox: List[float], time_range: Tuple[str, str], 
                          width: int = 512, height: int = 512) -> Optional[bytes]:
        """Get a satellite image from Sentinel Hub."""
        token = self._get_token()
        if not token:
            return None
            
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # This is a simplified example - you'll need to customize the request
        # based on your Sentinel Hub configuration and requirements
        payload = {
            "input": {
                "bounds": {
                    "bbox": bbox,
                    "properties": {
                        "crs": "http://www.opengis.net/def/crs/EPSG/0/4326"
                    }
                },
                "data": [
                    {
                        "type": "sentinel-2-l2a",
                        "dataFilter": {
                            "timeRange": {
                                "from": time_range[0],
                                "to": time_range[1]
                            },
                            "mosaickingOrder": "mostRecent"
                        }
                    }
                ]
            },
            "output": {
                "width": width,
                "height": height,
                "responses": [
                    {
                        "identifier": "default",
                        "format": {
                            "type": "image/jpeg"
                        }
                    }
                ]
            },
            "evalscript": """
                //VERSION=3
                function setup() {
                    return {
                        input: ["B04", "B03", "B02", "dataMask"],
                        output: { bands: 4 }
                    };
                }
                
                function evaluatePixel(sample) {
                    return [
                        sample.B04 * 2.5,
                        sample.B03 * 2.5,
                        sample.B02 * 2.5,
                        sample.dataMask
                    ];
                }
            """
        }
        
        try:
            response = requests.post(
                f"{self.BASE_URL}process",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            logger.error(f"Sentinel Hub API error: {str(e)}")
            return None


def compare_locations(yandex_data: Dict, dgis_data: Dict) -> Dict:
    """Compare location data from different sources."""
    # This is a simplified comparison - you would need to implement
    # more sophisticated logic based on your requirements
    
    result = {
        'match_confidence': 0,
        'address_similarity': 0,
        'coordinates_distance_km': None,
        'details': {}
    }
    
    try:
        # Extract coordinates if available
        yandex_coords = extract_yandex_coordinates(yandex_data)
        dgis_coords = extract_dgis_coordinates(dgis_data)
        
        if yandex_coords and dgis_coords:
            # Calculate distance between coordinates
            distance = haversine(
                yandex_coords[1], yandex_coords[0],  # lon, lat
                dgis_coords[1], dgis_coords[0]       # lon, lat
            )
            result['coordinates_distance_km'] = distance
            
            # Higher confidence for closer points
            if distance < 0.1:  # within 100m
                result['match_confidence'] = 95
            elif distance < 1:   # within 1km
                result['match_confidence'] = 80
            elif distance < 5:   # within 5km
                result['match_confidence'] = 60
            else:
                result['match_confidence'] = 30
        
        # Compare address information if available
        yandex_address = extract_yandex_address(yandex_data)
        dgis_address = extract_dgis_address(dgis_data)
        
        if yandex_address and dgis_address:
            # Simple string similarity (you might want to use a more sophisticated method)
            similarity = calculate_similarity(yandex_address, dgis_address)
            result['address_similarity'] = similarity
            
            # Adjust confidence based on address similarity
            if similarity > 0.8:
                result['match_confidence'] = min(100, result.get('match_confidence', 0) + 20)
            elif similarity > 0.6:
                result['match_confidence'] = min(100, result.get('match_confidence', 0) + 10)
        
        return result
        
    except Exception as e:
        logger.error(f"Error comparing locations: {str(e)}")
        result['error'] = str(e)
        return result


def haversine(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    from math import radians, cos, sin, asin, sqrt
    
    # Convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    
    # Haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    
    # Radius of earth in kilometers is 6371
    km = 6371 * c
    return km


def calculate_similarity(str1: str, str2: str) -> float:
    """Calculate similarity between two strings (0 to 1)."""
    if not str1 or not str2:
        return 0.0
        
    # Convert to lowercase and split into words
    set1 = set(str1.lower().split())
    set2 = set(str2.lower().split())
    
    if not set1 and not set2:
        return 1.0
        
    # Jaccard similarity
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    
    return intersection / union if union > 0 else 0.0


# Helper functions to extract data from API responses
def extract_yandex_coordinates(data: Dict) -> Optional[Tuple[float, float]]:
    """Extract coordinates from Yandex Maps API response."""
    try:
        if 'features' in data and len(data['features']) > 0:
            coords = data['features'][0]['geometry']['coordinates']
            return (coords[1], coords[0])  # lat, lon
    except (KeyError, IndexError, TypeError):
        pass
    return None


def extract_dgis_coordinates(data: Dict) -> Optional[Tuple[float, float]]:
    """Extract coordinates from 2GIS API response."""
    try:
        if 'result' in data and 'items' in data['result'] and len(data['result']['items']) > 0:
            point = data['result']['items'][0].get('point', {})
            return (point.get('lat'), point.get('lon'))
    except (KeyError, IndexError, TypeError):
        pass
    return None


def extract_yandex_address(data: Dict) -> Optional[str]:
    """Extract address from Yandex Maps API response."""
    try:
        if 'features' in data and len(data['features']) > 0:
            return data['features'][0].get('properties', {}).get('name')
    except (KeyError, IndexError, TypeError):
        pass
    return None


def extract_dgis_address(data: Dict) -> Optional[str]:
    """Extract address from 2GIS API response."""
    try:
        if 'result' in data and 'items' in data['result'] and len(data['result']['items']) > 0:
            return data['result']['items'][0].get('full_name')
    except (KeyError, IndexError, TypeError):
        pass
    return None
