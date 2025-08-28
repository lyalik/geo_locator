"""
Sentinel Hub Service for satellite imagery integration
Provides access to Sentinel-2 satellite imagery and analysis capabilities
"""

import os
import asyncio
import aiohttp
import json
import base64
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from .cache_service import CacheService

logger = logging.getLogger(__name__)

@dataclass
class SatelliteImage:
    """Satellite image data structure"""
    image_url: str
    acquisition_date: str
    cloud_coverage: float
    bbox: List[float]
    resolution: int
    bands: List[str]
    metadata: Dict[str, Any]

@dataclass
class ImageAnalysis:
    """Satellite image analysis results"""
    vegetation_index: float
    built_up_area: float
    water_bodies: float
    bare_soil: float
    cloud_coverage: float
    change_detection: Optional[Dict[str, Any]] = None

class SentinelHubService:
    """Service for Sentinel Hub satellite imagery integration"""
    
    def __init__(self):
        self.cache_service = CacheService()
        self.base_url = "https://services.sentinel-hub.com"
        self.oauth_url = "https://services.sentinel-hub.com/oauth/token"
        self.process_url = "https://services.sentinel-hub.com/api/v1/process"
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests
        
        # Authentication (will need to be configured)
        self.client_id = None
        self.client_secret = None
        self.access_token = None
        self.token_expires_at = None
    
    def configure_credentials(self, client_id: str, client_secret: str):
        """Configure Sentinel Hub credentials"""
        self.client_id = client_id
        self.client_secret = client_secret
    
    async def _ensure_rate_limit(self):
        """Ensure rate limiting compliance"""
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval - time_since_last)
        self.last_request_time = asyncio.get_event_loop().time()
    
    async def _get_access_token(self) -> str:
        """Get or refresh access token"""
        if (self.access_token and self.token_expires_at and 
            datetime.now().timestamp() < self.token_expires_at):
            return self.access_token
        
        if not self.client_id or not self.client_secret:
            raise ValueError("Sentinel Hub credentials not configured")
        
        await self._ensure_rate_limit()
        
        async with aiohttp.ClientSession() as session:
            data = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
            
            try:
                async with session.post(self.oauth_url, data=data) as response:
                    if response.status == 200:
                        token_data = await response.json()
                        self.access_token = token_data['access_token']
                        expires_in = token_data.get('expires_in', 3600)
                        self.token_expires_at = datetime.now().timestamp() + expires_in - 60
                        return self.access_token
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to get access token: {response.status} - {error_text}")
                        raise Exception(f"Authentication failed: {response.status}")
            except Exception as e:
                logger.error(f"Error getting access token: {e}")
                raise
    
    async def get_satellite_image(
        self, 
        bbox: List[float], 
        date_from: str, 
        date_to: str,
        resolution: int = 10,
        max_cloud_coverage: float = 20.0,
        bands: List[str] = None
    ) -> Optional[SatelliteImage]:
        """
        Get satellite image for specified area and time period
        
        Args:
            bbox: Bounding box [min_lon, min_lat, max_lon, max_lat]
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
            resolution: Image resolution in meters
            max_cloud_coverage: Maximum cloud coverage percentage
            bands: List of bands to include
        """
        cache_key = f"sentinel_image:{':'.join(map(str, bbox))}:{date_from}:{date_to}:{resolution}"
        
        # Check cache first
        cached_result = await self.cache_service.get(cache_key)
        if cached_result:
            return SatelliteImage(**cached_result)
        
        if bands is None:
            bands = ["B02", "B03", "B04", "B08"]  # Blue, Green, Red, NIR
        
        try:
            access_token = await self._get_access_token()
            await self._ensure_rate_limit()
            
            # Construct request payload
            payload = {
                "input": {
                    "bounds": {
                        "bbox": bbox,
                        "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"}
                    },
                    "data": [{
                        "type": "sentinel-2-l2a",
                        "dataFilter": {
                            "timeRange": {
                                "from": f"{date_from}T00:00:00Z",
                                "to": f"{date_to}T23:59:59Z"
                            },
                            "maxCloudCoverage": max_cloud_coverage
                        }
                    }]
                },
                "output": {
                    "width": 512,
                    "height": 512,
                    "responses": [{
                        "identifier": "default",
                        "format": {"type": "image/png"}
                    }]
                },
                "evalscript": self._get_evalscript(bands)
            }
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.process_url, 
                    json=payload, 
                    headers=headers
                ) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        image_url = f"data:image/png;base64,{base64.b64encode(image_data).decode()}"
                        
                        # Get metadata from headers if available
                        metadata = {
                            'content_type': response.headers.get('content-type', ''),
                            'content_length': response.headers.get('content-length', ''),
                            'processing_time': response.headers.get('x-processing-time', '')
                        }
                        
                        satellite_image = SatelliteImage(
                            image_url=image_url,
                            acquisition_date=date_to,  # Use end date as acquisition
                            cloud_coverage=max_cloud_coverage,  # Approximation
                            bbox=bbox,
                            resolution=resolution,
                            bands=bands,
                            metadata=metadata
                        )
                        
                        # Cache the result
                        await self.cache_service.set(
                            cache_key, 
                            satellite_image.__dict__, 
                            ttl=3600  # 1 hour
                        )
                        
                        return satellite_image
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to get satellite image: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error getting satellite image: {e}")
            return None
    
    def _get_evalscript(self, bands: List[str]) -> str:
        """Generate evalscript for Sentinel Hub processing"""
        band_mapping = {
            "B02": "B02",  # Blue
            "B03": "B03",  # Green
            "B04": "B04",  # Red
            "B08": "B08",  # NIR
            "B11": "B11",  # SWIR1
            "B12": "B12"   # SWIR2
        }
        
        # True color RGB evalscript
        if set(bands) >= {"B02", "B03", "B04"}:
            return """
            //VERSION=3
            function setup() {
                return {
                    input: ["B02", "B03", "B04"],
                    output: { bands: 3 }
                };
            }
            
            function evaluatePixel(sample) {
                return [sample.B04 * 2.5, sample.B03 * 2.5, sample.B02 * 2.5];
            }
            """
        
        # Default evalscript for any bands
        band_inputs = ', '.join([f'"{band}"' for band in bands if band in band_mapping])
        return f"""
        //VERSION=3
        function setup() {{
            return {{
                input: [{band_inputs}],
                output: {{ bands: {len(bands)} }}
            }};
        }}
        
        function evaluatePixel(sample) {{
            return [{', '.join([f'sample.{band}' for band in bands if band in band_mapping])}];
        }}
        """
    
    async def analyze_satellite_image(
        self, 
        bbox: List[float], 
        date_from: str, 
        date_to: str
    ) -> Optional[ImageAnalysis]:
        """
        Analyze satellite image for vegetation, built-up areas, etc.
        """
        cache_key = f"sentinel_analysis:{':'.join(map(str, bbox))}:{date_from}:{date_to}"
        
        # Check cache first
        cached_result = await self.cache_service.get(cache_key)
        if cached_result:
            return ImageAnalysis(**cached_result)
        
        try:
            access_token = await self._get_access_token()
            await self._ensure_rate_limit()
            
            # NDVI and built-up analysis evalscript
            evalscript = """
            //VERSION=3
            function setup() {
                return {
                    input: ["B02", "B03", "B04", "B08", "B11", "SCL"],
                    output: { bands: 4 }
                };
            }
            
            function evaluatePixel(sample) {
                // NDVI calculation
                let ndvi = (sample.B08 - sample.B04) / (sample.B08 + sample.B04);
                
                // Built-up index (simplified)
                let builtUp = (sample.B11 - sample.B08) / (sample.B11 + sample.B08);
                
                // Water detection (NDWI)
                let water = (sample.B03 - sample.B08) / (sample.B03 + sample.B08);
                
                // Cloud mask from SCL
                let cloud = sample.SCL === 9 || sample.SCL === 10 ? 1 : 0;
                
                return [ndvi, builtUp, water, cloud];
            }
            """
            
            payload = {
                "input": {
                    "bounds": {
                        "bbox": bbox,
                        "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"}
                    },
                    "data": [{
                        "type": "sentinel-2-l2a",
                        "dataFilter": {
                            "timeRange": {
                                "from": f"{date_from}T00:00:00Z",
                                "to": f"{date_to}T23:59:59Z"
                            },
                            "maxCloudCoverage": 30.0
                        }
                    }]
                },
                "output": {
                    "width": 256,
                    "height": 256,
                    "responses": [{
                        "identifier": "default",
                        "format": {"type": "image/tiff"}
                    }]
                },
                "evalscript": evalscript
            }
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.process_url, 
                    json=payload, 
                    headers=headers
                ) as response:
                    if response.status == 200:
                        # For now, return mock analysis data
                        # In production, would process the TIFF data
                        analysis = ImageAnalysis(
                            vegetation_index=0.65,  # Mock NDVI
                            built_up_area=0.25,     # Mock built-up percentage
                            water_bodies=0.05,      # Mock water percentage
                            bare_soil=0.05,         # Mock bare soil percentage
                            cloud_coverage=10.0     # Mock cloud coverage
                        )
                        
                        # Cache the result
                        await self.cache_service.set(
                            cache_key, 
                            analysis.__dict__, 
                            ttl=3600  # 1 hour
                        )
                        
                        return analysis
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to analyze satellite image: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error analyzing satellite image: {e}")
            return None
    
    async def get_time_series_analysis(
        self, 
        bbox: List[float], 
        start_date: str, 
        end_date: str,
        interval_days: int = 30
    ) -> List[ImageAnalysis]:
        """
        Get time series analysis for change detection
        """
        cache_key = f"sentinel_timeseries:{':'.join(map(str, bbox))}:{start_date}:{end_date}:{interval_days}"
        
        # Check cache first
        cached_result = await self.cache_service.get(cache_key)
        if cached_result:
            return [ImageAnalysis(**item) for item in cached_result]
        
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            
            analyses = []
            current_dt = start_dt
            
            while current_dt <= end_dt:
                next_dt = current_dt + timedelta(days=interval_days)
                if next_dt > end_dt:
                    next_dt = end_dt
                
                analysis = await self.analyze_satellite_image(
                    bbox,
                    current_dt.strftime("%Y-%m-%d"),
                    next_dt.strftime("%Y-%m-%d")
                )
                
                if analysis:
                    analyses.append(analysis)
                
                current_dt = next_dt + timedelta(days=1)
            
            # Cache the result
            await self.cache_service.set(
                cache_key, 
                [analysis.__dict__ for analysis in analyses], 
                ttl=7200  # 2 hours
            )
            
            return analyses
            
        except Exception as e:
            logger.error(f"Error getting time series analysis: {e}")
            return []
    
    # Synchronous wrappers for Flask compatibility
    def get_satellite_image_sync(self, *args, **kwargs) -> Optional[SatelliteImage]:
        """Synchronous wrapper for get_satellite_image"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.get_satellite_image(*args, **kwargs))
        finally:
            loop.close()
    
    def analyze_satellite_image_sync(self, *args, **kwargs) -> Optional[ImageAnalysis]:
        """Synchronous wrapper for analyze_satellite_image"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.analyze_satellite_image(*args, **kwargs))
        finally:
            loop.close()
    
    def get_time_series_analysis_sync(self, *args, **kwargs) -> List[ImageAnalysis]:
        """Synchronous wrapper for get_time_series_analysis"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.get_time_series_analysis(*args, **kwargs))
        finally:
            loop.close()
