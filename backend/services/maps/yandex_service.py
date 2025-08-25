import os
import aiohttp
import asyncio
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class YandexMapsService:
    """Service for interacting with Yandex Maps API"""
    
    BASE_URL = "https://search-maps.yandex.ru/v1/"
    GEOCODE_URL = "https://geocode-maps.yandex.ru/1.x/"
    STATIC_MAPS_URL = "https://static-maps.yandex.ru/1.x/"  # For satellite imagery
    
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
        """Search for places using Yandex Maps API"""
        params = {
            'apikey': self.api_key,
            'text': query,
            'll': f'{lon},{lat}',
            'spn': '0.05,0.05',
            'type': 'biz',
            'results': 10,
            'lang': 'ru_RU',
            'format': 'json'
        }
        
        session = await self._get_session()
        try:
            async with session.get(self.BASE_URL, params=params) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            logger.error(f"Yandex Maps API error: {e}")
            return {'error': str(e)}
    
    async def get_satellite_image(self, lat: float, lon: float, zoom: int = 17, width: int = 600, height: int = 400) -> bytes:
        """Get satellite image for given coordinates"""
        params = {
            'll': f'{lon},{lat}',
            'z': zoom,
            'l': 'sat',  # Satellite layer
            'size': f'{width},{height}',
            'pt': f'{lon},{lat},pm2rdl',  # Add marker at the center
            'lang': 'ru_RU'
        }
        
        session = await self._get_session()
        try:
            async with session.get(self.STATIC_MAPS_URL, params=params) as response:
                response.raise_for_status()
                return await response.read()
        except Exception as e:
            logger.error(f"Yandex Static Maps API error: {e}")
            return None

    async def reverse_geocode(self, lat: float, lon: float) -> Dict:
        """Get address from coordinates"""
        params = {
            'apikey': self.api_key,
            'geocode': f'{lon},{lat}',
            'format': 'json',
            'results': 1,
            'lang': 'ru_RU'
        }
        
        session = await self._get_session()
        try:
            async with session.get(self.GEOCODE_URL, params=params) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            logger.error(f"Yandex Geocode API error: {e}")
            return {'error': str(e)}

# Singleton instance
yandex_service = YandexMapsService(api_key=os.getenv('YANDEX_API_KEY', ''))
