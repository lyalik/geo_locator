# 🖼️ УСТАНОВКА CLIP IMAGE SIMILARITY

## ⚠️ ВАЖНО: Порядок установки

Из-за конфликтов зависимостей между `numpy 2.x` и `faiss-cpu`, необходимо соблюдать **строгий порядок** установки.

---

## 📋 ВАРИАНТ 1: Чистая установка (рекомендуется)

### Шаг 1: Создание виртуального окружения

```bash
cd /home/denis/Documents/Hackathon_2025/geo_locator/backend

# Создаем новое виртуальное окружение
python3 -m venv venv

# Активируем
source venv/bin/activate

# Обновляем pip
pip install --upgrade pip
```

### Шаг 2: Установка зависимостей

```bash
# Устанавливаем ВСЕ зависимости из requirements.txt
pip install -r requirements.txt
```

**Примечание:** Файл `requirements.txt` уже содержит правильные версии:
- `numpy>=1.26.0,<2.0` - совместимая с faiss
- `opencv-python==4.10.0.84` - совместимая с numpy 1.26
- `opencv-python-headless==4.10.0.84` - для EasyOCR

---

## 📋 ВАРИАНТ 2: Обновление существующего окружения

### Если уже установлены другие версии:

```bash
cd /home/denis/Documents/Hackathon_2025/geo_locator/backend
source venv/bin/activate

# Шаг 1: Удаляем проблемные пакеты
pip uninstall opencv-python-headless -y

# Шаг 2: Устанавливаем правильную версию numpy
pip install "numpy>=1.26.0,<2.0" --force-reinstall

# Шаг 3: Устанавливаем opencv
pip install "opencv-python==4.10.0.84"
pip install "opencv-python-headless==4.10.0.84"

# Шаг 4: Устанавливаем CLIP и FAISS
pip install open-clip-torch==2.24.0
pip install faiss-cpu==1.8.0
pip install sentence-transformers==2.7.0
```

---

## 🔧 ПРОВЕРКА УСТАНОВКИ

### Проверьте версии:

```bash
python -c "import numpy; print(f'numpy: {numpy.__version__}')"
python -c "import faiss; print(f'faiss: OK')"
python -c "import open_clip; print(f'open-clip: OK')"
python -c "import cv2; print(f'opencv: {cv2.__version__}')"
```

**Ожидаемый вывод:**
```
numpy: 1.26.4
faiss: OK
open-clip: OK
opencv: 4.10.0.84
```

---

## 🏗️ ПОСТРОЕНИЕ CLIP ИНДЕКСА

После установки зависимостей:

```bash
cd /home/denis/Documents/Hackathon_2025/geo_locator/backend
python build_clip_index.py
```

**Ожидаемый вывод:**
```
🚀 Starting CLIP index building...
📊 Found 56 photos with coordinates in database
✅ 56 photos have valid file paths
🤖 Loading CLIP model: ViT-B/32
✅ CLIP model loaded on cpu
🏗️ Building CLIP index from 56 photos...
Processed 56 images...
✅ Built index with 56 images
💾 Saved index to data/clip_cache/embeddings.pkl
🎉 Successfully built CLIP index with 56 images!

📊 Index statistics:
   Total images: 56
   Dimension: 512
   Model: ViT-B/32
   Device: cpu
   Cache exists: True
```

---

## 🐛 УСТРАНЕНИЕ ПРОБЛЕМ

### Проблема 1: `numpy.core.multiarray failed to import`

**Причина:** Установлена numpy 2.x, несовместимая с faiss-cpu

**Решение:**
```bash
pip install "numpy>=1.26.0,<2.0" --force-reinstall
```

### Проблема 2: `opencv-python-headless requires numpy>=2`

**Причина:** Установлена новая версия opencv-python-headless

**Решение:**
```bash
pip uninstall opencv-python-headless -y
pip install "opencv-python-headless==4.10.0.84"
```

### Проблема 3: `ImportError: cannot import name 'create_app'`

**Причина:** Исправлено в `build_clip_index.py`

**Решение:** Используйте обновленную версию скрипта (уже исправлено)

### Проблема 4: `cannot identify image file` для видео

**Причина:** В БД есть видеофайлы, CLIP работает только с изображениями

**Решение:** Это нормально, видео пропускаются автоматически

---

## 📦 СПИСОК НОВЫХ ЗАВИСИМОСТЕЙ

Добавлены в `requirements.txt`:

```txt
# CLIP and Vector Search (Image Similarity)
open-clip-torch==2.24.0  # OpenCLIP for image embeddings
faiss-cpu==1.8.0  # Facebook AI Similarity Search
sentence-transformers==2.7.0  # For text embeddings
scikit-learn>=1.0.0  # Required by sentence-transformers
timm>=0.9.0  # Required by open-clip-torch

# Важные ограничения версий
numpy>=1.26.0,<2.0  # КРИТИЧНО для faiss-cpu
opencv-python==4.10.0.84
opencv-python-headless==4.10.0.84
```

---

## 🔄 ОБНОВЛЕНИЕ ИНДЕКСА

### Автоматическое обновление (в будущем):

При добавлении новых фото индекс будет обновляться автоматически.

### Ручное обновление:

```bash
cd /home/denis/Documents/Hackathon_2025/geo_locator/backend
python build_clip_index.py
```

Это пересоздаст индекс со всеми фотографиями из базы данных.

---

## 📊 РАЗМЕР ДАННЫХ

- **CLIP модель:** ~350 MB (загружается автоматически)
- **FAISS индекс:** ~2 KB на изображение
- **Для 56 изображений:** ~112 KB
- **Для 1000 изображений:** ~2 MB

---

## 🚀 ЗАПУСК СИСТЕМЫ

После установки и построения индекса:

```bash
cd /home/denis/Documents/Hackathon_2025/geo_locator
./start_demo.sh
```

Система автоматически загрузит CLIP индекс при первом запросе.

---

## ✅ ГОТОВО!

CLIP Image Similarity полностью интегрирован и готов к использованию! 🎉
