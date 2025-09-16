import axios from 'axios';
import { Platform } from 'react-native';

// Конфигурация API
const API_BASE_URL = Platform.OS === 'web' && typeof window !== 'undefined' && window.location?.hostname === 'localhost'
  ? 'http://localhost:5001'  // Веб-версия
  : 'http://192.168.1.67:5001'; // Мобильная версия

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
        'Content-Type': 'multipart/form-data',
      },
    });
    
    console.log('✅ ApiService инициализирован с baseURL:', this.api.defaults.baseURL);

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
   * Детекция нарушений на изображении
   * @param {FormData} formData - Данные формы с изображением и координатами
   * @returns {Promise} Результат анализа
   */
  async detectViolation(formData) {
    try {
      console.log('🔄 Начинаем анализ нарушений...');
      console.log('📡 API Base URL:', this.api.defaults.baseURL);
      console.log('📝 FormData содержит:', Array.from(formData.keys()));
      
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
   * @returns {Promise} История загрузок
   */
  async getUserHistory(userId = null) {
    try {
      const params = userId ? { user_id: userId } : {};
      const response = await this.api.get('/api/violations/history', { params });
      return response.data;
    } catch (error) {
      console.error('Ошибка получения истории:', error);
      throw error;
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
}

// Экспортируем единственный экземпляр
export default new ApiService();
