import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Box, CircularProgress, IconButton, Paper, Slider, Tooltip, Zoom } from '@mui/material';
import { styled } from '@mui/material/styles';
import { debounce } from 'lodash';
import {
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  GpsFixed as GpsFixedIcon,
  Refresh as RefreshIcon,
  Layers as LayersIcon,
  SatelliteAlt as SatelliteIcon,
  Map as MapIcon
} from '@mui/icons-material';
import { useSnackbar } from 'notistack';
import { getSatelliteImage } from '../../services/api';

// Styled components
const MapContainer = styled(Box)({
  position: 'relative',
  width: '100%',
  height: '100%',
  overflow: 'hidden',
  borderRadius: '8px',
  boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
  backgroundColor: '#f0f0f0',
});

const MapImage = styled('img')({
  width: '100%',
  height: '100%',
  objectFit: 'cover',
  transition: 'opacity 0.3s ease-in-out',
  cursor: 'grab',
  '&:active': {
    cursor: 'grabbing',
  },
});

const ControlsContainer = styled(Paper)({
  position: 'absolute',
  top: 16,
  right: 16,
  display: 'flex',
  flexDirection: 'column',
  gap: '8px',
  padding: '8px',
  borderRadius: '8px',
  backgroundColor: 'rgba(255, 255, 255, 0.9)',
  boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
  zIndex: 1,
});

const ZoomControls = styled(Box)({
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  gap: '4px',
  padding: '8px 0',
});

const ZoomSlider = styled(Slider)({
  height: '120px',
  '& .MuiSlider-rail': {
    backgroundColor: '#ccc',
  },
  '& .MuiSlider-track': {
    backgroundColor: '#1976d2',
  },
  '& .MuiSlider-thumb': {
    backgroundColor: '#1976d2',
  },
});

const LoadingOverlay = styled(Box)({
  position: 'absolute',
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
  backgroundColor: 'rgba(0, 0, 0, 0.5)',
  zIndex: 2,
  color: 'white',
  flexDirection: 'column',
  gap: '16px',
});

