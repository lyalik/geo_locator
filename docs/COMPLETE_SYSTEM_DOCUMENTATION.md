# Geo Locator - Полная документация системы

## 📋 Обзор проекта

Geo Locator - это комплексная система для обнаружения и управления нарушениями с использованием искусственного интеллекта, геолокации и мобильных технологий. Система состоит из трех основных компонентов: backend API, веб-приложения для администрирования и мобильного приложения.

### 🎯 Основные возможности
- **Двойная система ИИ**: YOLO + Mistral AI для детекции нарушений
- **Геолокация**: Интеграция с российскими сервисами (Яндекс, 2GIS, Роскосмос, OSM)
- **Офлайн режим**: Сохранение данных без интернета с последующей синхронизацией
- **Push уведомления**: Реальное время оповещений через Expo
- **Админ панель**: Полное управление системой через веб-интерфейс
- **Оптимизация производительности**: Сжатие изображений и кэширование

---

## 🏗️ Архитектура системы

### Backend (Flask API)
- **Порт**: 5001
- **База данных**: PostgreSQL
- **Кэш**: Redis
- **Авторизация**: Flask-Login (сессионная)

### Frontend (React)
- **Порт**: 3000
- **Технологии**: React, Material-UI, Leaflet
- **API**: Axios с поддержкой cookies

### Mobile (React Native + Expo)
- **Платформы**: iOS, Android
- **Технологии**: Expo, React Navigation
- **Уведомления**: Expo Notifications

---

## 📱 Мобильное приложение
npx expo start --offline
### Основные экраны
1. **LoginScreen** - Авторизация пользователя
2. **CameraScreen** - Съемка и анализ нарушений
3. **MapScreen** - Карта с отображением нарушений
4. **ProfileScreen** - Профиль пользователя

### Ключевые сервисы

#### ApiService
```javascript
// Базовая конфигурация API
const API_BASE_URL = 'http://localhost:5001';

// Основные методы
- login(email, password)
- uploadViolation(formData)
- getViolations()
- getUserHistory()
```

#### OfflineStorageService
```javascript
// Офлайн функциональность
- savePhotoOffline(photoUri, location, metadata)
- syncOfflinePhotos(uploadFunction)
- getPendingPhotosCount()
- getStorageStats()
```

#### PerformanceOptimizer
```javascript
// Оптимизация производительности
- optimizeImage(imageUri, options)
- createThumbnail(imageUri, size)
- cacheAnalysisResult(imageUri, result)
- getCachedAnalysisResult(imageUri)
```

#### NotificationService
```javascript
// Push уведомления
- initializeNotifications()
- registerForPushNotifications()
- handleNotificationReceived(notification)
- cleanup()
```

### Функции CameraScreen

#### Офлайн режим
- Автоматическое определение состояния сети
- Сохранение фото локально при отсутствии интернета
- Индикатор статуса сети в UI
- Счетчик неотправленных фото
- Синхронизация при восстановлении связи

#### Оптимизация производительности
- Сжатие изображений перед отправкой
- Кэширование результатов анализа
- Оптимизация размеров изображений
- Создание превью для быстрого отображения

#### UX улучшения
- Анимация затвора при съемке
- Вибрация для тактильной обратной связи
- Tap-to-focus с анимированным индикатором
- Переключение вспышки
- Отображение GPS координат

### Зависимости
```json
{
  "@react-native-async-storage/async-storage": "2.2.0",
  "expo-camera": "~17.0.8",
  "expo-file-system": "~19.0.4",
  "expo-image-manipulator": "~13.0.5",
  "expo-location": "^19.0.7",
  "expo-network": "~8.0.5",
  "expo-notifications": "~0.30.0",
  "react-native-maps": "1.20.1"
}
```

---

## 🌐 Веб-приложение (Frontend)

### Основные компоненты

#### Dashboard
- Центральная панель управления
- Вкладки для всех функций системы
- Интерактивная карта с нарушениями
- Статистика и аналитика

#### AdminPanel
- Управление пользователями
- Управление нарушениями (CRUD операции)
- Фильтрация и поиск
- Массовые операции

#### InteractiveMap
- Отображение нарушений на карте
- Кластеризация маркеров
- Переключаемые слои (спутниковый, обычный)
- Детальная информация по клику

#### ViolationUploader & BatchViolationUploader
- Загрузка одиночных и пакетных нарушений
- Drag & drop интерфейс
- Прогресс-бары загрузки
- Опциональный геолокационный анализ

