# 📍 Документация геолокационной системы Geo Locator

## 🎯 Обзор системы

Комплексная система геолокации, объединяющая множественные источники данных для максимально точного определения местоположения объектов по фотографиям.

### Основные компоненты:

1. **Yandex Maps API** - поиск мест, геокодирование, панорамы
2. **2GIS API** - детальная информация об организациях и объектах  
3. **Роскосмос спутниковые данные** - официальные российские спутниковые снимки
4. **Яндекс Спутник API** - высококачественные спутниковые изображения
5. **База данных изображений** - собственная коллекция с геотегами
6. **EXIF анализатор** - извлечение GPS координат из метаданных
7. **Агрегатор результатов** - объединение данных из всех источников

## 🔧 Архитектура системы

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend UI   │───▶│   Geo API        │───▶│  Geo Aggregator │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        │
                       ┌────────────────────────────────┼────────────────────────────────┐
                       │                                │                                │
                       ▼                                ▼                                ▼
            ┌─────────────────┐              ┌─────────────────┐              ┌─────────────────┐
            │  Yandex Maps    │              │     2GIS API    │              │   Roscosmos     │
            │    Service      │              │    Service      │              │   Satellite     │
            └─────────────────┘              └─────────────────┘              └─────────────────┘
                       │                                │                                │
                       └────────────────────────────────┼────────────────────────────────┘
                                                        │
                                              ┌─────────────────┐
                                              │  Yandex Satellite│
                                              │    Service      │
                                              └─────────────────┘
                       │                                │                                │
                       └────────────────────────────────┼────────────────────────────────┘
                                                        │
                                                        ▼
                                              ┌─────────────────┐
                                              │  Image Database │
                                              │    Service      │
                                              └─────────────────┘
                                                        │
                                                        ▼
                                              ┌─────────────────┐
                                              │   PostgreSQL    │
                                              │   Database      │
                                              └─────────────────┘
```

## 🚀 API Endpoints

### Основные endpoints геолокации:

#### `POST /api/geo/locate`
Главный endpoint для определения местоположения изображения.

**Параметры:**
- `image` (file) - изображение для анализа
- `location_hint` (string, optional) - подсказка о местоположении
- `description` (string, optional) - описание изображения

**Ответ:**
```json
{
  "success": true,
  "final_location": {
    "coordinates": {"latitude": 55.7558, "longitude": 37.6176},
    "source": "exif_gps",
    "confidence": 0.95
  },
  "confidence_score": 0.95,
  "sources_used": ["exif_gps", "image_match"],
  "recommendations": ["Высокая уверенность в определении местоположения"]
}
```

#### `GET /api/geo/search/places`
Поиск мест через Yandex Maps и 2GIS.

**Параметры:**
- `q` (string) - поисковый запрос
- `lat`, `lon` (float, optional) - координаты центра поиска
- `radius` (int, optional) - радиус поиска в метрах
- `source` (string, optional) - источник: 'yandex', 'dgis', 'all'

#### `GET /api/geo/geocode`
Геокодирование адреса в координаты.

**Параметры:**
- `address` (string) - адрес для геокодирования
- `source` (string, optional) - 'yandex' или 'dgis'

#### `GET /api/geo/reverse-geocode`
Обратное геокодирование - координаты в адрес.

**Параметры:**
- `lat`, `lon` (float) - координаты
- `source` (string, optional) - 'yandex' или 'dgis'

#### `GET /api/geo/images/search`
Поиск изображений в базе данных.

**Параметры:**
- `q` (string, optional) - текстовый поиск
- `lat`, `lon` (float, optional) - поиск по координатам
- `radius` (int, optional) - радиус поиска
- `has_gps` (bool, optional) - фильтр по наличию GPS
- `city` (string, optional) - фильтр по городу

#### `GET /api/geo/nearby`
Поиск ближайших мест определенной категории.

**Параметры:**
- `lat`, `lon` (float) - координаты центра
- `category` (string, optional) - категория мест
- `radius` (int, optional) - радиус поиска

## 🔑 Настройка API ключей

В файле `.env` необходимо указать:

```bash
# Yandex Maps API
YANDEX_API_KEY=

