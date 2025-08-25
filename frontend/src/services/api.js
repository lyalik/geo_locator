import axios from 'axios';

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
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Authentication API
export const auth = {
  signup: (email, password) => api.post('/auth/register', { email, password }),
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
  getYandexMap: (center, zoom = 12) => {
    return `https://maps-rc.yandex.ru/1.1/?ll=${center[1]},${center[0]}&z=${zoom}&l=map`;
  },
  get2GISMap: (center, zoom = 12) => {
    return `https://2gis.ru/?q=${center[0]},${center[1]}&zoom=${zoom}`;
  },
};

export default api;
