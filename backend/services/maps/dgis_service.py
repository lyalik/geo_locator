import os
import aiohttp
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class DGisService:
    """Service for interacting with 2GIS API"""
    
    BASE_URL = "https://catalog.api.2gis.com/3.0/items"
    GEOCODE_URL = "https://catalog.api.2gis.com/3.0/geo/geocode"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def search_places(self, query: str, lat: float, lon: float, radius: int = 500) -> Dict:
        """Search for places using 2GIS API"""
        params = {
            'q': query,
            'point': f'{lon},{lat}',
            'radius': radius,
            'fields': 'items.point,items.geometry.centroid,items.address',
            'key': self.api_key
        }
        
        session = await self._get_session()
        try:
            async with session.get(self.BASE_URL, params=params) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            logger.error(f"2GIS API error: {e}")
            return {'error': str(e)}
    
    async def reverse_geocode(self, lat: float, lon: float) -> Dict:
        """Get address from coordinates using 2GIS API"""
        params = {
            'point': f'{lon},{lat}',
            'fields': 'items.point,items.geometry.centroid,items.address',
            'key': self.api_key
        }
        
        session = await self._get_session()
        try:
            async with session.get(self.GEOCODE_URL, params=params) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            logger.error(f"2GIS Geocode API error: {e}")
            return {'error': str(e)}

# Singleton instance
dgis_service = DGisService(api_key=os.getenv('DGIS_API_KEY', ''))