# 2GIS API  
DGIS_API_KEY=

# Роскосмос спутниковые данные
ROSCOSMOS_API_KEY=your_roscosmos_api_key

# Яндекс Спутник (использует тот же ключ что и Yandex Maps)
# YANDEX_API_KEY уже указан выше

# База данных
POSTGRES_USER=postgres
POSTGRES_PASSWORD=
POSTGRES_DB=geo_locator
POSTGRES_HOST=localhost
```

## 📊 Алгоритм определения местоположения

### 1. Извлечение EXIF GPS (приоритет: 1.0)
- Анализ метаданных изображения
- Извлечение GPS координат, если доступны
- Максимальная точность при наличии данных

### 2. Поиск в базе изображений (приоритет: 0.9)
- Сравнение с существующими изображениями
- Поиск по координатам в радиусе 1км
- Учет визуального сходства (будущая функция)

### 3. Сопоставление с российскими спутниковыми снимками (приоритет: 0.8)
- Получение данных через Роскосмос и Яндекс Спутник
- Сравнение изображений через CV алгоритмы
- Подтверждение местоположения российскими источниками

### 4. Поиск через внешние API (приоритет: 0.7)
- Yandex Maps: поиск по описанию места
- 2GIS: детальная информация об объектах
- Геокодирование подсказок пользователя

### 5. Агрегация результатов
- Взвешенное усреднение координат
- Расчет итоговой уверенности
- Генерация рекомендаций

## 🗄️ База данных изображений

### Модель GeoImage

```sql
CREATE TABLE geo_images (
    id UUID PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_hash VARCHAR(64) UNIQUE NOT NULL,
    
    -- Геолокация
    latitude FLOAT,
    longitude FLOAT,
    altitude FLOAT,
    
    -- Метаданные
    width INTEGER,
    height INTEGER,
    camera_make VARCHAR(100),
    camera_model VARCHAR(100),
    
    -- Адресная информация  
    address TEXT,
    city VARCHAR(100),
    region VARCHAR(100),
    country VARCHAR(100),
    
    -- Статус обработки
    processed BOOLEAN DEFAULT FALSE,
    has_gps BOOLEAN DEFAULT FALSE,
    geo_source VARCHAR(50), -- 'exif', 'manual', 'api_match'
    
    -- Временные метки
    date_taken TIMESTAMP,
    date_uploaded TIMESTAMP DEFAULT NOW(),
    date_modified TIMESTAMP DEFAULT NOW()
);
```

### Основные операции:

1. **Добавление изображения** - автоматическое извлечение метаданных
2. **Поиск похожих** - по координатам и визуальному сходству  
3. **Обновление геолокации** - ручная корректировка координат
4. **Создание миниатюр** - для быстрого просмотра

## 🎨 Интеграция с внешними сервисами

### Yandex Maps API

**Возможности:**
- Поиск организаций и достопримечательностей
- Геокодирование и обратное геокодирование
- Статические карты с метками
- Панорамы улиц (Street View)

**Лимиты:** 
- 25,000 запросов/день (бесплатный план)
- 50 запросов/секунду

### 2GIS API

**Возможности:**
- Детальная информация об организациях
- Рейтинги, отзывы, фотографии
- Рабочие часы, контакты
- Категории и рубрики

**Лимиты:**
- 10,000 запросов/день (бесплатный план)
- 10 запросов/секунду

### Роскосмос спутниковые данные

**Возможности:**
- Официальные российские спутниковые снимки
- Данные спутников Ресурс-П (1-3м), Канопус-В (2.5м)
- Архивные снимки с фильтрацией по облачности
- Покрытие территории России и сопредельных государств

**Лимиты:**
- Зависят от API ключа и тарифного плана
- Открытый доступ через ScanEx (Космоснимки)

### Яндекс Спутник

**Возможности:**
- Высококачественные спутниковые снимки
- Гибридные карты (спутник + подписи)
- Статические изображения до 650x450 пикселей
- Регулярные обновления снимков

**Лимиты:**
- Использует лимиты Yandex Maps API
- Максимальный zoom: 17
- Размер изображения ограничен API

## 📈 Метрики качества

### Показатели точности:

1. **GPS Accuracy** - точность GPS координат из EXIF
2. **Match Confidence** - уверенность в сопоставлении
3. **Source Reliability** - надежность источника данных
4. **Aggregation Score** - итоговая оценка качества

### Мониторинг:

```python
# Получение статистики
GET /api/geo/statistics

