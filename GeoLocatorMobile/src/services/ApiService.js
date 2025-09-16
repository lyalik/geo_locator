import axios from 'axios';

// Конфигурация API
const API_BASE_URL = 'http://192.168.1.67:5001'; // Backend работает на порту 5001
// Для веб-версии используйте localhost:
// const API_BASE_URL = 'http://localhost:5001';

class ApiService {
  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000, // 30 секунд для анализа изображений
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

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
      const response = await this.api.post('/api/violations/detect', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      console.error('Ошибка детекции нарушений:', error);
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
      const response = await this.api.get('/api/violations/list', { params });
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
      const response = await this.api.get('/health', { timeout: 5000 });
      return {
        online: true,
        status: response.status,
        message: 'Сервер доступен',
      };
    } catch (error) {
      console.log('Server status check failed:', error.message);
      return {
        online: false,
        status: error.response?.status || 0,
        message: error.message || 'Сервер недоступен',
      };
    }
  }

  /**
   * Авторизация пользователя
   * @param {string} email - Email пользователя
   * @param {string} password - Пароль
   * @returns {Promise} Результат авторизации
   */
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
      return {
        success: true,
        user: response.data.user,
        token: response.data.token || `session_${response.data.user?.id}_${Date.now()}`
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
      return {
        success: true,
        user: response.data.user,
        token: response.data.token || `session_${response.data.user?.id}_${Date.now()}`
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