### Исправленная авторизация
```javascript
// Сессионная авторизация вместо JWT
const api = axios.create({
  baseURL: API_URL,
  withCredentials: true, // Включение cookies
  timeout: 120000
});

// Убраны Bearer токены
api.interceptors.request.use((config) => {
  // Cookies отправляются автоматически
  return config;
});
```

### Зависимости
```json
{
  "react": "^18.2.0",
  "@mui/material": "^5.14.1",
  "axios": "^1.4.0",
  "leaflet": "^1.9.4",
  "recharts": "^2.7.2"
}
```

---

## 🔧 Backend API

### Основные маршруты

#### Авторизация (`/auth`)
```python
POST /auth/login     # Вход в систему
POST /auth/register  # Регистрация
POST /auth/logout    # Выход
GET  /auth/me        # Текущий пользователь
```

#### Нарушения (`/api/violations`)
```python
GET    /list                    # Список всех нарушений
POST   /detect                  # Детекция нарушений в изображении
POST   /batch_detect           # Пакетная детекция
GET    /{id}                   # Получить нарушение
PUT    /{id}                   # Обновить нарушение
DELETE /{id}                   # Удалить нарушение
```

#### Админ API (`/admin`)
```python
GET    /users                  # Список пользователей
GET    /violations             # Список нарушений (админ)
DELETE /violations/{id}        # Удаление нарушения (админ)
GET    /analytics              # Аналитика системы
```

#### Уведомления (`/api/notifications`)
```python
GET  /preferences              # Настройки уведомлений
POST /preferences              # Обновить настройки
POST /save-push-token          # Сохранить push токен
POST /send-push                # Отправить push уведомление
GET  /stats                    # Статистика уведомлений
```

### Модели данных

#### User
```python
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(255))
    role = db.Column(db.String(50), default='user')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

#### Photo
```python
class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_path = db.Column(db.String(500))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    has_gps = db.Column(db.Boolean, default=False)
    location_method = db.Column(db.String(50))
    address_data = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

#### Violation
```python
class Violation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    photo_id = db.Column(db.Integer, db.ForeignKey('photos.id'))
    category = db.Column(db.String(100))
    confidence = db.Column(db.Float)
    bbox_data = db.Column(db.JSON)
    source = db.Column(db.String(50))  # 'yolo' или 'mistral_ai'
    status = db.Column(db.String(50), default='pending')
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

### Сервисы ИИ

#### YOLOViolationDetector
```python
# Детекция объектов с помощью YOLOv8
- detect_violations(image_path)
- process_detections(results)
- filter_violations(detections)
```

#### MistralAIService
```python
# Анализ изображений через Mistral AI
- analyze_image(image_path, prompt)
- detect_violations(image_path)
- generate_description(violations)
```

### Геолокационные сервисы

#### YandexMapsService
```python
- geocode(address)
- reverse_geocode(lat, lon)
- search_places(query, lat, lon)
- get_static_map(lat, lon, zoom)
```

#### DGISService
```python
- search_places(query, lat, lon)
- get_place_details(place_id)
- get_nearby_places(lat, lon, radius)
```

#### RoscosmosService
```python
- get_satellite_image(lat, lon, zoom, date)
- search_archive(bbox, date_from, date_to)
- get_image_metadata(image_id)
```

---

## 🔔 Push уведомления

### Тестирование системы
Результаты тестирования: **83.3% успешности (5/6 тестов)**

#### ✅ Работающие функции:
- Авторизация пользователей
- Сохранение push токенов
- Управление настройками уведомлений
- Отправка push уведомлений
- Статистика уведомлений

#### Интеграция с мобильным приложением
```javascript
// Инициализация в App.js
useEffect(() => {
  NotificationService.initializeNotifications();
  return () => NotificationService.cleanup();
}, []);

