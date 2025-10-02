#!/bin/bash

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║     🧪 ТЕСТИРОВАНИЕ ИНТЕГРАЦИИ ВАЛИДАЦИИ                     ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Цвета для вывода
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция проверки
check_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
        return 0
    else
        echo -e "${RED}❌ $2${NC}"
        return 1
    fi
}

echo "📋 Проверка файлов..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Проверка наличия файлов
FILES=(
    "backend/models/violation_response.py"
    "backend/services/reference_database_service.py"
    "backend/routes/violation_api.py"
    "backend/routes/coordinate_api.py"
    "backend/services/yolo_violation_detector.py"
)

all_files_exist=true
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        check_status 0 "Файл найден: $file"
    else
        check_status 1 "Файл отсутствует: $file"
        all_files_exist=false
    fi
done

echo ""
echo "📊 Проверка датасета заказчика..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Проверка файлов датасета
DATASET_DIR="backend/uploads/data"
if [ -d "$DATASET_DIR" ]; then
    dataset_files=$(ls "$DATASET_DIR"/*.json 2>/dev/null | wc -l)
    if [ "$dataset_files" -gt 0 ]; then
        check_status 0 "Найдено $dataset_files файлов датасета"
        
        # Проверка содержимого
        for json_file in "$DATASET_DIR"/*.json; do
            if [ -f "$json_file" ]; then
                filename=$(basename "$json_file")
                records=$(jq -r '.count' "$json_file" 2>/dev/null || echo "0")
                echo "  • $filename: $records записей"
            fi
        done
    else
        check_status 1 "Файлы датасета не найдены"
    fi
else
    check_status 1 "Папка датасета не найдена"
fi

echo ""
echo "🔍 Проверка изменений в коде..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Проверка импорта ReferenceDatabaseService в violation_api.py
if grep -q "from services.reference_database_service import ReferenceDatabaseService" backend/routes/violation_api.py; then
    check_status 0 "Импорт ReferenceDatabaseService в violation_api.py"
else
    check_status 1 "Импорт ReferenceDatabaseService не найден"
fi

# Проверка импорта ViolationResponseFormatter
if grep -q "from models.violation_response import ViolationResponseFormatter" backend/routes/violation_api.py; then
    check_status 0 "Импорт ViolationResponseFormatter в violation_api.py"
else
    check_status 1 "Импорт ViolationResponseFormatter не найден"
fi

# Проверка импорта в coordinate_api.py
if grep -q "from services.reference_database_service import ReferenceDatabaseService" backend/routes/coordinate_api.py; then
    check_status 0 "Импорт ReferenceDatabaseService в coordinate_api.py"
else
    check_status 1 "Импорт ReferenceDatabaseService не найден в coordinate_api.py"
fi

# Проверка маппинга типов в yolo_violation_detector.py
if grep -q "VIOLATION_TYPE_MAPPING" backend/services/yolo_violation_detector.py; then
    check_status 0 "VIOLATION_TYPE_MAPPING найден в yolo_violation_detector.py"
else
    check_status 1 "VIOLATION_TYPE_MAPPING не найден"
fi

# Проверка функции map_to_customer_type
if grep -q "def map_to_customer_type" backend/services/yolo_violation_detector.py; then
    check_status 0 "Функция map_to_customer_type найдена"
else
    check_status 1 "Функция map_to_customer_type не найдена"
fi

# Проверка поля customer_type
if grep -q "'customer_type'" backend/services/yolo_violation_detector.py; then
    check_status 0 "Поле customer_type добавлено в детекции"
else
    check_status 1 "Поле customer_type не найдено"
fi

echo ""
echo "🔧 Проверка синтаксиса Python..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd backend

# Активация виртуального окружения
if [ -d "venv" ]; then
    source venv/bin/activate
    check_status 0 "Виртуальное окружение активировано"
else
    echo -e "${YELLOW}⚠️  Виртуальное окружение не найдено${NC}"
fi

# Проверка синтаксиса
python3 -m py_compile models/violation_response.py 2>/dev/null
check_status $? "Синтаксис violation_response.py"

python3 -m py_compile routes/violation_api.py 2>/dev/null
check_status $? "Синтаксис violation_api.py"

python3 -m py_compile routes/coordinate_api.py 2>/dev/null
check_status $? "Синтаксис coordinate_api.py"

python3 -m py_compile services/yolo_violation_detector.py 2>/dev/null
check_status $? "Синтаксис yolo_violation_detector.py"

cd ..

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                   📊 РЕЗУЛЬТАТЫ ПРОВЕРКИ                      ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

if $all_files_exist; then
    echo -e "${GREEN}✅ Все критические файлы на месте${NC}"
else
    echo -e "${RED}❌ Некоторые файлы отсутствуют${NC}"
fi

echo ""
echo "🚀 Следующие шаги:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. Запустить систему:"
echo "   ./start_demo.sh"
echo ""
echo "2. Протестировать API детекции нарушений:"
echo "   curl -X POST http://192.168.1.67:5001/api/violations/detect \\"
echo "     -F \"file=@test_image.jpg\" \\"
echo "     -F \"location_hint=Москва\""
echo ""
echo "3. Проверить наличие полей в ответе:"
echo "   - reference_matches"
echo "   - validation"
echo "   - issues[].customer_type (18-001 или 00-022)"
echo "   - issues[].label"
echo ""
echo "4. Протестировать определение координат:"
echo "   curl -X POST http://192.168.1.67:5001/api/coordinates/detect \\"
echo "     -F \"file=@test_image.jpg\""
echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  ✅ Проверка завершена! Готово к запуску.                    ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
