import { useState, useCallback, useEffect } from 'react';
import { useSnackbar } from 'notistack';

/**
 * Custom hook for managing map view state and interactions
 * @param {Object} initialView - Initial view state { center: { lat, lng }, zoom }
 * @param {Function} onViewChange - Callback when view changes
 * @returns {Object} Map view state and interaction handlers
 */
const useMapView = (initialView = {}, onViewChange) => {
  const { enqueueSnackbar } = useSnackbar();
  
  const [viewState, setViewState] = useState({
    center: initialView.center || { lat: 55.7558, lng: 37.6173 }, // Default to Moscow
    zoom: initialView.zoom || 12,
    bearing: 0,
    pitch: 0,
  });
  
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState(null);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Update view state and call the onViewChange callback
  const updateView = useCallback((newView) => {
    setViewState(prev => {
      const updatedView = {
        ...prev,
        ...newView,
        center: newView.center || prev.center,
      };
      
      // Call the callback with the new view state
      if (onViewChange) {
        onViewChange(updatedView);
      }
      
      return updatedView;
    });
  }, [onViewChange]);

  // Handle zoom in
  const zoomIn = useCallback(() => {
    updateView({
      zoom: Math.min(viewState.zoom + 1, 20)
    });
  }, [updateView, viewState.zoom]);

  // Handle zoom out
  const zoomOut = useCallback(() => {
    updateView({
      zoom: Math.max(viewState.zoom - 1, 1)
    });
  }, [updateView, viewState.zoom]);

  // Handle map drag start
  const handleDragStart = useCallback((event) => {
    setIsDragging(true);
    setDragStart({
      x: event.clientX,
      y: event.clientY,
      center: { ...viewState.center }
    });
  }, [viewState.center]);

  // Handle map drag move
  const handleDragMove = useCallback((event) => {
    if (!isDragging || !dragStart) return;
    
    const dx = event.clientX - dragStart.x;
    const dy = event.clientY - dragStart.y;
    
    setDragOffset({ x: dx, y: dy });
  }, [isDragging, dragStart]);

  // Handle map drag end
  const handleDragEnd = useCallback(() => {
    if (!isDragging || !dragStart) return;
    
    // Calculate new center based on drag distance
    const latPerPixel = 360 / Math.pow(2, viewState.zoom + 8);
    const lngPerPixel = latPerPixel * Math.cos((viewState.center.lat * Math.PI) / 180);
    
    const newLat = dragStart.center.lat - (dragOffset.y * latPerPixel);
    const newLng = dragStart.center.lng + (dragOffset.x * lngPerPixel);
    
    // Update the view with the new center
    updateView({
      center: {
        lat: newLat,
        lng: newLng
      }
    });
    
    // Reset drag state
    setIsDragging(false);
    setDragOffset({ x: 0, y: 0 });
    setDragStart(null);
  }, [isDragging, dragStart, dragOffset, viewState.zoom, updateView]);

  // Handle zoom change
  const handleZoom = useCallback((newZoom) => {
    updateView({
      zoom: newZoom
    });
  }, [updateView]);

  // Pan to a specific location
  const panTo = useCallback((location, zoom = null) => {
    updateView({
      center: {
        lat: location.lat,
        lng: location.lng
      },
      ...(zoom !== null && { zoom })
    });
  }, [updateView]);

  // Get current location using browser geolocation
  const getCurrentLocation = useCallback(() => {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        enqueueSnackbar('Геолокация не поддерживается вашим браузером', { variant: 'warning' });
        reject(new Error('Geolocation is not supported'));
        return;
      }

      setIsLoading(true);
      setError(null);
      
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          const location = { lat: latitude, lng: longitude };
          
          // Update view to current location
          panTo(location, 16);
          setIsLoading(false);
          resolve(location);
        },
        (error) => {
          console.error('Error getting location:', error);
          const errorMessage = error.message || 'Не удалось определить местоположение';
          enqueueSnackbar(errorMessage, { variant: 'error' });
          setError(errorMessage);
          setIsLoading(false);
          reject(error);
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 0,
        }
      );
    });
  }, [enqueueSnackbar, panTo]);

  // Fit bounds to show all markers
  const fitBounds = useCallback((markers, padding = 50) => {
    if (!markers || markers.length === 0) return;
    
    // Calculate bounds that contain all markers
    const lats = markers.map(marker => marker.position.lat);
    const lngs = markers.map(marker => marker.position.lng);
    
    const bounds = {
      north: Math.max(...lats),
      south: Math.min(...lats),
      east: Math.max(...lngs),
      west: Math.min(...lngs),
    };
    
    // Calculate center and zoom
    const center = {
      lat: (bounds.north + bounds.south) / 2,
      lng: (bounds.east + bounds.west) / 2,
    };
    
    // Simple zoom calculation (could be improved)
    const latDelta = bounds.north - bounds.south;
    const lngDelta = bounds.east - bounds.west;
    const maxDelta = Math.max(latDelta, lngDelta);
    const zoom = Math.min(
      Math.floor(Math.log2(360 / (maxDelta * 1.5)) + 1),
      18
    );
    
    // Update view
    updateView({
      center,
      zoom: Math.max(zoom, 10) // Don't zoom out too much
    });
  }, [updateView]);

  // Handle window resize
  useEffect(() => {
    const handleResize = () => {
      // You can add resize handling here if needed
    };
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return {
    // State
    viewState,
    isDragging,
    dragOffset,
    isLoading,
    error,
    
    // Actions
    updateView,
    zoomIn,
    zoomOut,
    handleDragStart,
    handleDragMove,
    handleDragEnd,
    handleZoom,
    panTo,
    getCurrentLocation,
    fitBounds,
  };
};

export default useMapView;
