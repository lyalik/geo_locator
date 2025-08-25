from .yandex_service import yandex_service
from .dgis_service import dgis_service
from typing import Dict, List, Any, Optional, Tuple
import asyncio
import logging
import io
from PIL import Image
import numpy as np
from io import BytesIO

logger = logging.getLogger(__name__)

class MapAggregator:
    """Aggregates data from multiple map providers"""
    
    def __init__(self):
        self.providers = {
            'yandex': yandex_service,
            'dgis': dgis_service
        }
    
    async def search_places(self, query: str, lat: float, lon: float, radius: int = 500) -> Dict[str, Any]:
        """Search places across all available providers"""
        tasks = []
        
        # Create tasks for all providers
        for provider_name, provider in self.providers.items():
            task = asyncio.create_task(
                self._safe_provider_call(
                    provider.search_places,
                    query, lat, lon, radius
                )
            )
            tasks.append((provider_name, task))
        
        # Wait for all tasks to complete
        results = {}
        for provider_name, task in tasks:
            try:
                result = await task
                if result and not result.get('error'):
                    results[provider_name] = result
            except Exception as e:
                logger.error(f"Error in {provider_name} search: {e}")
        
        return self._aggregate_results(results, query)
    
    async def reverse_geocode(self, lat: float, lon: float) -> Dict[str, Any]:
        """Get address from coordinates using all available providers"""
        tasks = []
        
        for provider_name, provider in self.providers.items():
            task = asyncio.create_task(
                self._safe_provider_call(
                    provider.reverse_geocode,
                    lat, lon
                )
            )
            tasks.append((provider_name, task))
        
        results = {}
        for provider_name, task in tasks:
            try:
                result = await task
                if result and not result.get('error'):
                    results[provider_name] = result
            except Exception as e:
                logger.error(f"Error in {provider_name} reverse geocode: {e}")
        
        return self._aggregate_geocode_results(results)
    
    async def _safe_provider_call(self, func, *args, **kwargs):
        """Safely call provider function with error handling"""
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Provider call failed: {e}")
            return {'error': str(e)}
    
    def _aggregate_results(self, results: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Aggregate results from multiple providers"""
        if not results:
            return {'error': 'No results from any provider'}
        
        # Simple aggregation - you can enhance this based on your needs
        aggregated = {
            'query': query,
            'providers': list(results.keys()),
            'results': {},
            'count': 0
        }
        
        # Count results from each provider
        for provider, result in results.items():
            if 'features' in result:
                aggregated['results'][provider] = len(result['features'])
            elif 'items' in result.get('result', {}):
                aggregated['results'][provider] = len(result['result']['items'])
            
            # Update total count
            if 'count' in result.get('result', {}):
                aggregated['count'] += result['result']['count']
        
        return aggregated
    
    async def get_satellite_image(self, lat: float, lon: float, zoom: int = 17, width: int = 600, height: int = 400) -> Dict[str, Any]:
        """Get satellite image from all available providers and combine them"""
        tasks = []
        
        # Create tasks for all providers that support satellite imagery
        if hasattr(yandex_service, 'get_satellite_image'):
            task = asyncio.create_task(
                self._safe_provider_call(
                    yandex_service.get_satellite_image,
                    lat, lon, zoom, width, height
                )
            )
            tasks.append(('yandex', task))
            
        if hasattr(dgis_service, 'get_satellite_image'):
            task = asyncio.create_task(
                self._safe_provider_call(
                    dgis_service.get_satellite_image,
                    lat, lon, zoom, width, height
                )
            )
            tasks.append(('dgis', task))
        
        # Wait for all tasks to complete
        images = {}
        for provider_name, task in tasks:
            try:
                image_data = await task
                if image_data:
                    images[provider_name] = image_data
            except Exception as e:
                logger.error(f"Error getting satellite image from {provider_name}: {e}")
        
        # If we have multiple images, we can combine them or return the first one
        if not images:
            return {'error': 'No satellite images available from any provider'}
        
        # For now, return the first available image
        provider, image_data = next(iter(images.items()))
        return {
            'provider': provider,
            'image': image_data,
            'content_type': 'image/jpeg',
            'lat': lat,
            'lon': lon,
            'zoom': zoom
        }
    
    def _combine_satellite_images(self, images: Dict[str, bytes]) -> bytes:
        """Combine multiple satellite images for better coverage/quality"""
        if not images:
            return None
            
        try:
            # Convert all images to PIL format
            pil_images = []
            for img_data in images.values():
                img = Image.open(io.BytesIO(img_data))
                pil_images.append(img.convert('RGB'))
            
            # Simple averaging of images
            if len(pil_images) == 1:
                return pil_images[0]
                
            # If we have multiple images, average them
            arrays = [np.array(img) for img in pil_images]
            avg_array = np.mean(arrays, axis=0).astype(np.uint8)
            
            # Convert back to bytes
            result = Image.fromarray(avg_array)
            img_byte_arr = BytesIO()
            result.save(img_byte_arr, format='JPEG')
            return img_byte_arr.getvalue()
            
        except Exception as e:
            logger.error(f"Error combining satellite images: {e}")
            return None

    def _aggregate_geocode_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate reverse geocoding results"""
        if not results:
            return {'error': 'No geocode results from any provider'}
        
        # Try to find the most detailed result
        best_result = None
        best_provider = None
        max_score = -1
        
        for provider, result in results.items():
            score = 0
            
            # Yandex format
            if 'response' in result.get('GeoObjectCollection', {}):
                score = len(result['GeoObjectCollection'].get('featureMember', []))
                if score > max_score:
                    max_score = score
                    best_result = result
                    best_provider = provider
            
            # 2GIS format
            elif 'result' in result and 'items' in result['result']:
                score = len(result['result']['items'])
                if score > max_score:
                    max_score = score
                    best_result = result['result']['items'][0] if result['result']['items'] else {}
                    best_provider = provider
        
        if best_result is None:
            return {'error': 'No valid geocode results found'}
            
        return {
            'provider': best_provider,
            'result': best_result,
            'all_providers': list(results.keys())
        }

# Singleton instance
map_aggregator = MapAggregator()
