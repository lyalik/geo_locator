# Geo Locator Server - Руководство по развертыванию и администрированию

## 🖥️ Обзор серверной части

Geo Locator Backend - это высокопроизводительный Flask API сервер с интеграцией ИИ сервисов, геолокационных API и системой управления данными. Сервер обеспечивает работу веб-приложения и мобильного приложения.

---

## 🏗️ Архитектура сервера

### Основные компоненты
- **Flask Application** - основной веб-сервер (порт 5001)
- **PostgreSQL** - основная база данных
- **Redis** - кэширование и сессии
- **Nginx** - reverse proxy и статические файлы (продакшн)
- **Gunicorn** - WSGI сервер (продакшн)

### Структура проекта
```
backend/
├── app.py                 # Главный файл приложения
├── config.py              # Конфигурация
├── models.py              # Модели базы данных
├── requirements.txt       # Python зависимости
├── routes/                # API маршруты
│   ├── admin_api.py       # Административные функции
│   ├── violation_api.py   # Управление нарушениями
│   ├── notification_api.py # Система уведомлений
│   └── ...
├── services/              # Бизнес-логика
│   ├── yolo_violation_detector.py
│   ├── mistral_ai_service.py
│   ├── yandex_maps_service.py
│   └── ...
└── uploads/               # Загруженные файлы
    └── violations/        # Фото нарушений
```

---

## 🚀 Установка и настройка

### Системные требования
- **OS**: Ubuntu 20.04+ / CentOS 8+ / Docker
- **Python**: 3.8+
- **RAM**: минимум 4GB, рекомендуется 8GB+
- **Диск**: минимум 20GB свободного места
- **CPU**: 2+ ядра, рекомендуется 4+

### Установка зависимостей

#### Ubuntu/Debian
```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Python и pip
sudo apt install python3 python3-pip python3-venv -y

# PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Redis
sudo apt install redis-server -y

# Системные библиотеки
sudo apt install libpq-dev python3-dev build-essential -y

# Для обработки изображений
sudo apt install libopencv-dev python3-opencv -y
```

#### CentOS/RHEL
```bash
# Обновление системы
sudo yum update -y

# Python и pip
sudo yum install python3 python3-pip python3-devel -y

# PostgreSQL
sudo yum install postgresql postgresql-server postgresql-contrib -y
sudo postgresql-setup initdb
sudo systemctl enable postgresql

# Redis
sudo yum install redis -y
sudo systemctl enable redis

# Системные библиотеки
sudo yum groupinstall "Development Tools" -y
sudo yum install postgresql-devel -y
```

### Настройка базы данных

#### PostgreSQL
```bash
# Создание пользователя и базы данных
sudo -u postgres psql

CREATE USER geolocator WITH PASSWORD 'your_secure_password';
CREATE DATABASE geolocator OWNER geolocator;
GRANT ALL PRIVILEGES ON DATABASE geolocator TO geolocator;
\q
```

#### Redis
```bash
# Настройка Redis
sudo systemctl start redis
sudo systemctl enable redis

# Проверка работы
redis-cli ping
# Ответ: PONG
```

### Установка приложения

```bash
# Клонирование репозитория
git clone https://github.com/your-org/geo-locator.git
cd geo-locator/backend

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Создание файла конфигурации
cp .env.example .env
nano .env
```

### Конфигурация (.env файл)

```env
# Основные настройки
FLASK_ENV=production
SECRET_KEY=your_very_secure_secret_key_here
DEBUG=False

# База данных
DATABASE_URL=postgresql://geolocator:your_secure_password@localhost/geolocator

# Redis
REDIS_URL=redis://localhost:6379/0

# API ключи геосервисов
YANDEX_API_KEY=your_yandex_maps_api_key
DGIS_API_KEY=your_2gis_api_key
ROSCOSMOS_API_KEY=your_roscosmos_api_key

# ИИ сервисы
MISTRAL_API_KEY=your_mistral_ai_api_key
OPENAI_API_KEY=your_openai_api_key  # опционально

# Уведомления
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EXPO_ACCESS_TOKEN=your_expo_access_token

# Безопасность
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
CORS_ORIGINS=http://localhost:3000,https://your-domain.com

# Файловое хранилище
UPLOAD_FOLDER=/var/www/geolocator/uploads
MAX_CONTENT_LENGTH=16777216  # 16MB

# Логирование
LOG_LEVEL=INFO
LOG_FILE=/var/log/geolocator/app.log
```

