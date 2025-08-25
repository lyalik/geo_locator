import React, { createContext, useState, useContext, useCallback } from 'react';
import { useSnackbar } from 'notistack';
import { getSatelliteImage, searchPlaces, reverseGeocode } from '../services/mapApi';

const MapContext = createContext();

export const MapProvider = ({ children }) => {
  const [mapState, setMapState] = useState({
    center: { lat: 55.7558, lng: 37.6173 }, // Moscow by default
    zoom: 12,
    isLoading: false,
    error: null,
    markers: [],
    selectedMarker: null,
    mapType: 'satellite',
  });

  const { enqueueSnackbar } = useSnackbar();

  // Update map view (center and zoom)
  const updateView = useCallback(async (lat, lng, zoom = mapState.zoom) => {
    try {
      setMapState(prev => ({
        ...prev,
        center: { lat, lng },
        zoom,
        isLoading: true,
        error: null,
      }));

      // Preload the image
      await getSatelliteImage(lat, lng, zoom);

      setMapState(prev => ({
        ...prev,
        isLoading: false,
      }));
    } catch (error) {
      console.error('Error updating map view:', error);
      setMapState(prev => ({
        ...prev,
        isLoading: false,
        error: 'Не удалось обновить карту',
      }));
      enqueueSnackbar('Ошибка при обновлении карты', { variant: 'error' });
    }
  }, [mapState.zoom, enqueueSnackbar]);

  // Add a marker to the map
  const addMarker = useCallback((marker) => {
    setMapState(prev => ({
      ...prev,
      markers: [...prev.markers, {
        id: Date.now().toString(),
        position: { lat: marker.lat, lng: marker.lng },
        title: marker.title || 'Метка',
        description: marker.description || '',
        color: marker.color || '#ff3d00',
        ...marker,
      }],
    }));
  }, []);

  // Remove a marker by ID
  const removeMarker = useCallback((markerId) => {
    setMapState(prev => ({
      ...prev,
      markers: prev.markers.filter(marker => marker.id !== markerId),
      selectedMarker: prev.selectedMarker?.id === markerId ? null : prev.selectedMarker,
    }));
  }, []);

  // Update an existing marker
  const updateMarker = useCallback((markerId, updates) => {
    setMapState(prev => ({
      ...prev,
      markers: prev.markers.map(marker => 
        marker.id === markerId ? { ...marker, ...updates } : marker
      ),
    }));
  }, []);

  // Select a marker
  const selectMarker = useCallback((marker) => {
    setMapState(prev => ({
      ...prev,
      selectedMarker: marker,
    }));
  }, []);

  // Clear all markers
  const clearMarkers = useCallback(() => {
    setMapState(prev => ({
      ...prev,
      markers: [],
      selectedMarker: null,
    }));
  }, []);

  // Toggle map type between satellite and map
  const toggleMapType = useCallback(() => {
    setMapState(prev => ({
      ...prev,
      mapType: prev.mapType === 'satellite' ? 'map' : 'satellite',
    }));
  }, []);

  // Search for places
  const search = useCallback(async (query, options = {}) => {
    try {
      const { lat, lng } = options.center || mapState.center;
      const radius = options.radius || 1000; // 1km by default
      
      const results = await searchPlaces(query, lat, lng, radius);
      return results;
    } catch (error) {
      console.error('Error searching places:', error);
      enqueueSnackbar('Ошибка при поиске мест', { variant: 'error' });
      return [];
    }
  }, [mapState.center, enqueueSnackbar]);

  // Reverse geocode coordinates to address
  const getAddressFromCoordinates = useCallback(async (lat, lng) => {
    try {
      const result = await reverseGeocode(lat, lng);
      return result;
    } catch (error) {
      console.error('Error reverse geocoding:', error);
      enqueueSnackbar('Не удалось определить адрес', { variant: 'error' });
      return null;
    }
  }, [enqueueSnackbar]);

  // Get current location
  const getCurrentLocation = useCallback(() => {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        enqueueSnackbar('Геолокация не поддерживается вашим браузером', { variant: 'warning' });
        reject(new Error('Geolocation is not supported'));
        return;
      }

      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          resolve({ lat: latitude, lng: longitude });
        },
        (error) => {
          console.error('Error getting location:', error);
          enqueueSnackbar('Не удалось определить ваше местоположение', { variant: 'error' });
          reject(error);
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 0,
        }
      );
    });
  }, [enqueueSnackbar]);

  // Pan to location
  const panTo = useCallback(async (location, zoom = 16) => {
    await updateView(location.lat, location.lng, zoom);
  }, [updateView]);

  // Fit bounds to show all markers
  const fitBounds = useCallback((bounds) => {
    // This is a simplified version - in a real app, you'd calculate the bounds
    // that contain all markers and center/zoom the map accordingly
    if (mapState.markers.length === 0) return;

    // Simple implementation: just center on the first marker
    const firstMarker = mapState.markers[0];
    updateView(firstMarker.position.lat, firstMarker.position.lng, 14);
  }, [mapState.markers, updateView]);

  return (
    <MapContext.Provider
      value={{
        ...mapState,
        updateView,
        addMarker,
        removeMarker,
        updateMarker,
        selectMarker,
        clearMarkers,
        toggleMapType,
        search,
        getAddressFromCoordinates,
        getCurrentLocation,
        panTo,
        fitBounds,
      }}
    >
      {children}
    </MapContext.Provider>
  );
};

// Custom hook to use the map context
export const useMap = () => {
  const context = useContext(MapContext);
  if (!context) {
    throw new Error('useMap must be used within a MapProvider');
  }
  return context;
};

export default MapContext;