// Регистрация токена
const token = await NotificationService.registerForPushNotifications();
await ApiService.savePushToken(token);
```

---

## 📊 Производительность и оптимизация

### Мобильное приложение

#### Оптимизация изображений
- Максимальный размер: 1280px
- Качество сжатия: 80%
- Автоматическое изменение размера
- Конвертация в JPEG

#### Кэширование
- Результаты анализа кэшируются на 24 часа
- Лимит кэша: 50MB
- Автоматическая очистка старых записей
- Статистика использования кэша

#### Офлайн режим
- Локальное сохранение фото
- Метаданные и геолокация
- Автоматическая синхронизация
- Индикаторы состояния

### Backend

#### База данных
- PostgreSQL для основных данных
- Redis для кэширования
- Индексы для быстрого поиска
- Оптимизированные запросы

#### API оптимизация
- Пагинация результатов
- Фильтрация на уровне БД
- Сжатие ответов
- Кэширование частых запросов

---

## 🚀 Развертывание

### Требования к системе
- Python 3.8+
- Node.js 16+
- PostgreSQL 12+
- Redis 6+

### Backend
```bash
cd backend
pip install -r requirements.txt
flask db upgrade
python app.py
```

### Frontend
```bash
cd frontend
npm install
npm start
```

### Mobile
```bash
cd GeoLocatorMobile
npm install
expo start
```

### Docker (опционально)
```bash
docker-compose up -d
```

---

## 🔧 Конфигурация

### Переменные окружения
```env
# База данных
DATABASE_URL=postgresql://user:pass@localhost/geolocator
REDIS_URL=redis://localhost:6379/0

# API ключи
YANDEX_API_KEY=your_yandex_key
DGIS_API_KEY=your_2gis_key
ROSCOSMOS_API_KEY=your_roscosmos_key
MISTRAL_API_KEY=your_mistral_key

# Настройки приложения
SECRET_KEY=your_secret_key
FLASK_ENV=production
```

### Настройки мобильного приложения
```javascript
// config/api.js
export const API_CONFIG = {
  BASE_URL: 'https://your-domain.com',
  TIMEOUT: 120000,
  MAX_RETRIES: 3
};
```

---

## 📈 Мониторинг и логирование

### Логи
- Backend: `logs/backend.log`
- Frontend: `logs/frontend.log`
- Уровни: DEBUG, INFO, WARNING, ERROR

### Метрики
- Количество обработанных изображений
- Точность детекции нарушений
- Время ответа API
- Статистика push уведомлений

### Health Check
```bash
curl http://localhost:5001/health
```

---

## 🔒 Безопасность

### Авторизация
- Сессионная авторизация Flask-Login
- CSRF protection
- Роли пользователей (user, admin)
- Secure cookies

### API Security
- CORS настройки
- Rate limiting
- Input validation
- SQL injection protection

### Мобильная безопасность
- Secure storage для токенов
- Certificate pinning
- Encrypted local storage

---

## 🧪 Тестирование

### Backend тесты
```bash
python -m pytest tests/
```

### Frontend тесты
```bash
npm test
```

### Push уведомления
```bash
python test_push_notifications.py
```

### Интеграционные тесты
```bash
python test_full_integration.py
```

---

## 📚 API документация

### Swagger/OpenAPI
Доступна по адресу: `http://localhost:5001/docs`

### Примеры запросов

#### Детекция нарушений
```bash
curl -X POST http://localhost:5001/api/violations/detect \
  -F "file=@image.jpg" \
  -F "latitude=55.7558" \
  -F "longitude=37.6176"
```

#### Получение списка нарушений
```bash
curl -X GET "http://localhost:5001/api/violations/list?page=1&per_page=20"
```

---

## 🎯 Roadmap

### Ближайшие планы
- [ ] Улучшение точности ИИ детекции
- [ ] Добавление новых типов нарушений
- [ ] Интеграция с государственными системами
- [ ] Мобильное приложение для iOS

### Долгосрочные цели
- [ ] Машинное обучение на собранных данных
- [ ] Предиктивная аналитика
- [ ] Интеграция с IoT устройствами
- [ ] Blockchain для верификации данных

---

## 👥 Команда разработки

### Роли и ответственности
- **Backend Developer**: API, база данных, ИИ сервисы
- **Frontend Developer**: React приложение, UI/UX
- **Mobile Developer**: React Native приложение
- **DevOps Engineer**: Развертывание, мониторинг
- **QA Engineer**: Тестирование, качество

---

## 📞 Поддержка

### Контакты
- Email: support@geolocator.ru
- Telegram: @geolocator_support
- GitHub: github.com/geolocator/issues

### Документация
- API: `/docs`
- User Guide: `/user-guide`
- Admin Guide: `/admin-guide`

---

## 📄 Лицензия

MIT License - см. файл LICENSE для деталей.

---

*Документация обновлена: 16 сентября 2025 г.*
*Версия системы: 2.0.0*
