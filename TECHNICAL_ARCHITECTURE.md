# Техническая архитектура системы Geo Locator

## Обзор архитектуры

Geo Locator представляет собой многоуровневую систему для определения географических координат объектов на изображениях и видео с использованием искусственного интеллекта и интеграции с российскими геолокационными сервисами.

## Архитектурные принципы

### 1. Модульная архитектура
- Разделение на независимые сервисы
- Слабая связанность между компонентами
- Высокая когезия внутри модулей
- Возможность горизонтального масштабирования

### 2. Микросервисная ориентация
- Каждый сервис отвечает за конкретную функциональность
- REST API для межсервисного взаимодействия
- Независимое развертывание компонентов
- Отказоустойчивость через изоляцию сервисов

### 3. Многоисточниковая интеграция
- Агрегация данных из различных источников
- Взвешенное объединение результатов
- Fallback механизмы при недоступности сервисов
- Кэширование для оптимизации производительности

## Компоненты системы

### Backend (Python Flask)

#### Основные сервисы

##### 1. CoordinateDetector
**Файл**: `backend/services/coordinate_detector.py`

**Назначение**: Основной сервис для определения координат объектов на изображениях

**Функциональность**:
- Извлечение GPS данных из EXIF
- Интеграция с YOLO детектором объектов
- Поиск похожих изображений в базе данных
- Запросы к геолокационным API (Яндекс, 2ГИС)
- Взвешенное объединение результатов

**Ключевые методы**:
```python
def detect_coordinates_from_image(image_path, location_hint=None)
def batch_detect_coordinates(image_paths, location_hint=None)
def _extract_gps_from_exif(image_path)
def _get_coordinates_from_geolocation_services(location_hint)
def _find_similar_images(image_path)
def _combine_coordinate_sources(sources)
```

##### 2. VideoCoordinateDetector
**Файл**: `backend/services/video_coordinate_detector.py`

**Назначение**: Анализ видеофайлов для определения координат

**Функциональность**:
- Извлечение кадров из видео с настраиваемым интервалом
- Покадровый анализ координат
- Агрегация результатов по всему видео
- Статистика обнаруженных объектов
- Оценка времени обработки

**Ключевые методы**:
```python
def analyze_video(video_path, frame_interval=30, location_hint=None)
def extract_frames(video_path, frame_interval=30)
def estimate_processing_time(video_path, frame_interval=30)
def _aggregate_frame_results(frame_results)
def _calculate_object_statistics(detections)
```

##### 3. YOLOObjectDetector (переименован из YOLOViolationDetector)
**Файл**: `backend/services/yolo_violation_detector.py`

**Назначение**: Детекция геолокационно-релевантных объектов

**Функциональность**:
- Загрузка и инициализация YOLOv8 модели
- Детекция объектов на изображениях
- Классификация по геолокационным категориям
- Оценка релевантности для определения координат
- Создание аннотированных изображений

**Категории объектов**:
- Здания и архитектура
- Памятники и достопримечательности  
- Инфраструктурные объекты
- Транспортные средства
- Природные объекты
- Городская мебель
- Вывески и указатели

##### 4. Геолокационные сервисы

###### YandexMapsService
**Файл**: `backend/services/yandex_maps_service.py`
- Поиск мест и адресов
- Геокодирование и обратное геокодирование
- Статические карты
- Панорамы улиц

###### DGISService  
**Файл**: `backend/services/dgis_service.py`
- Поиск организаций
- Детальная информация о местах
- Поиск ближайших объектов

###### RoscosmosService
**Файл**: `backend/services/roscosmos_satellite_service.py`
- Официальные спутниковые данные Роскосмос
- Архивный поиск снимков
- Интеграция с ScanEx (Kosmosnimki)

###### YandexSatelliteService
**Файл**: `backend/services/yandex_satellite_service.py`
- Спутниковые снимки Яндекс
- Гибридные карты
- Многоуровневое масштабирование

##### 5. GeoAggregatorService
**Файл**: `backend/services/geo_aggregator_service.py`

**Назначение**: Агрегация данных из всех геолокационных источников

**Функциональность**:
- Параллельные запросы к различным API
- Взвешенное объединение результатов
- Обработка ошибок и fallback логика
- Статистика успешности источников

#### API Endpoints

##### Coordinate API
**Файл**: `backend/routes/coordinate_api.py`

**Основные эндпоинты**:

```python
POST /api/coordinates/detect
# Определение координат для одного изображения

POST /api/coordinates/batch_detect  
# Пакетное определение координат

POST /api/coordinates/video/analyze
# Анализ видеофайла

GET /api/coordinates/video/estimate_time
# Оценка времени обработки видео

GET /api/coordinates/statistics
# Статистика детекции

GET /api/coordinates/objects/<photo_id>
# Получение объектов по ID фотографии
```

### Frontend (React)

#### Основные компоненты

##### 1. Dashboard
**Файл**: `frontend/src/components/Dashboard.js`
- Центральная панель управления
- Вкладки для различных функций
- Интеграция всех компонентов системы

