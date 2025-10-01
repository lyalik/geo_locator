#!/bin/bash

echo "🏗️ Создание production build для сетевого доступа..."

# Переходим в папку frontend
cd frontend

# Создаем production build
echo "📦 Building React app..."
npm run build

# Создаем nginx конфигурацию для production
echo "⚙️ Creating nginx config for production..."
cat > ../nginx-production.conf << 'EOF'
server {
    listen 80;
    server_name 192.168.1.67 45.130.189.36 localhost _;
    
    # Разрешаем доступ с любого IP в локальной сети
    root /home/denis/Documents/Hackathon_2025/geo_locator/frontend/build;
    index index.html;
    
    # Увеличиваем лимиты для загрузки файлов
    client_max_body_size 100M;
    
    # Настройки для внешнего доступа
    proxy_connect_timeout       60s;
    proxy_send_timeout          60s;
    proxy_read_timeout          60s;
    
    # Безопасность
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Статические файлы React
    location /static/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # API endpoints (Flask backend)
    location /api/ {
        proxy_pass http://127.0.0.1:5001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # CORS headers
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
        add_header Access-Control-Allow-Headers "Content-Type, Authorization, X-Requested-With";
        
        # Обработка preflight запросов
        if ($request_method = 'OPTIONS') {
            add_header Access-Control-Allow-Origin *;
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
            add_header Access-Control-Allow-Headers "Content-Type, Authorization, X-Requested-With";
            add_header Content-Length 0;
            add_header Content-Type text/plain;
            return 204;
        }
    }
    
    # Авторизация endpoints
    location /auth/ {
        proxy_pass http://127.0.0.1:5001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # CORS headers
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
        add_header Access-Control-Allow-Headers "Content-Type, Authorization, X-Requested-With";
        
        # Обработка preflight запросов
        if ($request_method = 'OPTIONS') {
            add_header Access-Control-Allow-Origin *;
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
            add_header Access-Control-Allow-Headers "Content-Type, Authorization, X-Requested-With";
            add_header Content-Length 0;
            add_header Content-Type text/plain;
            return 204;
        }
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:5001/health;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # React Router - все остальные запросы направляем на index.html
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # Логирование
    access_log /var/log/nginx/geo-locator-access.log;
    error_log /var/log/nginx/geo-locator-error.log;
}
EOF

echo "✅ Production build готов!"
echo "📋 Для использования production версии:"
echo "   sudo cp nginx-production.conf /etc/nginx/sites-available/geo-locator"
echo "   sudo systemctl reload nginx"
echo ""
echo "📋 Для возврата к development версии:"
echo "   sudo cp nginx-geo-locator.conf /etc/nginx/sites-available/geo-locator"
echo "   sudo systemctl reload nginx"
