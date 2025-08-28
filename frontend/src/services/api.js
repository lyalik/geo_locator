import axios from 'axios';
import { MAP_CONFIG, DEFAULT_MAP_CENTER, DEFAULT_ZOOM } from '../config/maps';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api/v1';

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const isAuthEndpoint = error.config?.url?.includes('/auth/');
    if (error.response?.status === 401 && !isAuthEndpoint) {
      // Handle unauthorized access (but not for auth endpoints)
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Authentication API
export const auth = {
  signup: (username, email, password) => api.post('/auth/register', { username, email, password }),
  login: (email, password) => api.post('/auth/login', { email, password }),
  logout: () => api.post('/auth/logout'),
  getCurrentUser: () => api.get('/auth/me'),
};

// Search API
export const search = {
  byText: (query) => api.post('/search/text', { query }),
  byImage: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/search/image', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  byVideo: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/search/video', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  byPanorama: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/search/panorama', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  getStatus: (requestId) => api.get(`/search/status/${requestId}`),
  getHistory: () => api.get('/search/history'),
};

// Maps API
export const maps = {
  getYandexMap: (center = DEFAULT_MAP_CENTER, zoom = DEFAULT_ZOOM) => {
    const [lat, lon] = center;
    const { apiKey } = MAP_CONFIG.yandex;
    return `https://api-maps.yandex.ru/2.1/?apikey=${apiKey}&lang=ru_RU&ll=${lon},${lat}&z=${zoom}&l=map`;
  },
  
  get2GISMap: (center = DEFAULT_MAP_CENTER, zoom = DEFAULT_ZOOM) => {
    const [lat, lon] = center;
    const { apiKey } = MAP_CONFIG.dgis;
    return `https://maps.2gis.com/?l=map&pt=${lon},${lat}&z=${zoom}&key=${apiKey}`;
  },
  
  // Geocoding service
  geocode: async (address) => {
    try {
      const response = await fetch(
        `https://geocode-maps.yandex.ru/1.x/?apikey=${MAP_CONFIG.yandex.apiKey}&format=json&geocode=${encodeURIComponent(address)}`
      );
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Geocoding error:', error);
      throw error;
    }
  },
  
  // Reverse geocoding service
  reverseGeocode: async (lat, lon) => {
    try {
      const response = await fetch(
        `https://geocode-maps.yandex.ru/1.x/?apikey=${MAP_CONFIG.yandex.apiKey}&format=json&geocode=${lon},${lat}`
      );
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Reverse geocoding error:', error);
      throw error;
    }
  }
};

export { api };
export default api;
