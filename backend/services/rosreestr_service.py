import os
import logging
import requests
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json
from .cache_service import cached_function, MapCache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PropertyInfo:
    """Data class for property information from Rosreestr."""
    cadastral_number: str
    address: str
    area: float
    category: str
    permitted_use: str
    owner_type: str
    registration_date: str
    cost: Optional[float] = None
    coordinates: Optional[Tuple[float, float]] = None
    building_year: Optional[int] = None
    floors: Optional[int] = None
    material: Optional[str] = None

class RosreestrService:
    """
    Service for integrating with Rosreestr (Russian Federal Service for State Registration) API.
    Provides property information, cadastral data, and ownership details.
    """
    
    def __init__(self):
        """Initialize Rosreestr service with API configuration."""
        self.base_url = "https://rosreestr.gov.ru/api/online"
        self.public_map_url = "https://pkk.rosreestr.ru/api"
        self.session = None
        
        # API endpoints
        self.endpoints = {
            'search_by_address': '/address/fir_objects',
            'search_by_cadastral': '/fir_object',
            'get_coordinates': '/features',
            'get_property_info': '/property',
            'get_ownership_info': '/ownership'
        }
    
    async def _get_session(self):
        """Get or create aiohttp session."""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def close_session(self):
        """Close aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None
    
    @cached_function('rosreestr_address', ttl=86400)  # Cache for 24 hours
    async def search_by_address(self, address: str) -> List[Dict[str, Any]]:
        """
        Search properties by address.
        
        Args:
            address: Property address to search
            
        Returns:
            List of property records
        """
        try:
            session = await self._get_session()
            
            # Use public PKK API for address search
            url = f"{self.public_map_url}/features/1"
            params = {
                'text': address,
                'limit': 20,
                'tolerance': 4
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_search_results(data)
                else:
                    logger.warning(f"Rosreestr API error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error searching by address: {str(e)}")
            return []
    
    @cached_function('rosreestr_cadastral', ttl=86400)
    async def get_property_by_cadastral_number(self, cadastral_number: str) -> Optional[PropertyInfo]:
        """
        Get property information by cadastral number.
        
        Args:
            cadastral_number: Cadastral number (e.g., "77:01:0001001:1234")
            
        Returns:
            PropertyInfo object or None
        """
        try:
            session = await self._get_session()
            
            # Use public PKK API
            url = f"{self.public_map_url}/features/1/{cadastral_number}"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_property_info(data, cadastral_number)
                else:
                    logger.warning(f"Property not found: {cadastral_number}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting property info: {str(e)}")
            return None
    
    @cached_function('rosreestr_coordinates', ttl=86400)
    async def get_properties_by_coordinates(self, lat: float, lon: float, radius: int = 100) -> List[PropertyInfo]:
        """
        Get properties within radius of coordinates.
        
        Args:
            lat: Latitude
            lon: Longitude
            radius: Search radius in meters
            
        Returns:
            List of PropertyInfo objects
        """
        try:
            session = await self._get_session()
            
            # Convert to Web Mercator projection (approximate)
            x = lon * 20037508.34 / 180
            y = lat * 20037508.34 / 180
            
            # Create bounding box
            buffer = radius * 0.00001  # Approximate conversion
            bbox = f"{x-buffer},{y-buffer},{x+buffer},{y+buffer}"
            
            url = f"{self.public_map_url}/features/1"
            params = {
                'bbox': bbox,
                'limit': 50
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    properties = []
                    
                    for feature in data.get('features', []):
                        prop_info = self._parse_feature_to_property(feature)
                        if prop_info:
                            properties.append(prop_info)
                    
                    return properties
                else:
                    logger.warning(f"Coordinate search failed: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error searching by coordinates: {str(e)}")
            return []
    
    async def validate_property_usage(self, cadastral_number: str, current_usage: str) -> Dict[str, Any]:
        """
        Validate if current property usage matches permitted usage.
        
        Args:
            cadastral_number: Property cadastral number
            current_usage: Current observed usage
            
        Returns:
            Validation result with compliance status
        """
        try:
            property_info = await self.get_property_by_cadastral_number(cadastral_number)
            
            if not property_info:
                return {
                    'valid': False,
                    'error': 'Property not found',
                    'compliance': 'unknown'
                }
            
            # Define usage mappings
            usage_mappings = {
                'residential': ['жилая', 'многоквартирный дом', 'индивидуальное жилищное строительство'],
                'commercial': ['торговля', 'офис', 'коммерческая', 'предпринимательство'],
                'industrial': ['производство', 'промышленность', 'склад'],
                'public': ['образование', 'здравоохранение', 'культура', 'спорт']
            }
            
            permitted_use = property_info.permitted_use.lower()
            current_usage_lower = current_usage.lower()
            
            # Check compliance
            is_compliant = False
            for usage_type, keywords in usage_mappings.items():
                if any(keyword in permitted_use for keyword in keywords):
                    if usage_type in current_usage_lower:
                        is_compliant = True
                        break
            
            return {
                'valid': True,
                'property_info': property_info.__dict__,
                'permitted_use': property_info.permitted_use,
                'current_usage': current_usage,
                'compliance': 'compliant' if is_compliant else 'violation',
                'violation_type': 'usage_mismatch' if not is_compliant else None
            }
            
        except Exception as e:
            logger.error(f"Error validating property usage: {str(e)}")
            return {
                'valid': False,
                'error': str(e),
                'compliance': 'unknown'
            }
    
    def _parse_search_results(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse search results from PKK API."""
        results = []
        
        for feature in data.get('features', []):
            attrs = feature.get('attrs', {})
            geometry = feature.get('geometry', {})
            
            result = {
                'cadastral_number': attrs.get('cn', ''),
                'address': attrs.get('address', ''),
                'area': attrs.get('area_value', 0),
                'category': attrs.get('category_type', ''),
                'coordinates': self._extract_coordinates(geometry)
            }
            
            if result['cadastral_number']:
                results.append(result)
        
        return results
    
    def _parse_property_info(self, data: Dict[str, Any], cadastral_number: str) -> Optional[PropertyInfo]:
        """Parse property information from API response."""
        try:
            feature = data.get('feature', {})
            attrs = feature.get('attrs', {})
            
            return PropertyInfo(
                cadastral_number=cadastral_number,
                address=attrs.get('address', ''),
                area=float(attrs.get('area_value', 0)),
                category=attrs.get('category_type', ''),
                permitted_use=attrs.get('util_by_doc', 'Не определено'),
                owner_type=attrs.get('form_of_ownership', ''),
                registration_date=attrs.get('date_create', ''),
                cost=attrs.get('cad_cost'),
                coordinates=self._extract_coordinates(feature.get('geometry', {})),
                building_year=attrs.get('year_built'),
                floors=attrs.get('floors'),
                material=attrs.get('material')
            )
            
        except Exception as e:
            logger.error(f"Error parsing property info: {str(e)}")
            return None
    
    def _parse_feature_to_property(self, feature: Dict[str, Any]) -> Optional[PropertyInfo]:
        """Convert feature to PropertyInfo object."""
        try:
            attrs = feature.get('attrs', {})
            cadastral_number = attrs.get('cn', '')
            
            if not cadastral_number:
                return None
            
            return PropertyInfo(
                cadastral_number=cadastral_number,
                address=attrs.get('address', ''),
                area=float(attrs.get('area_value', 0)),
                category=attrs.get('category_type', ''),
                permitted_use=attrs.get('util_by_doc', 'Не определено'),
                owner_type=attrs.get('form_of_ownership', ''),
                registration_date=attrs.get('date_create', ''),
                coordinates=self._extract_coordinates(feature.get('geometry', {}))
            )
            
        except Exception as e:
            logger.error(f"Error parsing feature: {str(e)}")
            return None
    
    def _extract_coordinates(self, geometry: Dict[str, Any]) -> Optional[Tuple[float, float]]:
        """Extract coordinates from geometry object."""
        try:
            if geometry.get('type') == 'Point':
                coords = geometry.get('coordinates', [])
                if len(coords) >= 2:
                    return (coords[1], coords[0])  # lat, lon
            elif geometry.get('type') in ['Polygon', 'MultiPolygon']:
                # Get centroid of polygon
                coords = geometry.get('coordinates', [])
                if coords:
                    # Simplified centroid calculation
                    if geometry.get('type') == 'Polygon':
                        ring = coords[0]
                    else:
                        ring = coords[0][0]
                    
                    if ring:
                        avg_lon = sum(point[0] for point in ring) / len(ring)
                        avg_lat = sum(point[1] for point in ring) / len(ring)
                        return (avg_lat, avg_lon)
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting coordinates: {str(e)}")
            return None
    
    async def get_property_violations(self, lat: float, lon: float, violation_types: List[str]) -> List[Dict[str, Any]]:
        """
        Check for property violations in the area.
        
        Args:
            lat: Latitude
            lon: Longitude
            violation_types: Types of violations to check
            
        Returns:
            List of potential violations
        """
        try:
            properties = await self.get_properties_by_coordinates(lat, lon, radius=50)
            violations = []
            
            for prop in properties:
                # Check for common violations
                violation_checks = {
                    'unauthorized_construction': self._check_unauthorized_construction,
                    'usage_violation': self._check_usage_violation,
                    'boundary_violation': self._check_boundary_violation
                }
                
                for violation_type in violation_types:
                    if violation_type in violation_checks:
                        check_result = violation_checks[violation_type](prop)
                        if check_result['has_violation']:
                            violations.append({
                                'property': prop.__dict__,
                                'violation_type': violation_type,
                                'details': check_result['details'],
                                'severity': check_result.get('severity', 'medium')
                            })
            
            return violations
            
        except Exception as e:
            logger.error(f"Error checking violations: {str(e)}")
            return []
    
    def _check_unauthorized_construction(self, property_info: PropertyInfo) -> Dict[str, Any]:
        """Check for unauthorized construction indicators."""
        # Simplified check - in real implementation would compare with construction permits
        has_violation = False
        details = []
        
        # Check if building year is missing (potential unauthorized construction)
        if not property_info.building_year and property_info.category == 'building':
            has_violation = True
            details.append("Отсутствует информация о годе постройки")
        
        # Check for unusual area values
        if property_info.area > 10000:  # Very large area might indicate issues
            has_violation = True
            details.append("Необычно большая площадь объекта")
        
        return {
            'has_violation': has_violation,
            'details': details,
            'severity': 'high' if has_violation else 'low'
        }
    
    def _check_usage_violation(self, property_info: PropertyInfo) -> Dict[str, Any]:
        """Check for property usage violations."""
        has_violation = False
        details = []
        
        # Check for residential properties with commercial indicators
        if 'жилая' in property_info.permitted_use.lower():
            if any(word in property_info.address.lower() for word in ['магазин', 'офис', 'салон']):
                has_violation = True
                details.append("Возможное коммерческое использование жилого помещения")
        
        return {
            'has_violation': has_violation,
            'details': details,
            'severity': 'medium' if has_violation else 'low'
        }
    
    def _check_boundary_violation(self, property_info: PropertyInfo) -> Dict[str, Any]:
        """Check for boundary violations."""
        # Simplified check - would require more complex spatial analysis
        has_violation = False
        details = []
        
        # This would typically involve comparing actual boundaries with registered ones
        # For now, just a placeholder
        
        return {
            'has_violation': has_violation,
            'details': details,
            'severity': 'low'
        }

