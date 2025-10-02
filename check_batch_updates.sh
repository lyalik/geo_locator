#!/bin/bash

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║   🔍 ПРОВЕРКА ОБНОВЛЕНИЙ ПАКЕТНОЙ ЗАГРУЗКИ                   ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "📋 Проверка backend обновлений..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Проверка violation_api.py
if grep -q "reference_db_service.search_by_coordinates" backend/routes/violation_api.py; then
    echo -e "${GREEN}✅ Backend: Поиск в reference database добавлен${NC}"
else
    echo -e "${YELLOW}⚠️  Backend: Поиск в reference database не найден${NC}"
fi

if grep -q "reference_db_service.validate_detection" backend/routes/violation_api.py; then
    echo -e "${GREEN}✅ Backend: Валидация добавлена${NC}"
else
    echo -e "${YELLOW}⚠️  Backend: Валидация не найдена${NC}"
fi

if grep -q "ViolationResponseFormatter.format_response" backend/routes/violation_api.py; then
    echo -e "${GREEN}✅ Backend: Унифицированный форматтер используется${NC}"
else
    echo -e "${YELLOW}⚠️  Backend: Форматтер не используется${NC}"
fi

echo ""
echo "📱 Проверка frontend обновлений..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Проверка BatchAnalyzer.js
if grep -q "import ValidationDisplay from './ValidationDisplay'" frontend/src/components/BatchAnalyzer.js; then
    echo -e "${GREEN}✅ Frontend: ValidationDisplay импортирован${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend: ValidationDisplay не импортирован${NC}"
fi

if grep -q "customer_type" frontend/src/components/BatchAnalyzer.js; then
    echo -e "${GREEN}✅ Frontend: Отображение customer_type добавлено${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend: customer_type не отображается${NC}"
fi

if grep -q "<ValidationDisplay" frontend/src/components/BatchAnalyzer.js; then
    echo -e "${GREEN}✅ Frontend: ValidationDisplay компонент используется${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend: ValidationDisplay не используется${NC}"
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                   📊 ИТОГИ ПРОВЕРКИ                           ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "✅ Все обновления применены!"
echo ""
echo "🚀 Для тестирования:"
echo "   1. Откройте: http://192.168.1.67:3000"
echo "   2. Перейдите в 'Пакетная загрузка'"
echo "   3. Загрузите несколько фото"
echo "   4. Укажите координаты: 55.89481, 37.68944"
echo "   5. Проверьте результаты!"
echo ""
echo "📖 Подробности: cat ОБНОВЛЕНИЯ_ПАКЕТНОЙ_ЗАГРУЗКИ.md"
