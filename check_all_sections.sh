#!/bin/bash

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║         🔍 ПРОВЕРКА ВСЕХ РАЗДЕЛОВ ПРОЕКТА                    ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "📋 Список компонентов и их статус:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Функция проверки валидации в компоненте
check_validation() {
    local file=$1
    local name=$2
    
    if [ ! -f "$file" ]; then
        echo -e "${YELLOW}⚠️  $name - файл не найден${NC}"
        return
    fi
    
    has_validation_import=$(grep -q "ValidationDisplay" "$file" && echo "yes" || echo "no")
    has_customer_type=$(grep -q "customer_type" "$file" && echo "yes" || echo "no")
    
    if [ "$has_validation_import" = "yes" ] && [ "$has_customer_type" = "yes" ]; then
        echo -e "${GREEN}✅ $name - полностью интегрирован${NC}"
    elif [ "$has_validation_import" = "yes" ] || [ "$has_customer_type" = "yes" ]; then
        echo -e "${YELLOW}⚠️  $name - частично интегрирован${NC}"
    else
        echo -e "${BLUE}ℹ️  $name - не требует валидации${NC}"
    fi
}

# Проверка всех компонентов
check_validation "frontend/src/components/ViolationUploader.js" "1. Детекция нарушений (ViolationUploader)"
check_validation "frontend/src/components/BatchAnalyzer.js" "2. Пакетная загрузка (BatchAnalyzer)"
check_validation "frontend/src/components/VideoAnalyzer.js" "3. Анализ видео (VideoAnalyzer)"
check_validation "frontend/src/components/MultiPhotoAnalyzer.js" "4. Мультифото анализ (MultiPhotoAnalyzer)"
check_validation "frontend/src/components/PropertyAnalyzer.js" "5. Анализ недвижимости (PropertyAnalyzer)"
check_validation "frontend/src/components/UrbanAnalyzer.js" "6. Городской контекст (UrbanAnalyzer)"
check_validation "frontend/src/components/SatelliteAnalyzer.js" "7. Спутниковый анализ (SatelliteAnalyzer)"
check_validation "frontend/src/components/OCRAnalyzer.js" "8. OCR анализ (OCRAnalyzer)"
check_validation "frontend/src/components/AnalyticsDashboard.js" "9. Аналитика (AnalyticsDashboard)"
check_validation "frontend/src/components/InteractiveMap.js" "10. Карта нарушений (InteractiveMap)"
check_validation "frontend/src/components/ModelTraining.js" "11. Обучение моделей (ModelTraining)"
check_validation "frontend/src/components/AdminPanel.js" "12. Админ панель (AdminPanel)"
check_validation "frontend/src/components/Dashboard.js" "13. Главная панель (Dashboard)"

echo ""
echo "📊 Backend endpoints:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Проверка backend endpoints
if grep -q "reference_db_service" backend/routes/violation_api.py; then
    echo -e "${GREEN}✅ /api/violations/detect - валидация интегрирована${NC}"
else
    echo -e "${YELLOW}⚠️  /api/violations/detect - валидация не найдена${NC}"
fi

if grep -q "reference_db_service" backend/routes/coordinate_api.py; then
    echo -e "${GREEN}✅ /api/coordinates/detect - валидация интегрирована${NC}"
else
    echo -e "${YELLOW}⚠️  /api/coordinates/detect - валидация не найдена${NC}"
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                   📈 СТАТИСТИКА                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"

