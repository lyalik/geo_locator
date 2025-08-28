import os
import logging
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from .cache_service import cached_function, MapCache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class OSMFeature:
    """Data class for OpenStreetMap feature."""
    osm_id: str
    osm_type: str  # node, way, relation
    name: str
    feature_type: str
    coordinates: Tuple[float, float]
    tags: Dict[str, str]
    address: Optional[str] = None
    bbox: Optional[List[float]] = None

@dataclass
class OSMBuilding:
    """Data class for OpenStreetMap building."""
    osm_id: str
    building_type: str
    name: Optional[str]
    address: str
    coordinates: Tuple[float, float]
    levels: Optional[int] = None
    height: Optional[float] = None
    construction_year: Optional[int] = None
    amenity: Optional[str] = None
    tags: Dict[str, str] = None

class OpenStreetMapService:
    """
    Service for integrating with OpenStreetMap APIs (Nominatim, Overpass).
    Provides enhanced mapping, geocoding, and POI data.
    """
    
    def __init__(self):
        """Initialize OpenStreetMap service."""
        self.nominatim_url = "https://nominatim.openstreetmap.org"
        self.overpass_url = "https://overpass-api.de/api"
        self.session = None
        
        # User agent for API requests (required by OSM)
        self.user_agent = "GeoLocator/1.0 (hackathon2025@example.com)"
        
        # Rate limiting
        self.request_delay = 1.0  # seconds between requests
        self.last_request_time = 0
    
    async def _get_session(self):
        """Get or create aiohttp session with proper headers."""
        if not self.session:
            headers = {
                'User-Agent': self.user_agent,
                'Accept': 'application/json'
            }
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=timeout
            )
        return self.session
    
    async def close_session(self):
        """Close aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def _rate_limit(self):
        """Implement rate limiting for API requests."""
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_delay:
            await asyncio.sleep(self.request_delay - time_since_last)
        
        self.last_request_time = asyncio.get_event_loop().time()
    
    @cached_function('osm_geocode', ttl=86400)
    async def geocode_address(self, address: str, country_code: str = 'ru') -> List[Dict[str, Any]]:
        """
        Geocode address using Nominatim API.
        
        Args:
            address: Address to geocode
            country_code: Country code for search
            
        Returns:
            List of geocoding results
        """
        try:
            await self._rate_limit()
            session = await self._get_session()
            
            params = {
                'q': address,
                'format': 'json',
                'addressdetails': 1,
                'limit': 10,
                'countrycodes': country_code,
                'extratags': 1
            }
            
            url = f"{self.nominatim_url}/search"
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_nominatim_results(data)
                else:
                    logger.warning(f"Nominatim geocoding failed: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error geocoding address: {str(e)}")
            return []
    
    @cached_function('osm_reverse_geocode', ttl=86400)
    async def reverse_geocode(self, lat: float, lon: float, zoom: int = 18) -> Optional[Dict[str, Any]]:
        """
        Reverse geocode coordinates using Nominatim API.
        
        Args:
            lat: Latitude
            lon: Longitude
            zoom: Detail level (1-18)
            
        Returns:
            Reverse geocoding result
        """
        try:
            await self._rate_limit()
            session = await self._get_session()
            
            params = {
                'lat': lat,
                'lon': lon,
                'format': 'json',
                'addressdetails': 1,
                'extratags': 1,
                'zoom': zoom
            }
            
            url = f"{self.nominatim_url}/reverse"
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_nominatim_result(data)
                else:
                    logger.warning(f"Nominatim reverse geocoding failed: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error reverse geocoding: {str(e)}")
            return None
    
    @cached_function('osm_buildings', ttl=3600)
    async def get_buildings_in_area(self, lat: float, lon: float, radius: int = 100) -> List[OSMBuilding]:
        """
        Get buildings in area using Overpass API.
        
        Args:
            lat: Center latitude
            lon: Center longitude
            radius: Search radius in meters
            
        Returns:
            List of buildings
        """
        try:
            await self._rate_limit()
            session = await self._get_session()
            
            # Create Overpass query for buildings
            overpass_query = f"""
            [out:json][timeout:25];
            (
              way["building"](around:{radius},{lat},{lon});
              relation["building"](around:{radius},{lat},{lon});
            );
            out geom;
            """
            
            url = f"{self.overpass_url}/interpreter"
            
            async with session.post(url, data=overpass_query) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_overpass_buildings(data)
                else:
                    logger.warning(f"Overpass API failed: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting buildings: {str(e)}")
            return []
    
    @cached_function('osm_amenities', ttl=3600)
    async def get_amenities_in_area(self, lat: float, lon: float, radius: int = 500, 
                                   amenity_types: List[str] = None) -> List[OSMFeature]:
        """
        Get amenities (POIs) in area using Overpass API.
        
        Args:
            lat: Center latitude
            lon: Center longitude
            radius: Search radius in meters
            amenity_types: List of amenity types to search for
            
        Returns:
            List of amenities
        """
        try:
            await self._rate_limit()
            session = await self._get_session()
            
            # Default amenity types if not specified
            if not amenity_types:
                amenity_types = [
                    'school', 'hospital', 'pharmacy', 'restaurant', 'cafe',
                    'bank', 'atm', 'fuel', 'parking', 'police', 'fire_station'
                ]
            
            # Create amenity filter
            amenity_filter = '|'.join(amenity_types)
            
            # Create Overpass query for amenities
            overpass_query = f"""
            [out:json][timeout:25];
            (
              node["amenity"~"^({amenity_filter})$"](around:{radius},{lat},{lon});
              way["amenity"~"^({amenity_filter})$"](around:{radius},{lat},{lon});
            );
            out geom;
            """
            
            url = f"{self.overpass_url}/interpreter"
            
            async with session.post(url, data=overpass_query) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_overpass_amenities(data)
                else:
                    logger.warning(f"Overpass API failed: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting amenities: {str(e)}")
            return []
    
    @cached_function('osm_roads', ttl=3600)
    async def get_roads_in_area(self, lat: float, lon: float, radius: int = 200) -> List[Dict[str, Any]]:
        """
        Get roads and streets in area using Overpass API.
        
        Args:
            lat: Center latitude
            lon: Center longitude
            radius: Search radius in meters
            
        Returns:
            List of roads
        """
        try:
            await self._rate_limit()
            session = await self._get_session()
            
            # Create Overpass query for roads
            overpass_query = f"""
            [out:json][timeout:25];
            (
              way["highway"](around:{radius},{lat},{lon});
            );
            out geom;
            """
            
            url = f"{self.overpass_url}/interpreter"
            
            async with session.post(url, data=overpass_query) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_overpass_roads(data)
                else:
                    logger.warning(f"Overpass API failed: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting roads: {str(e)}")
            return []
    
    async def search_places(self, query: str, lat: float = None, lon: float = None, 
                           radius: int = 10000) -> List[OSMFeature]:
        """
        Search for places using Nominatim API.
        
        Args:
            query: Search query
            lat: Center latitude for bounded search
            lon: Center longitude for bounded search
            radius: Search radius in meters
            
        Returns:
            List of found places
        """
        try:
            await self._rate_limit()
            session = await self._get_session()
            
            params = {
                'q': query,
                'format': 'json',
                'addressdetails': 1,
                'limit': 20,
                'extratags': 1
            }
            
            # Add bounding box if coordinates provided
            if lat is not None and lon is not None:
                # Convert radius to approximate degrees
                deg_radius = radius / 111000  # rough conversion
                params['viewbox'] = f"{lon-deg_radius},{lat+deg_radius},{lon+deg_radius},{lat-deg_radius}"
                params['bounded'] = 1
            
            url = f"{self.nominatim_url}/search"
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_nominatim_search_results(data)
                else:
                    logger.warning(f"Nominatim search failed: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error searching places: {str(e)}")
            return []
    
    async def analyze_urban_context(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Analyze urban context around coordinates.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Urban context analysis
        """
        try:
            # Get various data types
            buildings = await self.get_buildings_in_area(lat, lon, 200)
            amenities = await self.get_amenities_in_area(lat, lon, 500)
            roads = await self.get_roads_in_area(lat, lon, 300)
            address_info = await self.reverse_geocode(lat, lon)
            
            # Analyze building density
            building_density = len(buildings) / (3.14 * 0.2 * 0.2)  # buildings per km²
            
            # Categorize amenities
            amenity_categories = {}
            for amenity in amenities:
                category = amenity.tags.get('amenity', 'other')
                amenity_categories[category] = amenity_categories.get(category, 0) + 1
            
            # Analyze road types
            road_types = {}
            for road in roads:
                highway_type = road.get('tags', {}).get('highway', 'unknown')
                road_types[highway_type] = road_types.get(highway_type, 0) + 1
            
            # Determine area type
            area_type = self._classify_area_type(buildings, amenities, road_types)
            
            return {
                'coordinates': {'lat': lat, 'lon': lon},
                'address_info': address_info,
                'area_type': area_type,
                'building_count': len(buildings),
                'building_density': building_density,
                'amenity_count': len(amenities),
                'amenity_categories': amenity_categories,
                'road_count': len(roads),
                'road_types': road_types,
                'buildings': [building.__dict__ for building in buildings],
                'amenities': [amenity.__dict__ for amenity in amenities],
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing urban context: {str(e)}")
            return {
                'error': str(e),
                'coordinates': {'lat': lat, 'lon': lon}
            }
    
    def _parse_nominatim_results(self, data: List[Dict]) -> List[Dict[str, Any]]:
        """Parse Nominatim geocoding results."""
        results = []
        
        for item in data:
            result = {
                'display_name': item.get('display_name', ''),
                'lat': float(item.get('lat', 0)),
                'lon': float(item.get('lon', 0)),
                'importance': item.get('importance', 0),
                'place_id': item.get('place_id'),
                'osm_type': item.get('osm_type'),
                'osm_id': item.get('osm_id'),
                'address': item.get('address', {}),
                'bbox': item.get('boundingbox'),
                'class': item.get('class'),
                'type': item.get('type')
            }
            results.append(result)
        
        return results
    
    def _parse_nominatim_result(self, data: Dict) -> Dict[str, Any]:
        """Parse single Nominatim result."""
        return {
            'display_name': data.get('display_name', ''),
            'lat': float(data.get('lat', 0)),
            'lon': float(data.get('lon', 0)),
            'place_id': data.get('place_id'),
            'osm_type': data.get('osm_type'),
            'osm_id': data.get('osm_id'),
            'address': data.get('address', {}),
            'class': data.get('class'),
            'type': data.get('type')
        }
    
    def _parse_nominatim_search_results(self, data: List[Dict]) -> List[OSMFeature]:
        """Parse Nominatim search results to OSMFeature objects."""
        features = []
        
        for item in data:
            try:
                feature = OSMFeature(
                    osm_id=str(item.get('osm_id', '')),
                    osm_type=item.get('osm_type', ''),
                    name=item.get('display_name', ''),
                    feature_type=item.get('type', ''),
                    coordinates=(float(item.get('lat', 0)), float(item.get('lon', 0))),
                    tags=item.get('extratags', {}),
                    address=item.get('display_name', ''),
                    bbox=item.get('boundingbox')
                )
                features.append(feature)
            except Exception as e:
                logger.warning(f"Error parsing search result: {str(e)}")
        
        return features
    
    def _parse_overpass_buildings(self, data: Dict) -> List[OSMBuilding]:
        """Parse Overpass API building results."""
        buildings = []
        
        for element in data.get('elements', []):
            try:
                tags = element.get('tags', {})
                
                # Get coordinates (center point for ways/relations)
                if element.get('type') == 'node':
                    coords = (element.get('lat', 0), element.get('lon', 0))
                else:
                    # Calculate centroid for ways
                    geometry = element.get('geometry', [])
                    if geometry:
                        lats = [point.get('lat', 0) for point in geometry]
                        lons = [point.get('lon', 0) for point in geometry]
                        coords = (sum(lats) / len(lats), sum(lons) / len(lons))
                    else:
                        continue
                
                building = OSMBuilding(
                    osm_id=str(element.get('id', '')),
                    building_type=tags.get('building', 'yes'),
                    name=tags.get('name'),
                    address=self._format_address_from_tags(tags),
                    coordinates=coords,
                    levels=self._safe_int(tags.get('building:levels')),
                    height=self._safe_float(tags.get('height')),
                    construction_year=self._safe_int(tags.get('start_date')),
                    amenity=tags.get('amenity'),
                    tags=tags
                )
                buildings.append(building)
                
            except Exception as e:
                logger.warning(f"Error parsing building: {str(e)}")
        
        return buildings
    
    def _parse_overpass_amenities(self, data: Dict) -> List[OSMFeature]:
        """Parse Overpass API amenity results."""
        amenities = []
        
        for element in data.get('elements', []):
            try:
                tags = element.get('tags', {})
                
                # Get coordinates
                if element.get('type') == 'node':
                    coords = (element.get('lat', 0), element.get('lon', 0))
                else:
                    # Calculate centroid for ways
                    geometry = element.get('geometry', [])
                    if geometry:
                        lats = [point.get('lat', 0) for point in geometry]
                        lons = [point.get('lon', 0) for point in geometry]
                        coords = (sum(lats) / len(lats), sum(lons) / len(lons))
                    else:
                        continue
                
                amenity = OSMFeature(
                    osm_id=str(element.get('id', '')),
                    osm_type=element.get('type', ''),
                    name=tags.get('name', tags.get('amenity', 'Unknown')),
                    feature_type=tags.get('amenity', ''),
                    coordinates=coords,
                    tags=tags,
                    address=self._format_address_from_tags(tags)
                )
                amenities.append(amenity)
                
            except Exception as e:
                logger.warning(f"Error parsing amenity: {str(e)}")
        
        return amenities
    
    def _parse_overpass_roads(self, data: Dict) -> List[Dict[str, Any]]:
        """Parse Overpass API road results."""
        roads = []
        
        for element in data.get('elements', []):
            try:
                tags = element.get('tags', {})
                geometry = element.get('geometry', [])
                
                road = {
                    'osm_id': str(element.get('id', '')),
                    'name': tags.get('name', ''),
                    'highway_type': tags.get('highway', ''),
                    'surface': tags.get('surface', ''),
                    'maxspeed': tags.get('maxspeed', ''),
                    'lanes': self._safe_int(tags.get('lanes')),
                    'geometry': geometry,
                    'tags': tags
                }
                roads.append(road)
                
            except Exception as e:
                logger.warning(f"Error parsing road: {str(e)}")
        
        return roads
    
    def _classify_area_type(self, buildings: List[OSMBuilding], amenities: List[OSMFeature], 
                           road_types: Dict[str, int]) -> str:
        """Classify area type based on features."""
        # Count building types
        residential_count = sum(1 for b in buildings if 'residential' in b.building_type.lower() or b.building_type == 'house')
        commercial_count = sum(1 for b in buildings if 'commercial' in b.building_type.lower() or b.building_type in ['retail', 'office'])
        
        # Count amenity types
        commercial_amenities = sum(1 for a in amenities if a.feature_type in ['restaurant', 'cafe', 'shop', 'bank'])
        public_amenities = sum(1 for a in amenities if a.feature_type in ['school', 'hospital', 'library'])
        
        # Analyze road types
        major_roads = road_types.get('primary', 0) + road_types.get('secondary', 0) + road_types.get('trunk', 0)
        residential_roads = road_types.get('residential', 0)
        
        # Classification logic
        if commercial_count > residential_count and commercial_amenities > 2:
            return 'commercial'
        elif residential_count > commercial_count and residential_roads > major_roads:
            return 'residential'
        elif public_amenities > 2:
            return 'institutional'
        elif major_roads > residential_roads:
            return 'transport_hub'
        else:
            return 'mixed_use'
    
    def _format_address_from_tags(self, tags: Dict[str, str]) -> str:
        """Format address from OSM tags."""
        address_parts = []
        
        if 'addr:housenumber' in tags:
            address_parts.append(tags['addr:housenumber'])
        if 'addr:street' in tags:
            address_parts.append(tags['addr:street'])
        if 'addr:city' in tags:
            address_parts.append(tags['addr:city'])
        
        return ', '.join(address_parts) if address_parts else ''
    
    def _safe_int(self, value: str) -> Optional[int]:
        """Safely convert string to int."""
        if not value:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
    
    def _safe_float(self, value: str) -> Optional[float]:
        """Safely convert string to float."""
        if not value:
            return None
        try:
            # Handle height values like "15 m"
            if isinstance(value, str):
                value = value.split()[0]  # Take first part
            return float(value)
        except (ValueError, TypeError):
            return None

# Synchronous wrapper functions for Flask integration
def sync_geocode_address(address: str, country_code: str = 'ru') -> List[Dict[str, Any]]:
    """Synchronous wrapper for address geocoding."""
    service = OpenStreetMapService()
    try:
        return asyncio.run(service.geocode_address(address, country_code))
    finally:
        asyncio.run(service.close_session())

def sync_reverse_geocode(lat: float, lon: float, zoom: int = 18) -> Optional[Dict[str, Any]]:
    """Synchronous wrapper for reverse geocoding."""
    service = OpenStreetMapService()
    try:
        return asyncio.run(service.reverse_geocode(lat, lon, zoom))
    finally:
        asyncio.run(service.close_session())

def sync_get_buildings_in_area(lat: float, lon: float, radius: int = 100) -> List[OSMBuilding]:
    """Synchronous wrapper for getting buildings."""
    service = OpenStreetMapService()
    try:
        return asyncio.run(service.get_buildings_in_area(lat, lon, radius))
    finally:
        asyncio.run(service.close_session())

def sync_analyze_urban_context(lat: float, lon: float) -> Dict[str, Any]:
    """Synchronous wrapper for urban context analysis."""
    service = OpenStreetMapService()
    try:
        return asyncio.run(service.analyze_urban_context(lat, lon))
    finally:
        asyncio.run(service.close_session())

def sync_search_places(query: str, lat: float = None, lon: float = None, radius: int = 10000) -> List[OSMFeature]:
    """Synchronous wrapper for place search."""
    service = OpenStreetMapService()
    try:
        return asyncio.run(service.search_places(query, lat, lon, radius))
    finally:
        asyncio.run(service.close_session())
