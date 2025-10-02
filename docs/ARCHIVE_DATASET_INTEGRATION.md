# Интеграция архивного датасета фото зданий

## Обзор функциональности

Архивный датасет фото зданий и сооружений интегрирован в систему Geo Locator для повышения точности определения координат и улучшения анализа объектов. Система использует архивные данные в двух основных разделах:

### 🎯 1. Раздел "Анализ координат"

**Назначение:** Повышение точности определения местоположения через сравнение с архивными фото

**Как работает:**
- При загрузке фото система автоматически ищет похожие здания в архиве
- Сравнивает архитектурные особенности, цветовые характеристики, текстуры
- Использует координаты из архивных метаданных для уточнения местоположения
- Архивный поиск имеет приоритет 3 (после GPS и геолокации, но до Google Vision)

**Приоритеты источников координат:**
1. GPS метаданные (приоритет 1)
2. Геолокационные сервисы (приоритет 2)  
3. **🏛️ Архивные фото (приоритет 3)**
4. Google Vision OCR (приоритет 4)
5. Google Gemini анализ (приоритет 5)
6. Поиск похожих изображений (приоритет 6)

### 🤖 2. Раздел "Анализ ИИ"

**Назначение:** Улучшение распознавания нарушений и анализа объектов через исторический контекст

**Как работает:**
- Ищет похожие здания в архиве (порог схожести 0.6)
- Создает контекст на основе архивных метаданных
- Улучшает промпты для Google Gemini с историческими данными
- Предоставляет информацию о типах зданий, архитектурных стилях, историческом контексте

## Структура архивного датасета

```
backend/data/archive_photos/
├── buildings/          # Жилые, офисные, торговые здания
├── landmarks/          # Достопримечательности и памятники  
├── streets/            # Уличные виды и перекрестки
└── metadata/           # JSON файлы с метаданными
```

## Формат метаданных

Каждое архивное фото должно иметь соответствующий JSON файл:

```json
{
  "filename": "building_001.jpg",
  "coordinates": {
    "latitude": 55.7558,
    "longitude": 37.6176
  },
  "address": "Красная площадь, 1, Москва",
  "building_type": "historical",
  "architectural_style": "russian_baroque", 
  "construction_year": 1491,
  "description": "Собор Василия Блаженного",
  "tags": ["собор", "историческое здание", "красная площадь"],
  "photo_date": "2023-08-15",
  "photographer": "archive_team",
  "quality_score": 0.95
}
```

## Технические детали интеграции

### ArchivePhotoService

**Основные методы:**
- `find_similar_buildings()` - поиск похожих зданий по изображению
- `get_coordinates_from_similar_buildings()` - получение координат из архива
- `search_by_architectural_features()` - поиск по архитектурным особенностям
- `get_building_metadata()` - получение метаданных здания

**Алгоритм сравнения:**
- Извлечение цветовых гистограмм (BGR каналы)
- Анализ текстурных признаков (градиенты Sobel)
- Статистические характеристики (среднее, стандартное отклонение)
- Косинусное сходство между векторами признаков

### Интеграция в coordinate_detector.py

```python
# Шаг 6: Поиск в архивных фото
archive_coords = self._find_archive_coordinates(image_path)

# Объединение всех источников координат
final_coordinates = self._combine_coordinate_sources(
    image_coords, geo_result, similarity_coords, objects,
    google_ocr_coords, google_geo_coords, archive_coords
)
```

### Интеграция в Google Vision Service

```python
# Улучшенный анализ нарушений с архивным контекстом
def analyze_violations_with_archive_context(self, image_path, custom_prompt=None):
    # Поиск похожих зданий в архиве
    similar_buildings = self.archive_service.find_similar_buildings(image_path)
    
    # Создание контекста из архивных данных
    archive_context = self._create_archive_context(similar_buildings)
    
    # Улучшенный промпт с историческим контекстом
    enhanced_prompt = self._create_enhanced_violation_prompt(archive_context)
```

## Добавление новых архивных фото

### 1. Подготовка файлов

Поместите фото в соответствующую категорию:
- `buildings/` - для обычных зданий
- `landmarks/` - для достопримечательностей  
- `streets/` - для уличных видов

### 2. Создание метаданных

Создайте JSON файл в папке `metadata/` с именем `{filename_without_extension}.json`

### 3. Автоматическая индексация

Система автоматически загружает новые файлы при инициализации `ArchivePhotoService`

### 4. Программное добавление

```python
archive_service = ArchivePhotoService()
metadata = {
    "coordinates": {"latitude": 55.7558, "longitude": 37.6176},
    "address": "Адрес здания",
    "building_type": "residential",
    "architectural_style": "modern",
    "description": "Описание здания"
}
archive_service.add_building_to_archive(image_path, metadata)
```

## Мониторинг и отладка

### Логи системы

```
🏛️ Archive Photo Service initialized with 15 photos
🔍 Found archive match: Собор Василия Блаженного  
🏛️ Enhanced violation analysis with 2 archive matches
```

### API ответы

В разделе "Анализ координат":
```json
{
  "coordinate_sources": {
    "archive_photo_match": true
  },
  "coordinates": {
    "source": "archive_photo_match",
    "matched_building": {
      "description": "Собор Василия Блаженного"
    }
  }
}
```

В разделе "Анализ ИИ":
```json
{
  "archive_context": {
    "building_types": ["historical"],
    "architectural_styles": ["russian_baroque"]
  },
  "similar_buildings": [...]
}
```

## Тестирование функциональности

### 1. Тестовые архивные фото

В системе предустановлены тестовые метаданные:
- `sample_building_001.json` - Собор Василия Блаженного
- `sample_landmark_001.json` - Спасская башня  
- `sample_street_001.json` - Никольская улица

### 2. Проверка интеграции

1. Загрузите фото здания в раздел "Анализ координат"
2. Проверьте в ответе API флаг `archive_photo_match: true`
3. Загрузите фото в раздел "Анализ ИИ" 
4. Убедитесь в наличии `archive_context` в результатах

### 3. Статистика архива

```python
archive_service = ArchivePhotoService()
stats = archive_service.get_archive_statistics()
print(f"Всего фото: {stats['total_photos']}")
```

## Преимущества использования

### Для определения координат:
- **Историческая точность** - проверенные координаты известных объектов
- **Архитектурный контекст** - понимание региональных особенностей
- **Повышение точности** - дополнительный источник геоданных

### Для анализа ИИ:
- **Контекстное понимание** - знание исторического фона объектов
- **Улучшенная классификация** - определение типов зданий по архивным аналогам  
- **Качественный анализ** - учет архитектурных особенностей региона

Архивный датасет значительно расширяет возможности системы Geo Locator, обеспечивая более точное определение координат и глубокий анализ объектов с учетом исторического и архитектурного контекста.
