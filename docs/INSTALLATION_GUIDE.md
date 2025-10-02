# 🚀 **GEO LOCATOR - Руководство по установке**

## 📋 **Системные требования**

### **Минимальные требования:**
- **ОС:** Ubuntu 20.04+ / macOS 10.15+ / Windows 10+
- **Python:** 3.8+
- **Node.js:** 16.0+
- **PostgreSQL:** 12+
- **Redis:** 6.0+
- **RAM:** 8GB (рекомендуется 16GB)
- **Диск:** 10GB свободного места

### **Рекомендуемые требования:**
- **CPU:** 4+ ядра
- **GPU:** NVIDIA с CUDA (опционально, для ускорения YOLO)
- **RAM:** 16GB+
- **SSD:** для лучшей производительности

---

## 🔧 **Установка системных зависимостей**

### **Ubuntu/Debian:**
```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Python и pip
sudo apt install python3.8 python3-pip python3-venv python3-dev -y

# Node.js и npm
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y

# PostgreSQL
sudo apt install postgresql postgresql-contrib postgresql-server-dev-all -y

# Redis
sudo apt install redis-server -y

# Системные библиотеки для OpenCV и геообработки
sudo apt install libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1 -y
sudo apt install gdal-bin libgdal-dev libproj-dev libgeos-dev -y

# Tesseract для OCR
sudo apt install tesseract-ocr tesseract-ocr-rus -y

# FFmpeg для обработки видео
sudo apt install ffmpeg -y
```

### **macOS:**
```bash
# Homebrew (если не установлен)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Python
brew install python@3.8

# Node.js
brew install node

# PostgreSQL
brew install postgresql
brew services start postgresql

# Redis
brew install redis
brew services start redis

# GDAL для геообработки
brew install gdal

# Tesseract
brew install tesseract tesseract-lang

# FFmpeg
brew install ffmpeg
```

### **Windows:**
```powershell
# Chocolatey (если не установлен)
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Python
choco install python --version=3.8.10

# Node.js
choco install nodejs

# PostgreSQL
choco install postgresql

# Redis
choco install redis-64

# Git
choco install git
```

---

## 📦 **Установка проекта**

### **1. Клонирование репозитория**
```bash
git clone <repository-url>
cd geo_locator
```

### **2. Backend установка**
```bash
cd backend

# Создание виртуального окружения
python3 -m venv venv

# Активация виртуального окружения
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Обновление pip
pip install --upgrade pip

# Установка зависимостей
pip install -r requirements.txt

# Установка дополнительных зависимостей для CUDA (опционально)
# pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### **3. Frontend установка**
```bash
cd ../frontend

# Установка зависимостей
npm install

# Проверка установки
npm list
```

---

## 🗄️ **Настройка базы данных**

### **PostgreSQL:**
```bash
# Запуск PostgreSQL
sudo systemctl start postgresql  # Linux
brew services start postgresql   # macOS

# Создание пользователя и базы данных
sudo -u postgres psql

-- В psql консоли:
CREATE USER geo_user WITH PASSWORD 'your_password';
CREATE DATABASE geo_locator OWNER geo_user;
GRANT ALL PRIVILEGES ON DATABASE geo_locator TO geo_user;

-- Включение расширений
\c geo_locator
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;
\q
```

### **Redis:**
```bash
# Запуск Redis
sudo systemctl start redis-server  # Linux
brew services start redis          # macOS

# Проверка работы
redis-cli ping
# Должен вернуть: PONG
```

---

## ⚙️ **Конфигурация**

### **1. Переменные окружения**
```bash
cd backend
cp env_example.txt .env
```

**Отредактируйте `.env` файл:**
```env
# База данных
DATABASE_URL=postgresql://geo_user:your_password@localhost:5432/geo_locator

# Redis
REDIS_URL=redis://localhost:6379/0

# API ключи (получите на соответствующих сайтах)
YANDEX_API_KEY=your_yandex_api_key
DGIS_API_KEY=your_2gis_api_key
ROSCOSMOS_API_KEY=your_roscosmos_api_key

# Mistral AI
MISTRAL_API_KEY=your_mistral_api_key

# Flask настройки
FLASK_ENV=development
SECRET_KEY=your_secret_key_here

# Порты
BACKEND_PORT=5001
FRONTEND_PORT=3000
```

### **2. Получение API ключей**

**Яндекс Карты:**
1. Перейдите на https://developer.tech.yandex.ru/
2. Создайте приложение
3. Получите API ключ для JavaScript API и HTTP Геокодера

**2GIS:**
1. Зарегистрируйтесь на https://dev.2gis.ru/
2. Создайте проект
3. Получите API ключ

**Роскосмос (опционально):**
1. Обратитесь к официальным источникам Роскосмос
2. Получите доступ к спутниковым данным

**Mistral AI:**
1. Зарегистрируйтесь на https://mistral.ai/
2. Получите API ключ для доступа к моделям

---

## 🚀 **Запуск системы**

### **1. Инициализация базы данных**
```bash
cd backend
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Создание таблиц
python -c "from app import app, db; app.app_context().push(); db.create_all()"