---

## 🔧 Настройка продакшн среды

### Nginx конфигурация

```nginx
# /etc/nginx/sites-available/geolocator
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;
    
    # SSL сертификаты
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # SSL настройки
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    # Безопасность
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
    
    # Основное приложение
    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Таймауты
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Статические файлы
    location /static/ {
        alias /var/www/geolocator/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Загруженные файлы
    location /uploads/ {
        alias /var/www/geolocator/uploads/;
        expires 1M;
        add_header Cache-Control "public";
    }
    
    # Ограничения размера загрузки
    client_max_body_size 20M;
    
    # Логирование
    access_log /var/log/nginx/geolocator_access.log;
    error_log /var/log/nginx/geolocator_error.log;
}
```

### Gunicorn конфигурация

```python
# gunicorn.conf.py
import multiprocessing

# Сервер
bind = "127.0.0.1:5001"
backlog = 2048

# Воркеры
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Перезапуск
max_requests = 1000
max_requests_jitter = 50
preload_app = True

# Логирование
accesslog = "/var/log/geolocator/gunicorn_access.log"
errorlog = "/var/log/geolocator/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Процесс
user = "geolocator"
group = "geolocator"
tmp_upload_dir = None
```

### Systemd сервис

```ini
# /etc/systemd/system/geolocator.service
[Unit]
Description=Geo Locator Flask Application
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=geolocator
Group=geolocator
RuntimeDirectory=geolocator
WorkingDirectory=/var/www/geolocator/backend
Environment=PATH=/var/www/geolocator/backend/venv/bin
ExecStart=/var/www/geolocator/backend/venv/bin/gunicorn --config gunicorn.conf.py app:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

---

## 🗄️ Управление базой данных

### Миграции

```bash
# Инициализация миграций
flask db init

# Создание миграции
flask db migrate -m "Initial migration"

# Применение миграций
flask db upgrade

# Откат миграции
flask db downgrade
```

### Резервное копирование

```bash
#!/bin/bash
# backup_db.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/geolocator"
DB_NAME="geolocator"
DB_USER="geolocator"

# Создание директории
mkdir -p $BACKUP_DIR

# Создание бэкапа
pg_dump -U $DB_USER -h localhost $DB_NAME | gzip > $BACKUP_DIR/geolocator_$DATE.sql.gz

# Удаление старых бэкапов (старше 30 дней)
find $BACKUP_DIR -name "geolocator_*.sql.gz" -mtime +30 -delete

echo "Backup completed: geolocator_$DATE.sql.gz"
```

### Восстановление

```bash
#!/bin/bash
# restore_db.sh

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file.sql.gz>"
    exit 1
fi

# Остановка приложения
sudo systemctl stop geolocator

# Восстановление базы данных
gunzip -c $BACKUP_FILE | psql -U geolocator -h localhost geolocator

# Запуск приложения
sudo systemctl start geolocator

echo "Database restored from $BACKUP_FILE"
```

---

## 📊 Мониторинг и логирование

### Настройка логирования

```python
# logging_config.py
import logging
import logging.handlers
import os

def setup_logging(app):
    if not app.debug:
        # Создание директории для логов
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        # Ротация логов
        file_handler = logging.handlers.RotatingFileHandler(
            'logs/geolocator.log', 
            maxBytes=10240000, 
            backupCount=10
        )
        
        # Формат логов
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Geo Locator startup')
```

### Мониторинг с Prometheus

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'geolocator'
    static_configs:
      - targets: ['localhost:5001']
    metrics_path: '/metrics'
    scrape_interval: 5s
```

### Health Check endpoint

```python
# В app.py
@app.route('/health')
def health_check():
    """Проверка состояния системы"""
    try:
        # Проверка базы данных
        db.session.execute('SELECT 1')
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    # Проверка Redis
    try:
        redis_client.ping()
        redis_status = "connected"
    except Exception as e:
        redis_status = f"error: {str(e)}"
    
    # Проверка дискового пространства
    disk_usage = shutil.disk_usage('/')
    disk_free_gb = disk_usage.free // (1024**3)
    
    return jsonify({
        'status': 'ok' if db_status == 'connected' and redis_status == 'connected' else 'error',
        'database': db_status,
        'redis': redis_status,
        'disk_free_gb': disk_free_gb,
        'version': '2.0.0',
        'timestamp': datetime.utcnow().isoformat()
    })
```

