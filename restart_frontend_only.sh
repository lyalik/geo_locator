#!/bin/bash

echo "🔄 ПЕРЕЗАПУСК ТОЛЬКО FRONTEND"
echo "=================================================="

# Остановка frontend процессов
echo "⏹️  Останавливаем Frontend..."
pkill -f "react-scripts" 2>/dev/null
pkill -f "npm start" 2>/dev/null
sleep 2

# Очистка кэша
echo "🧹 Очищаем кэш..."
cd frontend
rm -rf .cache node_modules/.cache 2>/dev/null

# Запуск frontend
echo "🚀 Запускаем Frontend..."
echo ""
echo "📝 ВАЖНО: После запуска в браузере нажмите Ctrl+Shift+R"
echo ""

HOST=0.0.0.0 PORT=3000 npm start

