import axios from 'axios';
import { Platform } from 'react-native';

// Конфигурация API
const API_BASE_URL = Platform.OS === 'web' && typeof window !== 'undefined' && window.location?.hostname === 'localhost'
  ? 'http://localhost:5001'  // Веб-версия
  : 'http://192.168.1.67:5001'; // Мобильная версия

// Проверяем доступность API
const checkAPIConnection = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    return response.ok;
  } catch (error) {
    console.error('❌ API недоступен:', error);
    return false;
  }
};

class ApiService {
  constructor() {
    console.log('🔧 Инициализация ApiService...');
    console.log('🌐 Platform.OS:', Platform.OS);
    console.log('🔗 API_BASE_URL:', API_BASE_URL);
    console.log('🌍 Window location:', typeof window !== 'undefined' ? window.location?.hostname : 'undefined');
    
    this.api = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000, // 30 секунд для анализа изображений
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    // Проверяем подключение к API при инициализации
    this.checkConnection();
    
    console.log('✅ ApiService инициализирован с baseURL:', this.api.defaults.baseURL);
  }
  
  async checkConnection() {
    try {
      const isConnected = await checkAPIConnection();
      if (isConnected) {
        console.log('✅ Подключение к API успешно');
      } else {
        console.warn('⚠️ API недоступен, проверьте сервер');
      }
    } catch (error) {
      console.error('❌ Ошибка проверки подключения:', error);
    }

    // Интерцептор для добавления токена авторизации
    this.api.interceptors.request.use(
      async (config) => {
        try {
          const AsyncStorage = (await import('@react-native-async-storage/async-storage')).default;
          const userData = await AsyncStorage.getItem('user');
          if (userData) {
            const user = JSON.parse(userData);
            const token = await AsyncStorage.getItem('authToken') || `session_${user.id}_${Date.now()}`;
            config.headers.Authorization = `Bearer ${token}`;
          }
        } catch (error) {
          console.log('Error getting auth token:', error);
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Интерцептор для обработки ошибок
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('API Error:', error);
        if (error.code === 'ECONNABORTED') {
          throw new Error('Превышено время ожидания. Проверьте подключение к интернету.');
        }
        if (error.response?.status === 500) {
          throw new Error('Ошибка сервера. Попробуйте позже.');
        }
        if (error.response?.status === 404) {
          throw new Error('Сервис недоступен. Проверьте настройки.');
        }
        if (error.response?.status === 401) {
          throw new Error('Ошибка авторизации. Войдите в систему заново.');
        }
        throw error;
      }
    );
  }

  /**
   * Детекция нарушений на изображении с OSM контекстом и ИИ анализом
   * @param {FormData} formData - Данные формы с изображением и координатами
   * @param {Object} location - Координаты для получения OSM контекста
   * @returns {Promise} Результат анализа с OSM контекстом
   */
  async detectViolationWithAI(formData, location = null) {
    try {
      console.log('🤖 Начинаем ИИ анализ с OSM контекстом...');
      console.log('📡 API Base URL:', this.api.defaults.baseURL);
      console.log('📝 FormData содержит:', Array.from(formData.keys()));
      
      // Проверяем подключение перед отправкой
      const isConnected = await checkAPIConnection();
      if (!isConnected) {
        throw new Error('Сервер недоступен. Проверьте подключение к интернету.');
      }
      
      // Получаем OSM контекст если есть координаты
      let osmContext = null;
      if (location && location.latitude && location.longitude) {
        console.log('🗺️ Получаем OSM контекст для координат:', location);
        try {
          osmContext = await this.getOSMUrbanContext(location.latitude, location.longitude);
          console.log('✅ OSM контекст получен:', osmContext);
        } catch (error) {
          console.warn('⚠️ Не удалось получить OSM контекст:', error.message);
        }
      }
      
      // Добавляем OSM контекст в FormData если доступен
      if (osmContext && osmContext.success) {
        formData.append('osm_context', JSON.stringify(osmContext.data));
        console.log('📍 OSM контекст добавлен в запрос');
      }
      
      const response = await this.api.post('/api/violations/detect', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 60000, // 60 секунд
      });
      
      console.log('✅ ИИ анализ успешно завершен:', response.status);
      
      // Обогащаем результат OSM данными
      const result = response.data;
      if (result.success && osmContext && osmContext.success) {
        result.data.osmContext = osmContext.data;
        
        // Генерируем контекстный алерт
        try {
          const contextAlert = await this.generateContextualAlert(
            result.data.violations || [],
            osmContext.data
          );
          result.data.contextAlert = contextAlert;
          console.log('🚨 Контекстный алерт сгенерирован:', contextAlert);
        } catch (error) {
          console.warn('⚠️ Не удалось сгенерировать контекстный алерт:', error.message);
        }
      }
      
      return result;
    } catch (error) {
      console.error('❌ Ошибка ИИ анализа с OSM:');
      console.error('🔗 URL:', error.config?.url);
      console.error('📡 Base URL:', error.config?.baseURL);
      console.error('🌐 Network Error:', error.message);
      console.error('📱 Error Code:', error.code);
      console.error('🔍 Full Error:', error);
      
      if (error.response) {
        console.error('📤 Response Status:', error.response.status);
        console.error('📥 Response Data:', error.response.data);
      }
      
      throw error;
    }
  }