{
  "total_images": 1250,
  "images_with_gps": 890,
  "gps_coverage": 71.2,
  "available_services": {
    "yandex_maps": true,
    "dgis": true,
    "roscosmos_satellite": true,
    "yandex_satellite": true,
    "image_database": true
  }
}
```

## 🔧 Настройка и развертывание

### 1. Установка зависимостей

```bash
# Системные пакеты
sudo apt-get install postgresql postgis gdal-bin

# Python пакеты
pip install -r requirements.txt
```

### 2. Настройка базы данных

```bash
# Создание базы данных
createdb geo_locator

# Включение PostGIS расширения
psql geo_locator -c "CREATE EXTENSION postgis;"
```

### 3. Инициализация таблиц

```python
from services.image_database_service import ImageDatabaseService
service = ImageDatabaseService()
# Таблицы создаются автоматически
```

### 4. Запуск сервиса

```bash
# Запуск backend
python app.py

# Проверка здоровья системы
curl http://localhost:5000/api/geo/health
```

## 🚀 Примеры использования

### Python клиент:

```python
import requests

# Загрузка изображения для геолокации
with open('photo.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:5000/api/geo/locate',
        files={'image': f},
        data={
            'location_hint': 'Москва, Красная площадь',
            'description': 'Фотография Кремля'
        },
        headers={'Authorization': 'Bearer <token>'}
    )

result = response.json()
print(f"Coordinates: {result['final_location']['coordinates']}")
print(f"Confidence: {result['confidence_score']}")
```

### JavaScript клиент:

```javascript
const formData = new FormData();
formData.append('image', fileInput.files[0]);
formData.append('location_hint', 'Санкт-Петербург');

fetch('/api/geo/locate', {
    method: 'POST',
    body: formData,
    headers: {
        'Authorization': `Bearer ${token}`
    }
})
.then(response => response.json())
.then(data => {
    console.log('Location:', data.final_location.coordinates);
    console.log('Sources used:', data.sources_used);
});
```

## 🔍 Отладка и мониторинг

### Логирование:

Все сервисы используют стандартное Python логирование:

```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

### Основные лог-сообщения:

- `GPS coordinates found in EXIF data` - найдены GPS в EXIF
- `Found N similar images in database` - найдены похожие изображения
- `Satellite match score: X` - оценка сопоставления со спутником
- `Geolocation completed. Success: X, Confidence: Y` - итог геолокации

### Проверка состояния:

```bash
# Проверка всех сервисов
curl http://localhost:5000/api/geo/health

# Статистика базы изображений  
curl http://localhost:5000/api/geo/statistics
```

## 🎯 Рекомендации по использованию

### Для максимальной точности:

1. **Используйте изображения с GPS** - включите геотеги в настройках камеры
2. **Добавляйте описания** - указывайте примерное местоположение
3. **Пополняйте базу** - загружайте больше изображений с известными координатами
4. **Проверяйте результаты** - корректируйте неточные определения

### Ограничения системы:

1. **Качество EXIF** - не все камеры записывают точные GPS координаты
2. **API лимиты** - ограничения внешних сервисов на количество запросов
3. **Покрытие спутников** - российские сервисы лучше покрывают территорию РФ
4. **Визуальное сходство** - алгоритмы CV требуют дальнейшего развития

## 📚 Дополнительные ресурсы

- [Yandex Maps API Documentation](https://yandex.ru/dev/maps/)
- [2GIS API Documentation](https://docs.2gis.com/)
- [Геопортал Роскосмоса](https://gptl.ru/)
- [ScanEx Космоснимки](https://maps.kosmosnimki.ru/)
- [PostGIS Documentation](https://postgis.net/documentation/)
- [OpenCV Python Documentation](https://docs.opencv.org/)