const SatelliteMap = ({
  initialLat = 55.7558,
  initialLng = 37.6173,
  initialZoom = 16,
  width = '100%',
  height = '500px',
  markers = [],
  onMoveEnd,
  onZoom,
  onMarkerClick,
  ...props
}) => {
  const [position, setPosition] = useState({ lat: initialLat, lng: initialLng });
  const [zoom, setZoom] = useState(initialZoom);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [mapType, setMapType] = useState('satellite'); // 'satellite' or 'map'
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [imageSize, setImageSize] = useState({ width: 800, height: 600 });
  const containerRef = useRef(null);
  const { enqueueSnackbar } = useSnackbar();

  // Image cache
  const imageCache = useRef(new Map());

  // Calculate image URL with cache busting
  const getImageUrl = useCallback((lat, lng, zoom, width, height) => {
    const cacheKey = `${lat.toFixed(6)}_${lng.toFixed(6)}_${zoom}_${width}_${height}_${mapType}`;
    
    // Check cache first
    if (imageCache.current.has(cacheKey)) {
      return imageCache.current.get(cacheKey);
    }

    // Generate new URL and cache it
    const url = `/api/maps/satellite?lat=${lat}&lon=${lng}&zoom=${zoom}&width=${width}&height=${height}&type=${mapType}&t=${Date.now()}`;
    imageCache.current.set(cacheKey, url);
    
    // Limit cache size
    if (imageCache.current.size > 20) {
      const firstKey = imageCache.current.keys().next().value;
      imageCache.current.delete(firstKey);
    }
    
    return url;
  }, [mapType]);

  // Handle window resize
  useEffect(() => {
    const handleResize = () => {
      if (containerRef.current) {
        setImageSize({
          width: containerRef.current.offsetWidth,
          height: containerRef.current.offsetHeight,
        });
      }
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Load satellite image
  const loadImage = useCallback(
    debounce(async (lat, lng, zoom, width, height) => {
      try {
        setIsLoading(true);
        setError(null);

        // Use the API service to get the image
        const imageUrl = getImageUrl(lat, lng, zoom, width, height);
        
        // Preload the image
        await new Promise((resolve, reject) => {
          const img = new Image();
          img.onload = () => {
            setPosition({ lat, lng });
            setZoom(zoom);
            setIsLoading(false);
            resolve();
          };
          img.onerror = (err) => {
            console.error('Error loading image:', err);
            setError('Failed to load map image');
            setIsLoading(false);
            reject(err);
          };
          img.src = imageUrl;
        });

        // Notify parent component of position/zoom changes
        if (onMoveEnd) {
          onMoveEnd({ lat, lng, zoom });
        }
      } catch (err) {
        console.error('Error in loadImage:', err);
        enqueueSnackbar('Ошибка загрузки карты', { variant: 'error' });
        setError('Ошибка загрузки карты');
        setIsLoading(false);
      }
    }, 300),
    [getImageUrl, onMoveEnd, enqueueSnackbar]
  );

  // Initial load
  useEffect(() => {
    loadImage(initialLat, initialLng, initialZoom, imageSize.width, imageSize.height);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mapType]);

  // Handle drag start
  const handleMouseDown = (e) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX, y: e.clientY });
  };

  // Handle drag move
  const handleMouseMove = (e) => {
    if (!isDragging) return;
    
    const dx = e.clientX - dragStart.x;
    const dy = e.clientY - dragStart.y;
    setDragOffset({ x: dx, y: dy });
  };

  // Handle drag end
  const handleMouseUp = () => {
    if (!isDragging) return;
    
    // Calculate new position based on drag
    const latPerPixel = 360 / Math.pow(2, zoom + 8);
    const lngPerPixel = latPerPixel * Math.cos((position.lat * Math.PI) / 180);
    
    const newLat = position.lat - (dragOffset.y * latPerPixel);
    const newLng = position.lng + (dragOffset.x * lngPerPixel);
    
    // Load new image at the new position
    loadImage(newLat, newLng, zoom, imageSize.width, imageSize.height);
    
    // Reset drag state
    setIsDragging(false);
    setDragOffset({ x: 0, y: 0 });
  };

  // Handle zoom change
  const handleZoomChange = (e, newZoom) => {
    if (newZoom !== zoom) {
      setZoom(newZoom);
      loadImage(position.lat, position.lng, newZoom, imageSize.width, imageSize.height);
      if (onZoom) onZoom(newZoom);
    }
  };

  // Handle zoom in/out buttons
  const zoomIn = () => {
    const newZoom = Math.min(zoom + 1, 20);
    if (newZoom !== zoom) {
      setZoom(newZoom);
      loadImage(position.lat, position.lng, newZoom, imageSize.width, imageSize.height);
      if (onZoom) onZoom(newZoom);
    }
  };

  const zoomOut = () => {
    const newZoom = Math.max(zoom - 1, 1);
    if (newZoom !== zoom) {
      setZoom(newZoom);
      loadImage(position.lat, position.lng, newZoom, imageSize.width, imageSize.height);
      if (onZoom) onZoom(newZoom);
    }
  };

  // Handle current location
  const handleCurrentLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const { latitude, longitude } = pos.coords;
          loadImage(latitude, longitude, 16, imageSize.width, imageSize.height);
        },
        (err) => {
          console.error('Error getting location:', err);
          enqueueSnackbar('Не удалось определить местоположение', { variant: 'error' });
        }
      );
    } else {
      enqueueSnackbar('Геолокация не поддерживается вашим браузером', { variant: 'warning' });
    }
  };

  // Toggle map type
  const toggleMapType = () => {
    setMapType(prev => prev === 'satellite' ? 'map' : 'satellite');
  };

  // Refresh the current view
  const refreshMap = () => {
    loadImage(position.lat, position.lng, zoom, imageSize.width, imageSize.height);
  };

  // Render markers
  const renderMarkers = () => {
    return markers.map((marker, index) => (
      <Box
        key={index}
        onClick={() => onMarkerClick && onMarkerClick(marker)}
        sx={{
          position: 'absolute',
          left: '50%',
          top: '50%',
          transform: 'translate(-50%, -50%)',
          width: '24px',
          height: '24px',
          backgroundColor: marker.color || '#ff3d00',
          borderRadius: '50%',
          border: '2px solid white',
          cursor: 'pointer',
          zIndex: 2,
          '&:hover': {
            transform: 'translate(-50%, -50%) scale(1.2)',
          },
          ...marker.style,
        }}
      >
        {marker.label && (
          <Box
            sx={{
              position: 'absolute',
              top: '-30px',
              left: '50%',
              transform: 'translateX(-50%)',
              backgroundColor: 'white',
              padding: '2px 8px',
              borderRadius: '4px',
              fontSize: '12px',
              whiteSpace: 'nowrap',
              boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
              zIndex: 3,
            }}
          >
            {marker.label}
          </Box>
        )}
      </Box>
    ));
  };

  return (
    <MapContainer
      ref={containerRef}
      sx={{
        width,
        height,
        position: 'relative',
        ...props.sx,
      }}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      {/* Map Image */}
      <Box
        sx={{
          position: 'relative',
          width: '100%',
          height: '100%',
          overflow: 'hidden',
        }}
      >
        <MapImage
          src={getImageUrl(position.lat, position.lng, zoom, imageSize.width, imageSize.height)}
          alt="Satellite Map"
          style={{
            transform: `translate(${dragOffset.x}px, ${dragOffset.y}px)`,
            opacity: isLoading ? 0.5 : 1,
          }}
          onLoad={() => setIsLoading(false)}
          onError={() => {
            setError('Ошибка загрузки изображения');
            setIsLoading(false);
          }}
        />

        {/* Markers */}
        {markers.length > 0 && renderMarkers()}

        {/* Loading Overlay */}
        {isLoading && (
          <LoadingOverlay>
            <CircularProgress color="inherit" />
            <div>Загрузка карты...</div>
          </LoadingOverlay>
        )}

        {/* Error Overlay */}
        {error && !isLoading && (
          <LoadingOverlay>
            <div>{error}</div>
            <IconButton color="inherit" onClick={refreshMap}>
              <RefreshIcon />
            </IconButton>
          </LoadingOverlay>
        )}
      </Box>

      {/* Controls */}
      <ControlsContainer elevation={3}>
        <Tooltip title="Увеличить">
          <IconButton onClick={zoomIn} size="small">
            <ZoomInIcon />
          </IconButton>
        </Tooltip>

        <ZoomControls>
          <ZoomSlider
            orientation="vertical"
            value={zoom}
            min={1}
            max={20}
            step={1}
            onChange={(e, value) => handleZoomChange(e, value)}
            valueLabelDisplay="auto"
            valueLabelFormat={(value) => `${value}x`}
          />
        </ZoomControls>

        <Tooltip title="Уменьшить">
          <IconButton onClick={zoomOut} size="small">
            <ZoomOutIcon />
          </IconButton>
        </Tooltip>

        <Box sx={{ borderTop: '1px solid #e0e0e0', margin: '8px 0' }} />

        <Tooltip title="Текущее местоположение">
          <IconButton onClick={handleCurrentLocation} size="small">
            <GpsFixedIcon />
          </IconButton>
        </Tooltip>

        <Tooltip title="Обновить карту">
          <IconButton onClick={refreshMap} size="small">
            <RefreshIcon />
          </IconButton>
        </Tooltip>

        <Tooltip title={mapType === 'satellite' ? 'Переключить на карту' : 'Переключить на спутник'}>
          <IconButton onClick={toggleMapType} size="small">
            {mapType === 'satellite' ? <MapIcon /> : <SatelliteIcon />}
          </IconButton>
        </Tooltip>
      </ControlsContainer>

      {/* Attribution */}
      <Box
        sx={{
          position: 'absolute',
          bottom: 8,
          right: 8,
          backgroundColor: 'rgba(255, 255, 255, 0.8)',
          padding: '2px 8px',
          borderRadius: '4px',
          fontSize: '10px',
          zIndex: 1,
        }}
      >
        {mapType === 'satellite' ? 'Спутниковые снимки © Яндекс.Карты' : '© Яндекс.Карты'}
      </Box>
    </MapContainer>
  );
};

export default SatelliteMap;
