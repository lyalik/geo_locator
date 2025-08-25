from .yandex_service import yandex_service
from .dgis_service import dgis_service
from typing import Dict, List, Any, Optional
import asyncio
import logging

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
    
    def _aggregate_geocode_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate reverse geocoding results"""
        if not results:
            return {'error': 'No geocode results from any provider'}
        
        # Return the first successful result
        for provider, result in results.items():
            if 'response' in result.get('GeoObjectCollection', {}):
                return {
                    'provider': provider,
                    'result': result
                }
            elif 'result' in result and 'items' in result['result'] and result['result']['items']:
                return {
                    'provider': provider,
                    'result': result['result']['items'][0]
                }
        
        return {'error': 'No valid geocode results found'}

# Singleton instance
map_aggregator = MapAggregator()
