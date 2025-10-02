#!/bin/bash

echo "🔧 ПРИМЕНЕНИЕ ПАТЧА: Интеграция валидации по готовой базе"
echo "==========================================================="
echo ""

# Проверка наличия файлов
echo "📋 Проверка файлов..."

if [ ! -f "backend/models/violation_response.py" ]; then
    echo "❌ Файл violation_response.py не найден!"
    echo "   Он должен быть создан автоматически"
    exit 1
fi

if [ ! -f "backend/services/reference_database_service.py" ]; then
    echo "❌ Файл reference_database_service.py не найден!"
    exit 1
fi

echo "✅ Все необходимые файлы найдены"
echo ""

# Резервные копии
echo "💾 Создание резервных копий..."
mkdir -p backup_$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"

cp backend/routes/violation_api.py "$BACKUP_DIR/violation_api.py.bak"
cp backend/routes/coordinate_api.py "$BACKUP_DIR/coordinate_api.py.bak"
cp backend/services/yolo_violation_detector.py "$BACKUP_DIR/yolo_violation_detector.py.bak"

echo "✅ Резервные копии созданы в $BACKUP_DIR"
echo ""

# Проверка датасета
echo "📊 Проверка датасета заказчика..."
DATASET_FILES=$(ls backend/uploads/data/*.json 2>/dev/null | wc -l)

if [ "$DATASET_FILES" -gt 0 ]; then
    echo "✅ Найдено $DATASET_FILES файлов датасета"
else
    echo "⚠️  Файлы датасета не найдены в backend/uploads/data/"
    echo "   Скопируйте JSON файлы датасета в эту папку"
fi
echo ""

echo "📝 СЛЕДУЮЩИЕ ШАГИ:"
echo ""
echo "1. Откройте backend/routes/violation_api.py"
echo "   Добавьте импорты (см. ПАТЧ_ИНТЕГРАЦИЯ_ВАЛИДАЦИИ.md)"
echo ""
echo "2. Обновите функцию detect_violations()"
echo "   Замените блок response_data (см. патч)"
echo ""
echo "3. Обновите backend/services/yolo_violation_detector.py"
echo "   Добавьте VIOLATION_TYPE_MAPPING"
echo ""
echo "4. Перезапустите backend:"
echo "   cd backend && source venv/bin/activate && python app.py"
echo ""
echo "5. Протестируйте API:"
echo "   curl -X POST http://192.168.1.67:5001/api/violations/detect -F 'file=@test.jpg'"
echo ""
echo "==========================================================="
echo "📖 Полная инструкция: ПАТЧ_ИНТЕГРАЦИЯ_ВАЛИДАЦИИ.md"
echo "📖 Подробный аудит: ПОЛНЫЙ_АУДИТ_СИСТЕМЫ.md"
echo "==========================================================="

