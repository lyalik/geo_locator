#!/bin/bash

echo "🚀 ЗАПУСК GEO LOCATOR ДЛЯ ДЕМОНСТРАЦИИ"
echo "=" * 50

# Остановка существующих процессов
echo "🧹 Останавливаем существующие процессы..."
pkill -f "react-scripts" 2>/dev/null
pkill -f "npm start" 2>/dev/null
pkill -f "flask" 2>/dev/null
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
HOST=0.0.0.0 npm start &
FRONTEND_PID=$!
echo "Frontend запущен с PID: $FRONTEND_PID"
cd ..

# Ждем запуска frontend
sleep 10

echo ""
echo "🎉 GEO LOCATOR ЗАПУЩЕН!"
echo "=" * 50
echo "📍 Frontend (localhost): http://localhost:3000"
echo "📍 Frontend (external): http://192.168.1.67:3000"
echo "📍 Backend API: http://localhost:5001"
echo "📍 Health Check: http://localhost:5001/health"
echo "=" * 50
echo ""
echo "💡 Для остановки нажмите Ctrl+C"
echo ""

# Функция для корректного завершения
cleanup() {
    echo ""
    echo "🛑 Останавливаем сервисы..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    pkill -f "react-scripts" 2>/dev/null
    pkill -f "npm start" 2>/dev/null
    echo "✅ Сервисы остановлены"
    exit 0
}

# Обработчик сигнала завершения
trap cleanup SIGINT SIGTERM

# Ждем завершения
wait
