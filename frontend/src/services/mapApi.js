import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || '';

/**
 * Get satellite image for given coordinates
 * @param {number} lat - Latitude
 * @param {number} lng - Longitude
 * @param {number} zoom - Zoom level (1-20)
 * @param {number} width - Image width in pixels
 * @param {number} height - Image height in pixels
 * @param {string} type - Map type ('satellite' or 'map')
 * @returns {Promise<Blob>} - Image blob
 */
export const getSatelliteImage = async (lat, lng, zoom = 16, width = 800, height = 600, type = 'satellite') => {
  try {
    const response = await axios({
      method: 'get',
      url: `${API_BASE_URL}/api/maps/satellite`,
      params: { lat, lon: lng, zoom, width, height, type },
      responseType: 'blob',
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching satellite image:', error);
    throw error;
  }
};

/**
 * Search for places using the map API
 * @param {string} query - Search query
 * @param {number} lat - Latitude for search center
 * @param {number} lng - Longitude for search center
 * @param {number} radius - Search radius in meters
 * @returns {Promise<Object>} - Search results
 */
export const searchPlaces = async (query, lat, lng, radius = 500) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/maps/search`, {
      params: { q: query, lat, lon: lng, radius },
    });
    return response.data;
  } catch (error) {
    console.error('Error searching places:', error);
    throw error;
  }
};

/**
 * Reverse geocode coordinates to address
 * @param {number} lat - Latitude
 * @param {number} lng - Longitude
 * @returns {Promise<Object>} - Address information
 */
export const reverseGeocode = async (lat, lng) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/maps/reverse-geocode`, {
      params: { lat, lon: lng },
    });
    return response.data;
  } catch (error) {
    console.error('Error reverse geocoding:', error);
    throw error;
  }
};

/**
 * Get address suggestions for autocomplete
 * @param {string} query - Partial address query
 * @param {number} [lat] - Optional latitude for biasing results
 * @param {number} [lng] - Optional longitude for biasing results
 * @returns {Promise<Array>} - Array of address suggestions
 */
export const getAddressSuggestions = async (query, lat, lng) => {
  try {
    const params = { q: query };
    if (lat && lng) {
      params.lat = lat;
      params.lon = lng;
    }
    
    const response = await axios.get(`${API_BASE_URL}/api/maps/suggest`, { params });
    return response.data.suggestions || [];
  } catch (error) {
    console.error('Error getting address suggestions:', error);
    return [];
  }
};

export default {
  getSatelliteImage,
  searchPlaces,
  reverseGeocode,
  getAddressSuggestions,
};
