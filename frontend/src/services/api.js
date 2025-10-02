import axios from 'axios';

// Base URL for API calls - УМНОЕ определение с поддержкой nginx
const getApiUrl = () => {
  const hostname = window.location.hostname;
  const protocol = window.location.protocol;
  
  console.log(`🌐 Current hostname: ${hostname}`);
  
  // Если заход через локальную сеть - прямое обращение к backend на порту 5001
  if (hostname === '192.168.1.67' || hostname === 'localhost' || hostname === '127.0.0.1') {
    const apiUrl = 'http://192.168.1.67:5001';
    console.log(`🏠 Local network API (direct): ${apiUrl}`);
    return apiUrl;
  }
  
  // Для внешнего доступа через nginx - пустой baseURL, будем использовать абсолютные пути
  // nginx проксирует /api/* на backend:5001/api/*
  const apiUrl = '';
  console.log(`🌍 External API through nginx (relative paths)`);
  return apiUrl;
};

const API_URL = getApiUrl();

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  timeout: 120000, // 2 минуты таймаут для файловых операций
  withCredentials: true, // Включаем отправку cookies для сессионной авторизации
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor для сессионной авторизации
api.interceptors.request.use(
  (config) => {
    // Для сессионной авторизации Flask-Login не нужны Bearer токены
    // Cookies будут автоматически отправляться с withCredentials: true
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
  getYandexMap: (center = [55.7558, 37.6176], zoom = 10) => {
    const [lat, lon] = center;
    return `https://api-maps.yandex.ru/2.1/?lang=ru_RU&ll=${lon},${lat}&z=${zoom}&l=map`;
  },
  
  get2GISMap: (center = [55.7558, 37.6176], zoom = 10) => {
    const [lat, lon] = center;
    return `https://maps.2gis.com/?l=map&pt=${lon},${lat}&z=${zoom}`;
  },
  
  // Geocoding service
  geocode: async (address) => {
    try {
      const response = await fetch(
        `https://geocode-maps.yandex.ru/1.x/?format=json&geocode=${encodeURIComponent(address)}`
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
        `https://geocode-maps.yandex.ru/1.x/?format=json&geocode=${lon},${lat}`
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
      credentials: 'include' // Включаем cookies для сессионной авторизации
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
      credentials: 'include' // Включаем cookies для сессионной авторизации
    }).then(async response => {
      if (!response.ok) {
        // Пытаемся получить детальное сообщение об ошибке
        try {
          const errorData = await response.json();
          if (errorData.error === 'VIDEO_TOO_LONG') {
            throw new Error(errorData.message || `Видео слишком длинное (${errorData.duration} сек). Максимум: ${errorData.max_duration} сек`);
          }
          throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
        } catch (e) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
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

// Image analysis API (alias for coordinate analysis)
export const imageAnalysis = coordinateAnalysis;

// Video analysis API (alias for coordinate analysis)
export const videoAnalysis = coordinateAnalysis;

// Object Group Analysis API
export const objectGroupAnalysis = {
  analyzeGroups: (objects, locationHint = '') => {
    console.log('📤 analyzeGroups called with:', {
      locationHint: locationHint,
      objects: objects.map(obj => ({
        id: obj.id,
        name: obj.name,
        filesCount: obj.files.length
      }))
    });
    
    const formData = new FormData();
    
    if (locationHint) {
      formData.append('location_hint', locationHint);
    }
    
    // Добавляем все файлы из всех групп как простой список для batch_detect
    objects.forEach((obj) => {
      obj.files.forEach((fileData) => {
        formData.append('files', fileData.file);
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

    // Используем существующий batch_detect endpoint вместо несуществующего object-groups
    return fetch(`${API_URL}/api/violations/batch_detect`, {
      method: 'POST',
      body: formData,
      credentials: 'include' // Включаем cookies для сессионной авторизации
    }).then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    }).then(data => ({ data }));
  }
};

// Reference Database API methods
export const referenceDbApi = {
  // Получение статистики готовой базы данных
  getStats: () => api.get('/api/dataset/reference_db/stats'),
  
  // Поиск в готовой базе по координатам
  searchByCoordinates: (latitude, longitude, radiusKm = 0.1) => 
    api.post('/api/dataset/reference_db/search', {
      latitude,
      longitude,
      radius_km: radiusKm
    }),
  
  // Валидация результата против готовой базы
  validateDetection: (data) => 
    api.post('/api/dataset/reference_db/validate', data),
  
  // Получение примеров записей
  getSamples: (violationType = null, limit = 10) => 
    api.get('/api/dataset/reference_db/samples', {
      params: { violation_type: violationType, limit }
    })
};

// Model Training API methods
export const trainingApi = {
  // Дообучение YOLO модели
  trainYolo: () => api.post('/api/dataset/train_yolo'),
  
  // Дообучение Mistral AI модели
  trainMistral: () => api.post('/api/dataset/train_mistral'),
  
  // Получение статуса обучения
  getTrainingStatus: () => api.get('/api/dataset/training_status'),
  
  // Пакетная обработка для тестирования производительности
  batchProcess: (imagePaths) => 
    api.post('/api/dataset/batch_process', { image_paths: imagePaths })
};

export { api };
export default api;