##### 2. InteractiveMap
**Файл**: `frontend/src/components/InteractiveMap.js`
- Отображение объектов на карте
- Переключение слоев (спутник, OSM)
- Фильтрация и кластеризация
- Интерактивные маркеры

##### 3. CoordinateUploader (новый компонент)
- Загрузка изображений для анализа координат
- Отображение результатов детекции
- Визуализация найденных объектов

##### 4. VideoAnalyzer (новый компонент)  
- Загрузка и анализ видеофайлов
- Прогресс обработки
- Результаты покадрового анализа

## База данных (PostgreSQL)

### Основные таблицы

#### Photos
```sql
CREATE TABLE photos (
    id SERIAL PRIMARY KEY,
    file_path VARCHAR(500) NOT NULL,
    original_filename VARCHAR(255),
    lat DECIMAL(10, 8),
    lon DECIMAL(11, 8),
    address_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER REFERENCES users(id)
);
```

#### DetectedObjects (новая таблица)
```sql
CREATE TABLE detected_objects (
    id SERIAL PRIMARY KEY,
    photo_id INTEGER REFERENCES photos(id),
    category VARCHAR(100) NOT NULL,
    confidence DECIMAL(5, 4),
    bbox_data JSONB,
    coordinates JSONB,
    relevance_score DECIMAL(5, 4),
    source VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Videos (новая таблица)
```sql
CREATE TABLE videos (
    id SERIAL PRIMARY KEY,
    file_path VARCHAR(500) NOT NULL,
    original_filename VARCHAR(255),
    duration DECIMAL(10, 2),
    frame_count INTEGER,
    analysis_results JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER REFERENCES users(id)
);
```

#### CoordinateSources (новая таблица)
```sql
CREATE TABLE coordinate_sources (
    id SERIAL PRIMARY KEY,
    photo_id INTEGER REFERENCES photos(id),
    source_type VARCHAR(50) NOT NULL,
    coordinates JSONB,
    confidence DECIMAL(5, 4),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Интеграции

### Внешние API

#### Российские спутниковые сервисы
1. **Роскосмос Геопортал**
   - Официальные спутниковые данные
   - Архивные снимки
   - Высокое разрешение (1-3м)

2. **ScanEx (Kosmosnimki)**
   - Публичный доступ к спутниковым данным
   - Различные спутники (Resurs-P, Kanopus-V)
   - API для поиска и загрузки

3. **Яндекс Спутник**
   - Статические спутниковые карты
   - Гибридные слои
   - Актуальные данные

#### Геолокационные сервисы
1. **Яндекс.Карты API**
   - Геокодирование
   - Поиск организаций
   - Панорамы улиц

2. **2ГИС API**
   - Детальная информация о местах
   - Поиск организаций
   - Навигационные данные

3. **OpenStreetMap**
   - Открытые картографические данные
   - Информация о зданиях
   - Дополнительный источник данных

### AI/ML интеграции

#### YOLOv8 (Ultralytics)
- Предобученная модель для детекции объектов
- Кастомизация под геолокационные задачи
- Оптимизация производительности

#### Mistral AI
- Углубленный анализ изображений
- Описание объектов на естественном языке
- Дополнительная валидация результатов

## Безопасность

### Аутентификация и авторизация
- Flask-Login для сессионного управления
- Хеширование паролей (bcrypt)
- CSRF защита
- Валидация загружаемых файлов

### API Security
- Rate limiting для предотвращения злоупотреблений
- Валидация входных данных
- Санитизация файловых путей
- Логирование безопасности

### Конфиденциальность данных
- Шифрование API ключей
- Безопасное хранение учетных данных
- Соблюдение GDPR принципов

## Производительность и масштабирование

### Кэширование
- Redis для кэширования результатов API
- Кэширование спутниковых снимков
- Оптимизация повторных запросов

### Асинхронная обработка
- Celery для фоновых задач
- Очереди для обработки видео
- Неблокирующие операции

### Оптимизация базы данных
- Индексы для геопространственных запросов
- Партиционирование больших таблиц
- Оптимизация запросов

## Мониторинг и логирование

### Логирование
- Структурированные логи (JSON)
- Различные уровни логирования
- Ротация логов

### Метрики
- Производительность API
- Статистика использования
- Мониторинг ошибок

### Здоровье системы
- Health check endpoints
- Мониторинг доступности сервисов
- Алерты при сбоях

## Развертывание

### Docker контейнеризация
- Отдельные контейнеры для сервисов
- Docker Compose для локальной разработки
- Оптимизированные образы

### CI/CD Pipeline
- Автоматическое тестирование
- Сборка и развертывание
- Откат при ошибках

### Конфигурация окружений
- Переменные окружения для настроек
- Различные конфигурации для dev/prod
- Секретное управление

## Будущие улучшения

### Планируемые функции
1. Реальное время отслеживания
2. AR наложения
3. Мобильное приложение
4. Машинное обучение для улучшения точности
5. Интеграция с IoT устройствами

### Техническое развитие
1. Микросервисная архитектура
2. Kubernetes оркестрация
3. GraphQL API
4. Машинное обучение на краю (Edge ML)
5. Блокчейн для верификации данных