  /**
   * Детекция нарушений на изображении (базовая версия)
   * @param {FormData} formData - Данные формы с изображением и координатами
   * @returns {Promise} Результат анализа
   */
  async detectViolation(formData) {
    try {
      console.log('🔄 Начинаем анализ нарушений...');
      console.log('📡 API Base URL:', this.api.defaults.baseURL);
      console.log('📝 FormData содержит:', Array.from(formData.keys()));
      
      // Проверяем подключение перед отправкой
      const isConnected = await checkAPIConnection();
      if (!isConnected) {
        throw new Error('Сервер недоступен. Проверьте подключение к интернету.');
      }
      
      const response = await this.api.post('/api/violations/detect', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 60000, // 60 секунд
      });
      
      console.log('✅ Анализ успешно завершен:', response.status);
      console.log('📊 Результат:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ Ошибка детекции нарушений:');
      console.error('🔗 URL:', error.config?.url);
      console.error('📡 Base URL:', error.config?.baseURL);
      console.error('🌐 Network Error:', error.message);
      console.error('📱 Error Code:', error.code);
      console.error('🔍 Full Error:', error);
      
      if (error.response) {
        console.error('📤 Response Status:', error.response.status);
        console.error('📥 Response Data:', error.response.data);
      } else if (error.request) {
        console.error('📡 No Response Received:', error.request);
      }
      
      throw error;
    }
  }

  /**
   * Получение списка нарушений поблизости
   * @param {number} latitude - Широта
   * @param {number} longitude - Долгота  
   * @param {number} radius - Радиус поиска в метрах (по умолчанию 1000м)
   * @returns {Promise} Список нарушений
   */
  async getNearbyViolations(latitude, longitude, radius = 1000) {
    try {
      const response = await this.api.get('/api/violations/list', {
        params: {
          latitude,
          longitude,
          radius,
        },
      });
      return response.data;
    } catch (error) {
      console.error('Ошибка получения нарушений поблизости:', error);
      throw error;
    }
  }

  /**
   * Получение всех нарушений для карты
   * @returns {Promise} Список всех нарушений
   */
  async getAllViolations() {
    try {
      const response = await this.api.get('/api/violations/list');
      return response.data;
    } catch (error) {
      console.error('Ошибка получения всех нарушений:', error);
      throw error;
    }
  }

  /**
   * Получение аналитики и статистики
   * @returns {Promise} Данные аналитики
   */
  async getAnalytics() {
    try {
      const response = await this.api.get('/api/violations/analytics');
      return response.data;
    } catch (error) {
      console.error('Ошибка получения аналитики:', error);
      throw error;
    }
  }

  /**
   * Получение истории загрузок пользователя
   * @param {string} userId - ID пользователя (опционально)
   * @returns {Promise} История пользователя
   */
  async getUserHistory(userId = null) {
    try {
      console.log('📊 Получение истории пользователя...');
      const params = userId ? { user_id: userId } : {};
      const response = await this.api.get('/api/violations/history', { params });
      console.log('✅ История получена:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ Ошибка получения истории:', error);
      return { success: false, error: error.message };
    }
  }

  // Получение нарушений с координатами
  async getViolationsWithCoordinates() {
    try {
      console.log('📍 Получение нарушений с координатами...');
      const response = await this.api.get('/api/violations/coordinates');
      console.log('✅ Нарушения с координатами получены:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ Ошибка получения нарушений с координатами:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * Геокодирование адреса
   * @param {string} address - Адрес для геокодирования
   * @returns {Promise} Координаты адреса
   */
  async geocodeAddress(address) {
    try {
      const response = await this.api.get('/api/geo/geocode', {
        params: { address },
      });
      return response.data;
    } catch (error) {
      console.error('Ошибка геокодирования:', error);
      throw error;
    }
  }

  /**
   * Обратное геокодирование координат
   * @param {number} latitude - Широта
   * @param {number} longitude - Долгота
   * @returns {Promise} Адрес по координатам
   */
  async reverseGeocode(latitude, longitude) {
    try {
      const response = await this.api.get('/api/geo/reverse', {
        params: { latitude, longitude },
      });
      return response.data;
    } catch (error) {
      console.error('Ошибка обратного геокодирования:', error);
      throw error;
    }
  }

  /**
   * Проверка статуса сервера
   * @returns {Promise} Статус сервера
   */
  async checkServerStatus() {
    try {
      const response = await this.api.get('/health');
      return {
        online: true,
        message: 'Сервер работает нормально',
        ...response.data
      };
    } catch (error) {
      console.error('Ошибка проверки статуса сервера:', error);
      return {
        online: false,
        message: 'Сервер недоступен'
      };
    }
  }

  /**
   * Получение детальной информации о нарушении
   * @param {string} violationId - ID нарушения
   * @returns {Promise} Детальная информация о нарушении
   */
  async getViolationDetails(violationId) {
    try {
      const response = await this.api.get(`/api/violations/details/${violationId}`);
      return response.data;
    } catch (error) {
      console.error('Ошибка получения деталей нарушения:', error);
      throw error;
    }
  }

  /**
   * Обновление нарушения
   * @param {string} violationId - ID нарушения
   * @param {Object} updateData - Данные для обновления (notes, status)
   * @returns {Promise} Результат обновления
   */
  async updateViolation(violationId, updateData) {
    try {
      const response = await this.api.put(`/api/violations/details/${violationId}`, updateData);
      return response.data;
    } catch (error) {
      console.error('Ошибка обновления нарушения:', error);
      throw error;
    }
  }

  /**
   * Удаление нарушения
   * @param {string} violationId - ID нарушения
   * @param {string} userId - ID пользователя
   * @returns {Promise} Результат удаления
   */
  async deleteViolation(violationId, userId) {
    try {
      const response = await this.api.delete(`/api/violations/details/${violationId}`, {
        data: { user_id: userId }
      });
      return response.data;
    } catch (error) {
      console.error('Ошибка удаления нарушения:', error);
      throw error;
    }
  }

  /**
   * Получение персональной статистики пользователя
   * @param {string} userId - ID пользователя
   * @returns {Promise} Статистика пользователя
   */
  async getUserStats(userId) {
    try {
      const response = await this.api.get(`/api/violations/user/${userId}/stats`);
      return response.data;
    } catch (error) {
      console.error('Ошибка получения статистики пользователя:', error);
      throw error;
    }
  }

  async login(email, password) {
    try {
      const response = await this.api.post('/auth/login', {
        email,
        password
      }, {
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      const token = response.data.token || `session_${response.data.user?.id}_${Date.now()}`;
      
      // Сохраняем токен в AsyncStorage
      const AsyncStorage = (await import('@react-native-async-storage/async-storage')).default;
      await AsyncStorage.setItem('authToken', token);
      
      return {
        success: true,
        user: response.data.user,
        token: token
      };
    } catch (error) {
      console.error('Login failed:', error);
      return {
        success: false,
        message: error.response?.data?.message || 'Ошибка авторизации'
      };
    }
  }

  /**
   * Регистрация пользователя
   * @param {string} username - Имя пользователя
   * @param {string} email - Email
   * @param {string} password - Пароль
   * @returns {Promise} Результат регистрации
   */
  async register(username, email, password) {
    try {
      const response = await this.api.post('/auth/register', {
        username,
        email,
        password
      }, {
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      const token = response.data.token || `session_${response.data.user?.id}_${Date.now()}`;
      
      // Сохраняем токен в AsyncStorage
      const AsyncStorage = (await import('@react-native-async-storage/async-storage')).default;
      await AsyncStorage.setItem('authToken', token);
      
      return {
        success: true,
        user: response.data.user,
        token: token
      };
    } catch (error) {
      console.error('Registration failed:', error);
      return {
        success: false,
        message: error.response?.data?.message || 'Ошибка регистрации'
      };
    }
  }

  /**
   * Пакетная загрузка изображений
   * @param {Array} files - Массив файлов для анализа
   * @param {Object} location - Координаты {latitude, longitude}
   * @returns {Promise} Результаты анализа
   */
  async batchDetectViolations(files, location = null) {
    try {
      const formData = new FormData();
      
      files.forEach((file, index) => {
        formData.append('files', file);
      });

      if (location) {
        formData.append('latitude', location.latitude.toString());
        formData.append('longitude', location.longitude.toString());
      }

      const response = await this.api.post('/api/violations/batch_detect', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 60000, // 60 секунд для пакетной обработки
      });
      
      return response.data;
    } catch (error) {
      console.error('Ошибка пакетной детекции:', error);
      throw error;
    }
  }

  // Получение нарушений с координатами
  async getViolationsWithCoordinates() {
    try {
      console.log('📍 Получение нарушений с координатами...');
      const response = await this.api.get('/api/violations/coordinates');
      console.log('✅ Нарушения с координатами получены:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ Ошибка получения нарушений с координатами:', error);
      return { success: false, error: error.message };
    }
  }

  // Получение OSM зданий для карты
  async getOSMBuildings(latitude, longitude, radius = 1000) {
    try {
      console.log('🏢 Получение OSM зданий...');
      const response = await this.api.get('/api/osm/buildings', {
        params: { lat: latitude, lon: longitude, radius }
      });
      
      if (response.data.success) {
        console.log('✅ OSM здания получены:', response.data.buildings?.length || 0);
        return response.data;
      }
      return { success: false, error: 'No OSM buildings available' };
    } catch (error) {
      console.error('❌ Ошибка получения OSM зданий:', error);
      return { success: false, error: error.message };
    }
  }

  // Получение OSM городского контекста
  async getOSMUrbanContext(latitude, longitude, radius = 500) {
    try {
      console.log('🗺️ Получение OSM городского контекста...');
      const response = await this.api.get('/api/osm/urban-context', {
        params: { lat: latitude, lon: longitude, radius }
      });
      
      if (response.data.success) {
        console.log('✅ OSM контекст получен:', response.data.context);
        return response.data;
      }
      return { success: false, error: 'No OSM data available' };
    } catch (error) {
      console.error('❌ Ошибка получения OSM контекста:', error);
      return { success: false, error: error.message };
    }
  }

  // Проверка доступности OSM сервиса
  async checkOSMHealth() {
    try {
      const response = await this.api.get('/api/osm/health');
      return response.data;
    } catch (error) {
      console.error('Ошибка проверки OSM сервиса:', error);
      return { status: 'error', error: error.message };
    }
  }

  // Получение нарушений с OSM контекстом
  async getViolationsWithOSMContext() {
    try {
      const violations = await this.getViolationsWithCoordinates();
      
      if (violations.success && violations.data) {
        // Обогащаем каждое нарушение OSM данными
        const enrichedViolations = await Promise.all(
          violations.data.map(async (violation) => {
            if (violation.latitude && violation.longitude) {
              const osmContext = await this.getOSMUrbanContext(
                violation.latitude, 
                violation.longitude, 
                200
              );
              
              return {
                ...violation,
                osmContext: osmContext.success ? osmContext.context : null,
                zoneType: osmContext.success ? 
                  this.categorizeByOSMContext(osmContext.context) : 'unknown'
              };
            }
            return violation;
          })
        );
        
        return { success: true, data: enrichedViolations };
      }
      
      return violations;
    } catch (error) {
      console.error('Ошибка получения нарушений с OSM контекстом:', error);
      return { success: false, error: error.message };
    }
  }

  // Категоризация по OSM контексту
  categorizeByOSMContext(context) {
    if (!context) return 'unknown';
    
    const { buildings, amenities } = context;
    
    // Образовательные учреждения
    const educationAmenities = ['school', 'kindergarten', 'university', 'college'];
    if (amenities.some(a => educationAmenities.includes(a.amenity))) {
      return 'education_zone';
    }
    
    // Медицинские учреждения
    const healthAmenities = ['hospital', 'clinic', 'pharmacy', 'dentist'];
    if (amenities.some(a => healthAmenities.includes(a.amenity))) {
      return 'healthcare_zone';
    }
    
    // Торговые зоны
    const commercialAmenities = ['shop', 'mall', 'marketplace', 'restaurant'];
    if (amenities.some(a => commercialAmenities.includes(a.category))) {
      return 'commercial_zone';
    }
    
    // Жилые зоны
    const residentialBuildings = ['residential', 'apartments', 'house', 'dormitory'];
    if (buildings.some(b => residentialBuildings.includes(b.building_type))) {
      return 'residential_zone';
    }
    
    return 'general_zone';
  }

  // Генерация контекстных уведомлений
  async generateContextualAlert(violations, osmContext) {
    if (!violations || violations.length === 0) {
      return null;
    }
    
    const zoneType = this.categorizeByOSMContext(osmContext);
    const violationCount = violations.length;
    
    switch (zoneType) {
      case 'education_zone':
        return {
          type: 'warning',
          title: '⚠️ Школьная зона',
          message: `Обнаружено ${violationCount} нарушений в школьной зоне! Повышенная опасность для детей.`,
          priority: 'high'
        };
      case 'healthcare_zone':
        return {
          type: 'critical',
          title: '🚨 Медицинская зона',
          message: `Обнаружено ${violationCount} нарушений у медучреждения! Может препятствовать скорой помощи.`,
          priority: 'critical'
        };
      case 'residential_zone':
        return {
          type: 'info',
          title: '🏠 Жилая зона',
          message: `Обнаружено ${violationCount} нарушений в жилой зоне. Влияет на комфорт жителей.`,
          priority: 'medium'
        };
      case 'commercial_zone':
        return {
          type: 'warning',
          title: '🏪 Торговая зона',
          message: `Обнаружено ${violationCount} нарушений в торговой зоне. Может затруднить доступ покупателей.`,
          priority: 'medium'
        };
      default:
        return {
          type: 'info',
          title: '📍 Общая зона',
          message: `Зафиксировано ${violationCount} нарушений в данной области.`,
          priority: 'low'
        };
    }
  }

}

// Экспортируем единственный экземпляр
export default new ApiService();
