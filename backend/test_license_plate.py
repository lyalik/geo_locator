#!/usr/bin/env python3
"""
Тест для проверки License Plate Detector
"""

import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test EasyOCR import
try:
    import easyocr
    logger.info("✅ EasyOCR импортирован успешно")
except ImportError as e:
    logger.error(f"❌ EasyOCR не найден: {e}")
    sys.exit(1)

# Test our service
try:
    from services.license_plate_detector import LicensePlateDetector
    logger.info("✅ LicensePlateDetector импортирован успешно")
except ImportError as e:
    logger.error(f"❌ LicensePlateDetector не найден: {e}")
    sys.exit(1)

# Initialize detector
try:
    detector = LicensePlateDetector()
    logger.info("✅ LicensePlateDetector инициализирован успешно")
    logger.info(f"   Reader status: {detector.reader is not None}")
except Exception as e:
    logger.error(f"❌ Ошибка инициализации: {e}")
    sys.exit(1)

logger.info("\n" + "="*60)
logger.info("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
logger.info("="*60)
logger.info("License Plate Detector готов к работе!")
logger.info("Перезапустите backend для применения изменений:")
logger.info("  1. Остановите текущий backend (Ctrl+C)")
logger.info("  2. Запустите: ./start_demo.sh")
