# 🚀 Быстрая настройка базы данных Geo Locator

## Для нового сервера (полная установка)

### 1. Установка PostgreSQL
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install postgresql postgresql-contrib

# Запуск сервиса
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 2. Создание пользователя и базы данных
```bash
# Подключение к PostgreSQL
sudo -u postgres psql

# Создание пользователя и БД
CREATE USER geo_user WITH PASSWORD 'secure_password123';
CREATE DATABASE geo_locator OWNER geo_user;
GRANT ALL PRIVILEGES ON DATABASE geo_locator TO geo_user;
\q
```

### 3. Настройка переменных окружения
```bash
# Создайте файл .env в папке backend/
cat > backend/.env << EOF
DATABASE_URL=postgresql://geo_user:secure_password123@localhost:5432/geo_locator
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=geo_locator
POSTGRES_USER=geo_user
POSTGRES_PASSWORD=secure_password123
EOF
```

### 4. Создание всех таблиц
```bash
cd backend/
pip install sqlalchemy psycopg2-binary werkzeug python-dotenv
python create_database_tables.py
```

**Результат:**
- ✅ База данных создана
- ✅ Все таблицы созданы (users, photos, violations, detected_objects, geo_images, etc.)
- ✅ Индексы для производительности
- ✅ Администратор создан (admin/admin123)

## Для обновления существующей базы данных

```bash
cd backend/
python migrate_database.py
```

**Что делает:**
- 🔍 Анализирует текущую структуру
- 🏗️ Добавляет недостающие таблицы
- 🔧 Добавляет недостающие колонки
- 📊 Показывает статистику

## Проверка работы

```bash
# Подключение к БД
psql postgresql://geo_user:secure_password123@localhost:5432/geo_locator

# Проверка таблиц
\dt

# Проверка данных
SELECT table_name, 
       (SELECT COUNT(*) FROM information_schema.columns 
        WHERE table_name = t.table_name) as columns
FROM information_schema.tables t
WHERE table_schema = 'public';
```

## Структура созданных таблиц

| Таблица | Назначение |
|---------|------------|
| `users` | Пользователи системы |
| `photos` | Загруженные фотографии с метаданными |
| `violations` | Обнаруженные нарушения (YOLO + Mistral AI) |
| `detected_objects` | Детектированные объекты |
| `geo_images` | Архивные геопривязанные изображения |
| `analysis_sessions` | Сессии пакетной обработки |
| `system_logs` | Системные логи |

## Учетные данные по умолчанию

После создания базы данных:
- **Пользователь:** admin
- **Пароль:** admin123
- **Email:** admin@geolocator.local

## Устранение проблем

**Ошибка подключения:**
```bash
# Проверьте статус PostgreSQL
sudo systemctl status postgresql

# Перезапустите если нужно
sudo systemctl restart postgresql
```

**Ошибка прав доступа:**
```bash
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE geo_locator TO geo_user;"
```

**Проверка созданных таблиц:**
```bash
cd backend/
python -c "
import os
os.environ['DATABASE_URL'] = 'postgresql://geo_user:secure_password123@localhost:5432/geo_locator'
from migrate_database import analyze_database, get_database_url
from sqlalchemy import create_engine
analyze_database(create_engine(get_database_url()))
"
```

---

**Готово!** Ваша база данных Geo Locator настроена и готова к работе! 🎉
