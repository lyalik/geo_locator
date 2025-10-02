#!/bin/bash

echo "🚀 ЗАПУСК GEO LOCATOR ДЛЯ ДЕМОНСТРАЦИИ"
echo "=================================================="

# Остановка существующих процессов
echo "🧹 Останавливаем существующие процессы..."
pkill -f "react-scripts" 2>/dev/null
pkill -f "npm start" 2>/dev/null
pkill -f "python.*app.py" 2>/dev/null
sleep 2

# Проверяем PostgreSQL
echo "🔍 Проверяем PostgreSQL..."
if ! pgrep -x "postgres" > /dev/null; then
    echo "⚠️ PostgreSQL не запущен. Запускаем..."
    sudo systemctl start postgresql
    sleep 3
fi

# Запускаем Backend
echo "🔧 Запускаем Backend..."
cd backend
source venv/bin/activate
python app.py &
BACKEND_PID=$!
echo "Backend запущен с PID: $BACKEND_PID"
cd ..

# Ждем запуска backend
sleep 5

# Проверяем backend
echo "🔍 Проверяем Backend..."
if curl -s http://localhost:5001/health > /dev/null; then
    echo "✅ Backend работает"
else
    echo "❌ Backend не отвечает"
fi

# Запускаем Frontend
echo "🌐 Запускаем Frontend..."
cd frontend
# Очищаем кэш перед запуском
rm -rf .cache node_modules/.cache 2>/dev/null
# Запускаем с HOST=0.0.0.0 для доступа из сети
HOST=0.0.0.0 PORT=3000 npm start &
FRONTEND_PID=$!
echo "Frontend запущен с PID: $FRONTEND_PID"
cd ..

# Ждем запуска frontend
echo "⏳ Ожидаем запуск Frontend (10 сек)..."
sleep 10

# Проверяем frontend
echo "🔍 Проверяем Frontend..."
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Frontend работает"
else
    echo "⚠️ Frontend еще загружается..."
fi

echo ""
echo "=================================================="
echo "🎉 GEO LOCATOR ЗАПУЩЕН!"
echo "=================================================="
echo ""
echo "📱 ДОСТУП К ПРИЛОЖЕНИЮ:"
echo "  • Локально:      http://localhost:3000"
echo "  • Локальная сеть: http://192.168.1.67:3000"
echo "  • Внешний доступ: http://45.130.189.36 (через nginx)"
echo ""
echo "🔧 BACKEND API:"
echo "  • Health Check:  http://192.168.1.67:5001/health"
echo "  • API Direct:    http://192.168.1.67:5001/api/"
echo "  • Auth:          http://192.168.1.67:5001/auth/"
echo ""
echo "👤 ТЕСТОВЫЕ АККАУНТЫ:"
echo "  • Email: test@test.com | Password: test123"
echo "  • Email: admin@test.com | Password: admin123"
echo ""
echo "=================================================="
echo "💡 Для остановки нажмите Ctrl+C"
echo "=================================================="
echo ""

# Функция для корректного завершения
cleanup() {
    echo ""
    echo "🛑 Останавливаем сервисы..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    pkill -f "react-scripts" 2>/dev/null
    pkill -f "npm start" 2>/dev/null
    pkill -f "python.*app.py" 2>/dev/null
    sleep 1
    echo "✅ Сервисы остановлены"
    exit 0
}

# Обработчик сигнала завершения
trap cleanup SIGINT SIGTERM

# Ждем завершения
wait
