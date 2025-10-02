#!/bin/bash

echo "🧹 Очистка кэша и перезапуск frontend..."

# Остановить React dev server
echo "⏹️  Останавливаем React dev server..."
pkill -f "node.*react-scripts" || true
sleep 2

cd frontend

# Очистить все кэши
echo "🗑️  Очищаем кэши..."
rm -rf node_modules/.cache
rm -rf .cache
rm -rf build

# Очистить кэш npm
echo "🗑️  Очищаем npm cache..."
npm cache clean --force 2>/dev/null || true

echo ""
echo "✅ Кэш очищен!"
echo ""
echo "🚀 Теперь запустите frontend:"
echo "   cd frontend && npm start"
echo ""
echo "📝 После запуска:"
echo "   1. Откройте http://192.168.1.67:3000 в браузере"
echo "   2. Нажмите Ctrl+Shift+R для жесткой перезагрузки"
echo "   3. Откройте консоль (F12) и проверьте запросы"
echo "   4. Все запросы должны идти на http://192.168.1.67:5001"
echo ""
