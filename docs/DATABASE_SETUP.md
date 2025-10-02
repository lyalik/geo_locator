# 🗄️ База данных Geo Locator - Настройка и развертывание

Этот документ содержит инструкции по настройке базы данных PostgreSQL для системы Geo Locator.

## 📋 Содержание

- [Быстрый старт](#быстрый-старт)
- [Переменные окружения](#переменные-окружения)
- [Создание новой базы данных](#создание-новой-базы-данных)
- [Миграция существующей базы данных](#миграция-существующей-базы-данных)
- [Структура таблиц](#структура-таблиц)
- [Устранение проблем](#устранение-проблем)

## 🚀 Быстрый старт

### 1. Установка PostgreSQL

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**CentOS/RHEL:**
```bash
sudo yum install postgresql-server postgresql-contrib
sudo postgresql-setup initdb
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

**Docker:**
```bash
docker run -d \
  --name geo-locator-db \
  -e POSTGRES_DB=geo_locator \
  -e POSTGRES_USER=geo_user \
  -e POSTGRES_PASSWORD=secure_password \
  -p 5432:5432 \
  postgres:15
```

### 2. Создание пользователя и базы данных

```bash
# Подключаемся к PostgreSQL как суперпользователь
sudo -u postgres psql

# Создаем пользователя
CREATE USER geo_user WITH PASSWORD 'secure_password';

# Создаем базу данных
CREATE DATABASE geo_locator OWNER geo_user;

# Даем права пользователю
GRANT ALL PRIVILEGES ON DATABASE geo_locator TO geo_user;

# Выходим
\q
```

### 3. Настройка переменных окружения

Создайте файл `.env` в папке `backend/`:

```bash
# Database Configuration
DATABASE_URL=postgresql://geo_user:secure_password@localhost:5432/geo_locator

# Или используйте отдельные параметры:
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=geo_locator
POSTGRES_USER=geo_user
POSTGRES_PASSWORD=secure_password
```

### 4. Установка зависимостей и создание таблиц

```bash
cd backend/
pip install python-dotenv sqlalchemy psycopg2-binary werkzeug
python create_database_tables.py
```

## 🔧 Переменные окружения

### Основные параметры

| Переменная | Описание | Пример |
|------------|----------|--------|
| `DATABASE_URL` | Полный URL подключения | `postgresql://user:pass@host:5432/db` |
| `POSTGRES_HOST` | Хост PostgreSQL | `localhost` |
| `POSTGRES_PORT` | Порт PostgreSQL | `5432` |
| `POSTGRES_DB` | Имя базы данных | `geo_locator` |
| `POSTGRES_USER` | Пользователь | `geo_user` |
| `POSTGRES_PASSWORD` | Пароль | `secure_password` |

### Дополнительные параметры

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `DB_POOL_SIZE` | Размер пула соединений | `10` |
| `DB_MAX_OVERFLOW` | Максимальное переполнение пула | `20` |
| `DB_POOL_TIMEOUT` | Таймаут получения соединения | `30` |

## 🏗️ Создание новой базы данных

### Автоматическое создание

```bash
cd backend/
python create_database_tables.py
```

Скрипт выполнит:
- ✅ Создание базы данных (если не существует)
- ✅ Создание всех таблиц
- ✅ Создание индексов для производительности
- ✅ Создание пользователя-администратора
- ✅ Создание полезных представлений (views)

### Ручное создание

1. **Создание базы данных:**
```sql
CREATE DATABASE geo_locator 
    WITH ENCODING 'UTF8'
    LC_COLLATE='ru_RU.UTF-8'
    LC_CTYPE='ru_RU.UTF-8'
    TEMPLATE=template0;
```

2. **Создание пользователя:**
```sql
CREATE USER geo_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE geo_locator TO geo_user;
```

3. **Запуск скрипта создания таблиц:**
```bash
python create_database_tables.py
```

## 🔄 Миграция существующей базы данных

Если у вас уже есть база данных и нужно обновить её структуру:

```bash
cd backend/
python migrate_database.py
```

Скрипт миграции:
- 🔍 Анализирует текущую структуру
- 🏗️ Создает недостающие таблицы
- 🔧 Добавляет недостающие колонки
- 🔄 Обновляет типы данных
- 👁️ Создает полезные представления
- 📊 Показывает финальную статистику

## 📊 Структура таблиц

### Основные таблицы

| Таблица | Описание | Записей |
|---------|----------|---------|
| `users` | Пользователи системы | Администраторы и пользователи |
| `photos` | Загруженные фотографии | Все изображения с метаданными |
| `violations` | Обнаруженные нарушения | Результаты ИИ-анализа |
| `detected_objects` | Обнаруженные объекты | YOLO детекция объектов |

### Дополнительные таблицы

| Таблица | Описание |
|---------|----------|
| `geo_images` | Геопривязанные изображения для архивного поиска |
| `analysis_sessions` | Сессии пакетной обработки |
| `system_logs` | Системные логи и мониторинг |

### Полезные представления (Views)

| Представление | Описание |
|---------------|----------|
| `violation_summary` | Сводка по нарушениям (категории, статусы) |
| `user_activity` | Активность пользователей |
| `coordinate_coverage` | Покрытие координатами |

## 🔍 Проверка состояния базы данных

### Подключение к базе данных

```bash
# Через psql
psql postgresql://geo_user:secure_password@localhost:5432/geo_locator

# Или
PGPASSWORD=secure_password psql -h localhost -U geo_user -d geo_locator
```

### Полезные SQL запросы

**Проверка таблиц:**
```sql
SELECT table_name, 
       (SELECT COUNT(*) FROM information_schema.columns 
        WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public'
ORDER BY table_name;
```

**Статистика по данным:**
```sql
-- Количество записей в каждой таблице
SELECT 
    schemaname,
    tablename,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes,
    n_live_tup as live_rows
FROM pg_stat_user_tables
ORDER BY live_rows DESC;
```

**Использование места:**
```sql
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size(tablename::regclass)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(tablename::regclass) DESC;
```

## 🛠️ Устранение проблем

### Проблема: "database does not exist"

**Решение:**
```bash
# Создайте базу данных вручную
sudo -u postgres createdb geo_locator

# Или через SQL
sudo -u postgres psql -c "CREATE DATABASE geo_locator;"
```

### Проблема: "role does not exist"

**Решение:**
```bash
# Создайте пользователя
sudo -u postgres createuser -P geo_user

# Или через SQL
sudo -u postgres psql -c "CREATE USER geo_user WITH PASSWORD 'secure_password';"
```

### Проблема: "permission denied"

**Решение:**
```sql
-- Дайте права пользователю
GRANT ALL PRIVILEGES ON DATABASE geo_locator TO geo_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO geo_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO geo_user;
```

### Проблема: "connection refused"

**Решение:**
1. Проверьте, что PostgreSQL запущен:
```bash
sudo systemctl status postgresql
```

2. Проверьте настройки подключения в `postgresql.conf`:
```bash
# Найдите файл конфигурации
sudo find /etc -name "postgresql.conf" 2>/dev/null

# Отредактируйте настройки
listen_addresses = 'localhost'
port = 5432
```

3. Проверьте `pg_hba.conf` для разрешения подключений:
```bash
# Добавьте строку для локальных подключений
local   all             geo_user                                md5
host    all             geo_user        127.0.0.1/32            md5
```

### Проблема: Медленные запросы

**Решение:**
```bash
# Запустите создание индексов
python -c "
from create_database_tables import create_indexes, get_database_url
create_indexes(get_database_url())
"
```

## 📈 Мониторинг и обслуживание

### Регулярное обслуживание

```sql
-- Обновление статистики
ANALYZE;

-- Очистка и переиндексация
VACUUM ANALYZE;

-- Переиндексация (при необходимости)
REINDEX DATABASE geo_locator;
```

### Резервное копирование

```bash
# Создание резервной копии
pg_dump -h localhost -U geo_user -d geo_locator > backup_$(date +%Y%m%d_%H%M%S).sql

# Восстановление из резервной копии
psql -h localhost -U geo_user -d geo_locator < backup_20241001_161900.sql
```

## 🔐 Безопасность

### Рекомендации по безопасности

1. **Используйте сложные пароли:**
```bash
# Генерация случайного пароля
openssl rand -base64 32
```

2. **Ограничьте доступ по IP:**
```bash
# В pg_hba.conf
host    geo_locator     geo_user        192.168.1.0/24         md5
```

3. **Используйте SSL соединения:**
```bash
# В postgresql.conf
ssl = on
ssl_cert_file = 'server.crt'
ssl_key_file = 'server.key'
```

4. **Регулярно обновляйте PostgreSQL:**
```bash
sudo apt update && sudo apt upgrade postgresql
```

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи PostgreSQL:
```bash
sudo tail -f /var/log/postgresql/postgresql-*.log
```

2. Проверьте логи приложения:
```bash
tail -f backend/logs/app.log
```

3. Запустите диагностику:
```bash
python migrate_database.py  # Покажет текущее состояние БД
```

---

**Geo Locator Database Setup Guide**  
Версия: 1.0  
Дата: Октябрь 2024
