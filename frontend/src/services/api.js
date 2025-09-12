import axios from 'axios';
import { MAP_CONFIG, DEFAULT_MAP_CENTER, DEFAULT_ZOOM } from '../config/maps';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001';

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  timeout: 120000, // 2 минуты таймаут для файловых операций
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token to requests
api.interceptors.request.use(
  (config) => {
    // Проверяем оба возможных ключа токена
    const token = localStorage.getItem('authToken') || localStorage.getItem('token');
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

// Violations API
export const violations = {
  getList: () => api.get('/api/violations/list'),
  get: (violationId) => api.get(`/api/violations/${violationId}`),
  update: (violationId, data) => api.put(`/api/violations/${violationId}`, data),
  delete: (violationId) => api.delete(`/api/violations/${violationId}`),
  detect: (formData) => api.post('/api/violations/detect', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  }),
  batchDetect: (formData) => api.post('/api/violations/batch_detect', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  }),
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

// Coordinate analysis API endpoints
export const coordinateAnalysis = {
  // Photo coordinate detection
  detectFromPhoto: (file, locationHint = '') => {
    console.log('📤 detectFromPhoto called with:', {
      fileName: file.name,
      fileSize: file.size,
      fileType: file.type,
      locationHint: locationHint
    });
    
    const formData = new FormData();
    formData.append('file', file);
    if (locationHint) {
      formData.append('location_hint', locationHint);
    }
    
    // Логируем содержимое FormData
    console.log('📤 FormData contents:');
    for (let [key, value] of formData.entries()) {
      if (value instanceof File) {
        console.log(`  ${key}: File(${value.name}, ${value.size} bytes, ${value.type})`);
      } else {
        console.log(`  ${key}: ${value} (type: ${typeof value})`);
      }
    }
    
    // Дополнительная проверка файла
    console.log('📤 File object check:', {
      isFile: file instanceof File,
      fileName: file.name,
      fileSize: file.size,
      fileType: file.type,
      constructor: file.constructor.name
    });
    
    // Используем fetch вместо axios для корректной передачи файлов
    return fetch(`${API_URL}/api/coordinates/detect`, {
      method: 'POST',
      body: formData,
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('authToken') || localStorage.getItem('token') || ''}`
      }
    }).then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    }).then(data => ({ data }));
  },
  
  // Video coordinate analysis
  analyzeVideo: (file, locationHint = '', frameInterval = 30, maxFrames = 10) => {
    console.log('📤 analyzeVideo called with:', {
      fileName: file.name,
      fileSize: file.size,
      fileType: file.type,
      locationHint: locationHint,
      frameInterval: frameInterval,
      maxFrames: maxFrames
    });
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('location_hint', locationHint);
    formData.append('frame_interval', frameInterval.toString());
    formData.append('max_frames', maxFrames.toString());
    
    // Логируем содержимое FormData
    console.log('📤 FormData contents:');
    for (let [key, value] of formData.entries()) {
      if (value instanceof File) {
        console.log(`  ${key}: File(${value.name}, ${value.size} bytes, ${value.type})`);
      } else {
        console.log(`  ${key}: ${value}`);
      }
    }
    
    // Используем fetch вместо axios для корректной передачи файлов
    return fetch(`${API_URL}/api/coordinates/video/analyze`, {
      method: 'POST',
      body: formData,
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('authToken') || localStorage.getItem('token') || ''}`
      }
    }).then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    }).then(data => ({ data }));
  },
  
  estimateProcessingTime: (file, frameInterval = 30, maxFrames = 10) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('frame_interval', frameInterval.toString());
    formData.append('max_frames', maxFrames.toString());
    
    return api.post('/api/coordinates/video/estimate', formData);
  }
};

// Legacy video analysis API (for backward compatibility)
export const videoAnalysis = coordinateAnalysis;

// Image analysis API (alias for coordinate analysis)
export const imageAnalysis = coordinateAnalysis;

// Object Group Analysis API
export const objectGroupAnalysis = {
  analyzeGroups: (objects, locationHint = '') => {
    console.log('📤 analyzeGroups called with:', {
      objectsCount: objects.length,
      locationHint: locationHint,
      objects: objects.map(obj => ({
        id: obj.id,
        name: obj.name,
        filesCount: obj.files.length
      }))
    });
    
    const formData = new FormData();
    
    // Add objects metadata
    const objectsData = objects.map((obj, index) => ({
      id: obj.id,
      name: obj.name,
      description: obj.description,
      file_keys: obj.files.map((_, fileIndex) => `object_${obj.id}_file_${fileIndex}`)
    }));
    
    formData.append('objects', JSON.stringify(objectsData));
    
    if (locationHint) {
      formData.append('location_hint', locationHint);
    }
    
    // Add all files with unique keys
    objects.forEach((obj) => {
      obj.files.forEach((fileData, fileIndex) => {
        const fileKey = `object_${obj.id}_file_${fileIndex}`;
        formData.append(fileKey, fileData.file);
      });
    });

    // Log FormData contents
    console.log('📤 FormData contents:');
    for (let [key, value] of formData.entries()) {
      if (value instanceof File) {
        console.log(`  ${key}: File(${value.name}, ${value.size} bytes, ${value.type})`);
      } else {
        console.log(`  ${key}: ${value}`);
      }
    }

    return fetch(`${API_URL}/api/object-groups/analyze`, {
      method: 'POST',
      body: formData,
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('authToken') || localStorage.getItem('token') || ''}`
      }
    }).then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    }).then(data => ({ data }));
  }
};

export { api };
export default api;
