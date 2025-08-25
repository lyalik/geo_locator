# Geo Locator - Система определения координат объектов по фотографиям

## 🚀 О проекте

Geo Locator - это сервис для автоматического определения точных координат объектов на фотографиях с признаками нарушений использования нежилого фонда. Система интегрируется в существующую инфраструктуру и повышает точность выявления нарушений.

### Основные возможности

- 📸 Загрузка фотографий для анализа
- 🎯 Автоматическое определение координат объектов
- 🏢 Выявление нарушений использования нежилого фонда
- 🗺️ Визуализация на карте
- 📊 Анализ и отчетность

## 🛠️ Технологический стек

### Бэкенд
- Python 3.12
- Flask
- PostgreSQL с PostGIS
- Redis
- Celery
- Docker

### Фронтенд
- React
- Material-UI
- Yandex Maps API
- 2GIS Maps API

## 🚀 Быстрый старт

### Предварительные требования

- Docker и Docker Compose
- Git
- API ключи для сервисов (Yandex, 2GIS и др.)

### Установка

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/lyalik/geo_locator.git
   cd geo-locator
   ```

2. Создайте файл `.env` в корне проекта:
   ```env
   # Database
   POSTGRES_USER=your_user
   POSTGRES_PASSWORD=your_secure_password
   POSTGRES_DB=geo_locator
   
   # Redis
   CELERY_BROKER_URL=redis://redis:6379/0
   CELERY_RESULT_BACKEND=redis://redis:6379/0
   
   # API Keys
   YANDEX_API_KEY=your_yandex_key
   DGIS_API_KEY=your_dgis_key
   GEMINI_API_KEY=your_gemini_key
   ```

3. Настройте права доступа к Docker (если нужно):
   ```bash
   sudo usermod -aG docker $USER
   newgrp docker
   ```

4. Запустите приложение:
   ```bash
   docker-compose up --build
   ```

5. После успешного запуска откройте в браузере:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000
   - Flower (мониторинг Celery): http://localhost:5555

## 🔧 Разработка

### Установка зависимостей

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

### Запуск в режиме разработки

```bash
# Backend
cd backend
flask run --debug

# Frontend (в отдельном терминале)
cd frontend
npm start
```

## 📚 API Документация

Документация API доступна по адресу `http://localhost:5000/api/docs` после запуска приложения.

## 🐛 Поиск и устранение неисправностей

### Проблемы с правами Docker

Если возникают ошибки доступа к Docker:

```bash
# Остановите Docker
sudo systemctl stop docker.socket
sudo systemctl stop docker

# Добавьте пользователя в группу docker
sudo usermod -aG docker $USER

# Примените изменения
newgrp docker

# Проверьте доступ
docker ps
```

### Очистка Docker

Для полной пересборки контейнеров:

```bash
docker-compose down -v
docker-compose up --build
```

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для вашей функции (`git checkout -b feature/AmazingFeature`)
3. Зафиксируйте изменения (`git commit -m 'Add some AmazingFeature'`)
4. Отправьте изменения в форк (`git push origin feature/AmazingFeature`)
5. Откройте Pull Request

## 📄 Лицензия

Этот проект распространяется под лицензией MIT. См. файл `LICENSE` для получения дополнительной информации.

## 📞 Контакты

Denis Lyalik - lyalik.denis@gmail.com

Ссылка на проект: [https://github.com/lyalik/geo_locator](https://github.com/lyalik/geo_locator)