# Synchronous wrapper functions for Flask integration
def sync_search_by_address(address: str) -> List[Dict[str, Any]]:
    """Synchronous wrapper for address search."""
    service = RosreestrService()
    try:
        return asyncio.run(service.search_by_address(address))
    finally:
        asyncio.run(service.close_session())

def sync_get_property_by_cadastral_number(cadastral_number: str) -> Optional[PropertyInfo]:
    """Synchronous wrapper for cadastral number search."""
    service = RosreestrService()
    try:
        return asyncio.run(service.get_property_by_cadastral_number(cadastral_number))
    finally:
        asyncio.run(service.close_session())

def sync_validate_property_usage(cadastral_number: str, current_usage: str) -> Dict[str, Any]:
    """Synchronous wrapper for property usage validation."""
    service = RosreestrService()
    try:
        return asyncio.run(service.validate_property_usage(cadastral_number, current_usage))
    finally:
        asyncio.run(service.close_session())

def sync_get_properties_by_coordinates(lat: float, lon: float, radius: int = 100) -> List[PropertyInfo]:
    """Synchronous wrapper for coordinate-based search."""
    service = RosreestrService()
    try:
        return asyncio.run(service.get_properties_by_coordinates(lat, lon, radius))
    finally:
        asyncio.run(service.close_session())