---

## 🔒 Безопасность

### Настройки безопасности

```python
# security.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman

def configure_security(app):
    # Rate limiting
    limiter = Limiter(
        app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"]
    )
    
    # Security headers
    Talisman(app, {
        'force_https': True,
        'strict_transport_security': True,
        'content_security_policy': {
            'default-src': "'self'",
            'script-src': "'self' 'unsafe-inline'",
            'style-src': "'self' 'unsafe-inline'",
            'img-src': "'self' data: https:",
        }
    })
    
    return limiter
```

### Firewall настройки

```bash
# UFW конфигурация
sudo ufw default deny incoming
sudo ufw default allow outgoing

# SSH
sudo ufw allow ssh

# HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# PostgreSQL (только локально)
sudo ufw allow from 127.0.0.1 to any port 5432

# Redis (только локально)
sudo ufw allow from 127.0.0.1 to any port 6379

# Активация
sudo ufw enable
```

---

## 🚀 Развертывание с Docker

### Dockerfile

```dockerfile
FROM python:3.9-slim

# Системные зависимости
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libopencv-dev \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Python зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Код приложения
COPY . .

# Пользователь
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# Порт
EXPOSE 5001

# Команда запуска
CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "5001:5001"
    environment:
      - DATABASE_URL=postgresql://geolocator:password@db:5432/geolocator
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=geolocator
      - POSTGRES_USER=geolocator
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./uploads:/var/www/uploads
    depends_on:
      - app

volumes:
  postgres_data:
```

---

## 📈 Производительность и оптимизация

### Настройки PostgreSQL

```sql
-- postgresql.conf оптимизация
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
```

### Индексы базы данных

```sql
-- Индексы для оптимизации запросов
CREATE INDEX idx_photos_user_id ON photos(user_id);
CREATE INDEX idx_photos_created_at ON photos(created_at);
CREATE INDEX idx_photos_location ON photos(lat, lon);
CREATE INDEX idx_violations_category ON violations(category);
CREATE INDEX idx_violations_status ON violations(status);
CREATE INDEX idx_violations_created_at ON violations(created_at);
```

### Кэширование Redis

```python
# cache.py
import redis
import json
from functools import wraps

redis_client = redis.Redis.from_url(os.environ.get('REDIS_URL'))

def cache_result(timeout=3600):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Создание ключа кэша
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Попытка получить из кэша
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Выполнение функции
            result = func(*args, **kwargs)
            
            # Сохранение в кэш
            redis_client.setex(cache_key, timeout, json.dumps(result))
            
            return result
        return wrapper
    return decorator
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          python -m pytest tests/

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to server
        uses: appleboy/ssh-action@v0.1.4
        with:
          host: ${{ secrets.HOST }}
          username: ${{ secrets.USERNAME }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /var/www/geolocator
            git pull origin main
            source venv/bin/activate
            pip install -r requirements.txt
            flask db upgrade
            sudo systemctl restart geolocator
```

---

## 🆘 Устранение неполадок

### Частые проблемы

#### Приложение не запускается
```bash
# Проверка логов
sudo journalctl -u geolocator -f

# Проверка конфигурации
python -c "from app import app; print('Config OK')"

# Проверка зависимостей
pip check
```

#### Проблемы с базой данных
```bash
# Проверка подключения
psql -U geolocator -h localhost -d geolocator -c "SELECT version();"

# Проверка миграций
flask db current

# Восстановление из бэкапа
./restore_db.sh /var/backups/geolocator/latest.sql.gz
```

#### Высокая нагрузка
```bash
# Мониторинг процессов
htop

# Анализ медленных запросов PostgreSQL
sudo -u postgres psql -c "SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Очистка кэша Redis
redis-cli FLUSHALL
```

---

## 📞 Поддержка

### Контакты технической поддержки
- **Email**: devops@geolocator.ru
- **Telegram**: @geolocator_devops
- **Телефон**: +7 (800) 555-0124 (24/7)

### Документация
- **API**: https://api.geolocator.ru/docs
- **Wiki**: https://wiki.geolocator.ru
- **GitHub**: https://github.com/geolocator/server

---

*Руководство обновлено: 16 сентября 2025 г.*
*Версия сервера: 2.0.0*