# Проверка подключения
python check_users.py
```

### **2. Запуск Backend**
```bash
# Способ 1: Через скрипт
./start_local.sh

# Способ 2: Напрямую
python run_local.py

# Способ 3: Flask команда
export FLASK_APP=app.py
flask run --host=0.0.0.0 --port=5001
```

### **3. Запуск Frontend**
```bash
cd frontend

# Разработка
npm start

# Продакшн сборка
npm run build
npm install -g serve
serve -s build -l 3000
```

### **4. Проверка работоспособности**
```bash
# Backend API
curl http://localhost:5001/api/violations/health

# Frontend
curl http://localhost:3000
```

---

## 🧪 **Тестирование установки**

### **Автоматические тесты:**
```bash
cd backend

# Тест всех сервисов
python test_all_services.py

# Тест API
python quick_api_test.py

# Тест конкретных компонентов
python test_yolo_debug.py
python test_mistral_integration.py
python test_geo_system.py
```

### **Ручная проверка:**
1. Откройте http://localhost:3000
2. Перейдите в раздел "Загрузка нарушений"
3. Загрузите тестовое изображение
4. Проверьте работу детекции
5. Просмотрите результаты на карте

---

## 🔧 **Решение проблем**

### **Проблемы с Python зависимостями:**
```bash
# Обновление pip
pip install --upgrade pip setuptools wheel

# Переустановка проблемных пакетов
pip uninstall opencv-python
pip install opencv-python-headless

# Для Apple Silicon Mac:
pip install --upgrade torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

### **Проблемы с PostgreSQL:**
```bash
# Проверка статуса
sudo systemctl status postgresql

# Перезапуск
sudo systemctl restart postgresql

# Проверка подключения
psql -h localhost -U geo_user -d geo_locator
```

### **Проблемы с портами:**
```bash
# Проверка занятых портов
sudo netstat -tulpn | grep :5001
sudo netstat -tulpn | grep :3000

# Освобождение порта
sudo fuser -k 5001/tcp
sudo fuser -k 3000/tcp
```

### **Проблемы с YOLO моделью:**
```bash
# Скачивание модели вручную
cd backend
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt
# или
curl -L https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt -o yolov8n.pt
```

---

## 🐳 **Docker установка (альтернативный способ)**

### **Docker Compose:**
```yaml
# docker-compose.yml
version: '3.8'
services:
  postgres:
    image: postgis/postgis:14-3.2
    environment:
      POSTGRES_DB: geo_locator
      POSTGRES_USER: geo_user
      POSTGRES_PASSWORD: your_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build: ./backend
    ports:
      - "5001:5001"
    depends_on:
      - postgres
      - redis
    environment:
      - DATABASE_URL=postgresql://geo_user:your_password@postgres:5432/geo_locator
      - REDIS_URL=redis://redis:6379/0

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  postgres_data:
```

**Запуск:**
```bash
docker-compose up -d
```

---

## 📊 **Мониторинг и логи**

### **Логи системы:**
```bash
# Backend логи
tail -f logs/backend.log

# Frontend логи (в браузере)
F12 -> Console

# PostgreSQL логи
sudo tail -f /var/log/postgresql/postgresql-14-main.log

# Redis логи
sudo tail -f /var/log/redis/redis-server.log
```

### **Мониторинг ресурсов:**
```bash
# CPU и память
htop

# Дисковое пространство
df -h

# Сетевые подключения
ss -tulpn
```

---

## ✅ **Проверочный список**

После установки убедитесь, что:

- [ ] PostgreSQL запущен и доступен
- [ ] Redis запущен и отвечает на ping
- [ ] Backend API отвечает на /health endpoints
- [ ] Frontend загружается на localhost:3000
- [ ] YOLO модель загружена (yolov8n.pt)
- [ ] API ключи настроены в .env
- [ ] Тестовая загрузка изображения работает
- [ ] Карта отображается корректно
- [ ] Аналитика показывает данные

---

## 🆘 **Получение помощи**

### **Диагностические команды:**
```bash
# Проверка версий
python --version
node --version
psql --version
redis-server --version

# Проверка Python пакетов
pip list | grep -E "(torch|opencv|flask)"

# Проверка портов
netstat -an | grep -E "(5001|3000|5432|6379)"

# Проверка процессов
ps aux | grep -E "(python|node|postgres|redis)"
```

### **Логи для отладки:**
```bash
# Подробные логи Flask
export FLASK_DEBUG=1
python run_local.py

# Логи npm
npm start --verbose

# Системные логи
journalctl -f -u postgresql
journalctl -f -u redis
```

---

*Руководство обновлено: 16 сентября 2025 г.*
*Версия: 1.0.0*
