#!/bin/bash

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║   🧪 ТЕСТИРОВАНИЕ API ВАЛИДАЦИИ С ДАТАСЕТОМ ЗАКАЗЧИКА        ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Цвета
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

API_URL="http://192.168.1.67:5001"

echo -e "${BLUE}📋 Тест 1: Проверка здоровья системы${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -s "${API_URL}/health" | jq '.'
echo ""

echo -e "${BLUE}📊 Тест 2: Статистика сервисов${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -s "${API_URL}/api/geo/stats" | jq '.services.reference_database'
echo ""

echo -e "${BLUE}🔍 Тест 3: Загрузка изображения с координатами Москвы${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Создаём тестовое изображение..."

# Проверяем наличие тестового изображения
TEST_IMAGE="backend/test_image.jpg"
if [ ! -f "$TEST_IMAGE" ]; then
    # Ищем любое изображение в uploads
    TEST_IMAGE=$(find backend/uploads/violations -name "*.jpg" -o -name "*.png" | head -1)
    if [ -z "$TEST_IMAGE" ]; then
        echo -e "${YELLOW}⚠️  Тестовое изображение не найдено. Пропускаем тест загрузки.${NC}"
    fi
fi

if [ -f "$TEST_IMAGE" ]; then
    echo "Используем изображение: $TEST_IMAGE"
    echo ""
    echo "Загружаем изображение с подсказкой 'Москва, Красная площадь'..."
    
    RESPONSE=$(curl -s -X POST "${API_URL}/api/violations/detect" \
      -F "file=@${TEST_IMAGE}" \
      -F "location_hint=Москва, Красная площадь")
    
    echo ""
    echo "📄 ОТВЕТ API:"
    echo "$RESPONSE" | jq '.'
    
    echo ""
    echo -e "${GREEN}✅ Проверка полей в ответе:${NC}"
    
    # Проверка наличия ключевых полей
    HAS_ISSUES=$(echo "$RESPONSE" | jq -r '.issues // empty')
    HAS_REF_MATCHES=$(echo "$RESPONSE" | jq -r '.reference_matches // empty')
    HAS_VALIDATION=$(echo "$RESPONSE" | jq -r '.validation // empty')
    HAS_CUSTOMER_TYPE=$(echo "$RESPONSE" | jq -r '.issues[0].customer_type // empty')
    HAS_LABEL=$(echo "$RESPONSE" | jq -r '.issues[0].label // empty')
    
    if [ ! -z "$HAS_ISSUES" ]; then
        echo -e "${GREEN}✅ issues: найдено${NC}"
        ISSUES_COUNT=$(echo "$RESPONSE" | jq -r '.issues | length')
        echo "   Количество: $ISSUES_COUNT"
    else
        echo -e "${YELLOW}⚠️  issues: не найдено${NC}"
    fi
    
    if [ ! -z "$HAS_CUSTOMER_TYPE" ]; then
        echo -e "${GREEN}✅ customer_type: $HAS_CUSTOMER_TYPE${NC}"
    else
        echo -e "${YELLOW}⚠️  customer_type: не найдено${NC}"
    fi
    
    if [ ! -z "$HAS_LABEL" ]; then
        echo -e "${GREEN}✅ label: $HAS_LABEL${NC}"
    else
        echo -e "${YELLOW}⚠️  label: не найдено${NC}"
    fi
    
    if [ ! -z "$HAS_REF_MATCHES" ]; then
        REF_COUNT=$(echo "$RESPONSE" | jq -r '.reference_matches | length')
        echo -e "${GREEN}✅ reference_matches: найдено ($REF_COUNT совпадений)${NC}"
        
        # Показываем первое совпадение
        if [ "$REF_COUNT" -gt 0 ]; then
            echo ""
            echo "📍 Первое совпадение:"
            echo "$RESPONSE" | jq -r '.reference_matches[0] | "   Тип: \(.violation_type), Расстояние: \(.distance_km)км, Уверенность: \(.confidence)"'
        fi
    else
        echo -e "${YELLOW}⚠️  reference_matches: не найдено (может быть вне радиуса 50м)${NC}"
    fi
    
    if [ ! -z "$HAS_VALIDATION" ]; then
        VALIDATED=$(echo "$RESPONSE" | jq -r '.validation.validated // false')
        SCORE=$(echo "$RESPONSE" | jq -r '.validation.validation_score // 0')
        MESSAGE=$(echo "$RESPONSE" | jq -r '.validation.message // "N/A"')
        
        echo -e "${GREEN}✅ validation: найдено${NC}"
        echo "   Validated: $VALIDATED"
        echo "   Score: $SCORE"
        echo "   Message: $MESSAGE"
    else
        echo -e "${YELLOW}⚠️  validation: не найдено${NC}"
    fi
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                  📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ                   ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "✅ Система готова к тестированию через фронтенд!"
echo ""
echo "🌐 Откройте браузер:"
echo "   http://192.168.1.67:3000"
echo ""
echo "📸 Загрузите изображение с координатами в Москве:"
echo "   1. Перейдите в раздел 'Детекция нарушений'"
echo "   2. Загрузите фото"
echo "   3. Укажите адрес: 'Москва, Красная площадь'"
echo "   4. Нажмите 'Начать анализ'"
echo ""
echo "🔍 Что проверить в результатах:"
echo "   ✓ Тип нарушения: 18-001 или 00-022"
echo "   ✓ Блок 'Валидация по готовой базе заказчика'"
echo "   ✓ Список совпадений в базе (если есть)"
echo "   ✓ Степень валидации (%)"
echo "   ✓ Совпадение координат и типа"
echo ""
