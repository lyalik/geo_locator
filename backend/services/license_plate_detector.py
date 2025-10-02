"""
Сервис распознавания автомобильных номеров для определения региона
Использует EasyOCR для локального распознавания без внешних API
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
import cv2
import numpy as np

logger = logging.getLogger(__name__)

# База регионов РФ с координатами центров
RUSSIAN_REGIONS = {
    '01': {'name': 'Республика Адыгея', 'lat': 44.6098, 'lon': 40.1006},
    '02': {'name': 'Республика Башкортостан', 'lat': 54.7388, 'lon': 55.9721},
    '03': {'name': 'Республика Бурятия', 'lat': 53.5775, 'lon': 109.0380},
    '04': {'name': 'Республика Алтай', 'lat': 50.7114, 'lon': 86.1871},
    '05': {'name': 'Республика Дагестан', 'lat': 42.9849, 'lon': 47.5047},
    '06': {'name': 'Республика Ингушетия', 'lat': 43.3169, 'lon': 45.0354},
    '07': {'name': 'Кабардино-Балкарская Республика', 'lat': 43.4981, 'lon': 43.5978},
    '08': {'name': 'Республика Калмыкия', 'lat': 46.3087, 'lon': 44.2701},
    '09': {'name': 'Карачаево-Черкесская Республика', 'lat': 43.7676, 'lon': 41.9269},
    '10': {'name': 'Республика Карелия', 'lat': 63.0763, 'lon': 32.6170},
    '11': {'name': 'Республика Коми', 'lat': 64.5610, 'lon': 54.3269},
    '12': {'name': 'Республика Марий Эл', 'lat': 56.5927, 'lon': 48.0356},
    '13': {'name': 'Республика Мордовия', 'lat': 54.1838, 'lon': 45.1824},
    '14': {'name': 'Республика Саха (Якутия)', 'lat': 66.7664, 'lon': 124.1230},
    '15': {'name': 'Республика Северная Осетия — Алания', 'lat': 43.0156, 'lon': 44.6821},
    '16': {'name': 'Республика Татарстан', 'lat': 55.7964, 'lon': 49.1089},
    '17': {'name': 'Республика Тыва', 'lat': 51.7194, 'lon': 94.4502},
    '18': {'name': 'Удмуртская Республика', 'lat': 57.0166, 'lon': 53.1994},
    '19': {'name': 'Республика Хакасия', 'lat': 53.7210, 'lon': 91.4425},
    '21': {'name': 'Чувашская Республика', 'lat': 55.3791, 'lon': 47.0896},
    '22': {'name': 'Алтайский край', 'lat': 52.0406, 'lon': 84.0970},
    '23': {'name': 'Краснодарский край', 'lat': 45.0392, 'lon': 38.9766},
    '24': {'name': 'Красноярский край', 'lat': 64.2582, 'lon': 95.1533},
    '25': {'name': 'Приморский край', 'lat': 45.0677, 'lon': 134.8721},
    '26': {'name': 'Ставропольский край', 'lat': 45.0428, 'lon': 41.9734},
    '27': {'name': 'Хабаровский край', 'lat': 50.5504, 'lon': 136.6084},
    '28': {'name': 'Амурская область', 'lat': 53.6206, 'lon': 127.5343},
    '29': {'name': 'Архангельская область', 'lat': 63.5648, 'lon': 43.1165},
    '30': {'name': 'Астраханская область', 'lat': 46.3497, 'lon': 48.0408},
    '31': {'name': 'Белгородская область', 'lat': 50.6109, 'lon': 36.5867},
    '32': {'name': 'Брянская область', 'lat': 53.2434, 'lon': 34.3631},
    '33': {'name': 'Владимирская область', 'lat': 56.1439, 'lon': 40.3974},
    '34': {'name': 'Волгоградская область', 'lat': 50.4506, 'lon': 45.4697},
    '35': {'name': 'Вологодская область', 'lat': 59.2239, 'lon': 39.8843},
    '36': {'name': 'Воронежская область', 'lat': 51.6720, 'lon': 39.1843},
    '37': {'name': 'Ивановская область', 'lat': 57.0015, 'lon': 41.0150},
    '38': {'name': 'Иркутская область', 'lat': 56.1324, 'lon': 104.2606},
    '39': {'name': 'Калининградская область', 'lat': 54.7104, 'lon': 20.5120},
    '40': {'name': 'Калужская область', 'lat': 54.5109, 'lon': 36.2555},
    '41': {'name': 'Камчатский край', 'lat': 56.8343, 'lon': 160.6095},
    '42': {'name': 'Кемеровская область', 'lat': 55.3547, 'lon': 86.0861},
    '43': {'name': 'Кировская область', 'lat': 58.6035, 'lon': 49.6680},
    '44': {'name': 'Костромская область', 'lat': 58.5974, 'lon': 42.6917},
    '45': {'name': 'Курганская область', 'lat': 55.4500, 'lon': 65.3333},
    '46': {'name': 'Курская область', 'lat': 51.7373, 'lon': 36.1874},
    '47': {'name': 'Ленинградская область', 'lat': 60.0333, 'lon': 30.3000},
    '48': {'name': 'Липецкая область', 'lat': 52.6089, 'lon': 39.5704},
    '49': {'name': 'Магаданская область', 'lat': 62.6417, 'lon': 153.9486},
    '50': {'name': 'Московская область', 'lat': 55.7, 'lon': 37.5},
    '51': {'name': 'Мурманская область', 'lat': 68.9585, 'lon': 33.0827},
    '52': {'name': 'Нижегородская область', 'lat': 56.3287, 'lon': 44.0020},
    '53': {'name': 'Новгородская область', 'lat': 58.5213, 'lon': 31.2706},
    '54': {'name': 'Новосибирская область', 'lat': 55.0415, 'lon': 82.9346},
    '55': {'name': 'Омская область', 'lat': 54.9885, 'lon': 73.3242},
    '56': {'name': 'Оренбургская область', 'lat': 51.7727, 'lon': 55.0988},
    '57': {'name': 'Орловская область', 'lat': 52.9651, 'lon': 36.0785},
    '58': {'name': 'Пензенская область', 'lat': 53.2007, 'lon': 45.0046},
    '59': {'name': 'Пермский край', 'lat': 59.0144, 'lon': 56.2502},
    '60': {'name': 'Псковская область', 'lat': 57.8136, 'lon': 28.3496},
    '61': {'name': 'Ростовская область', 'lat': 47.2357, 'lon': 39.7015},
    '62': {'name': 'Рязанская область', 'lat': 54.6269, 'lon': 39.6916},
    '63': {'name': 'Самарская область', 'lat': 53.2028, 'lon': 50.1408},
    '64': {'name': 'Саратовская область', 'lat': 51.5924, 'lon': 46.0348},
    '65': {'name': 'Сахалинская область', 'lat': 50.6824, 'lon': 142.7768},
    '66': {'name': 'Свердловская область', 'lat': 56.8431, 'lon': 60.6454},
    '67': {'name': 'Смоленская область', 'lat': 54.7818, 'lon': 32.0401},
    '68': {'name': 'Тамбовская область', 'lat': 52.7213, 'lon': 41.4523},
    '69': {'name': 'Тверская область', 'lat': 56.8587, 'lon': 35.9176},
    '70': {'name': 'Томская область', 'lat': 56.4977, 'lon': 84.9744},
    '71': {'name': 'Тульская область', 'lat': 54.1961, 'lon': 37.6182},
    '72': {'name': 'Тюменская область', 'lat': 57.1531, 'lon': 65.5343},
    '73': {'name': 'Ульяновская область', 'lat': 54.3142, 'lon': 48.4031},
    '74': {'name': 'Челябинская область', 'lat': 55.1644, 'lon': 61.4368},
    '75': {'name': 'Забайкальский край', 'lat': 52.0334, 'lon': 113.4995},
    '76': {'name': 'Ярославская область', 'lat': 57.6299, 'lon': 39.8737},
    '77': {'name': 'Москва', 'lat': 55.7558, 'lon': 37.6176},
    '78': {'name': 'Санкт-Петербург', 'lat': 59.9343, 'lon': 30.3351},
    '79': {'name': 'Еврейская автономная область', 'lat': 48.7990, 'lon': 132.9253},
    '82': {'name': 'Республика Крым', 'lat': 45.0522, 'lon': 34.1021},
    '83': {'name': 'Ненецкий автономный округ', 'lat': 67.6381, 'lon': 53.0069},
    '86': {'name': 'Ханты-Мансийский автономный округ', 'lat': 61.0042, 'lon': 69.0019},
    '87': {'name': 'Чукотский автономный округ', 'lat': 66.6622, 'lon': 170.0000},
    '89': {'name': 'Ямало-Ненецкий автономный округ', 'lat': 66.5317, 'lon': 66.6141},
    '92': {'name': 'Севастополь', 'lat': 44.6167, 'lon': 33.5254},
    '95': {'name': 'Чеченская Республика', 'lat': 43.3170, 'lon': 45.6984},
    '99': {'name': 'Москва', 'lat': 55.7558, 'lon': 37.6176},
    '102': {'name': 'Республика Башкортостан', 'lat': 54.7388, 'lon': 55.9721},
    '113': {'name': 'Республика Мордовия', 'lat': 54.1838, 'lon': 45.1824},
    '116': {'name': 'Республика Татарстан', 'lat': 55.7964, 'lon': 49.1089},
    '121': {'name': 'Чувашская Республика', 'lat': 55.3791, 'lon': 47.0896},
    '123': {'name': 'Краснодарский край', 'lat': 45.0392, 'lon': 38.9766},
    '124': {'name': 'Красноярский край', 'lat': 64.2582, 'lon': 95.1533},
    '125': {'name': 'Приморский край', 'lat': 45.0677, 'lon': 134.8721},
    '126': {'name': 'Ставропольский край', 'lat': 45.0428, 'lon': 41.9734},
    '134': {'name': 'Волгоградская область', 'lat': 50.4506, 'lon': 45.4697},
    '136': {'name': 'Воронежская область', 'lat': 51.6720, 'lon': 39.1843},
    '138': {'name': 'Иркутская область', 'lat': 56.1324, 'lon': 104.2606},
    '142': {'name': 'Кемеровская область', 'lat': 55.3547, 'lon': 86.0861},
    '150': {'name': 'Московская область', 'lat': 55.7, 'lon': 37.5},
    '152': {'name': 'Нижегородская область', 'lat': 56.3287, 'lon': 44.0020},
    '154': {'name': 'Новосибирская область', 'lat': 55.0415, 'lon': 82.9346},
    '159': {'name': 'Пермский край', 'lat': 59.0144, 'lon': 56.2502},
    '161': {'name': 'Ростовская область', 'lat': 47.2357, 'lon': 39.7015},
    '163': {'name': 'Самарская область', 'lat': 53.2028, 'lon': 50.1408},
    '164': {'name': 'Саратовская область', 'lat': 51.5924, 'lon': 46.0348},
    '166': {'name': 'Свердловская область', 'lat': 56.8431, 'lon': 60.6454},
    '174': {'name': 'Челябинская область', 'lat': 55.1644, 'lon': 61.4368},
    '177': {'name': 'Москва', 'lat': 55.7558, 'lon': 37.6176},
    '178': {'name': 'Санкт-Петербург', 'lat': 59.9343, 'lon': 30.3351},
    '197': {'name': 'Москва', 'lat': 55.7558, 'lon': 37.6176},
    '199': {'name': 'Москва', 'lat': 55.7558, 'lon': 37.6176},
    '750': {'name': 'Московская область', 'lat': 55.7, 'lon': 37.5},
    '777': {'name': 'Москва', 'lat': 55.7558, 'lon': 37.6176},
    '790': {'name': 'Московская область', 'lat': 55.7, 'lon': 37.5},
    '797': {'name': 'Москва', 'lat': 55.7558, 'lon': 37.6176},
    '799': {'name': 'Москва', 'lat': 55.7558, 'lon': 37.6176}
}


class LicensePlateDetector:
    """
    Детектор автомобильных номеров с определением региона РФ
    """
    
    def __init__(self):
        """Инициализация детектора"""
        self.reader = None
        self._init_ocr()
        
    def _init_ocr(self):
        """Ленивая инициализация EasyOCR"""
        try:
            import easyocr
            self.reader = easyocr.Reader(['ru', 'en'], gpu=False)
            logger.info("✅ EasyOCR initialized for license plate detection")
        except ImportError:
            logger.warning("⚠️ EasyOCR not installed. Install: pip install easyocr")
            self.reader = None
        except Exception as e:
            logger.error(f"Failed to initialize EasyOCR: {e}")
            self.reader = None
    
    def detect_license_plates(self, image_path: str) -> Dict[str, Any]:
        """
        Определение координат по автомобильным номерам на фото
        
        Args:
            image_path: Путь к изображению
            
        Returns:
            Результат с координатами региона или None
        """
        if not self.reader:
            return {
                'success': False,
                'error': 'EasyOCR not available'
            }
        
        try:
            # Читаем изображение
            image = cv2.imread(image_path)
            if image is None:
                return {'success': False, 'error': 'Failed to load image'}
            
            # Распознаем текст
            results = self.reader.readtext(image)
            
            if not results:
                return {
                    'success': False,
                    'plates_found': 0,
                    'message': 'No text detected on image'
                }
            
            # Ищем автомобильные номера
            detected_plates = []
            for (bbox, text, confidence) in results:
                # Проверяем паттерн российского номера
                plate_info = self._parse_russian_plate(text, confidence)
                if plate_info:
                    detected_plates.append(plate_info)
            
            if not detected_plates:
                return {
                    'success': False,
                    'plates_found': 0,
                    'message': 'No license plates detected'
                }
            
            # Берем номер с наибольшей уверенностью
            best_plate = max(detected_plates, key=lambda x: x['confidence'])
            
            region_code = best_plate['region']
            region_info = RUSSIAN_REGIONS.get(region_code)
            
            if not region_info:
                return {
                    'success': False,
                    'plates_found': len(detected_plates),
                    'detected_region': region_code,
                    'message': f'Unknown region code: {region_code}'
                }
            
            logger.info(f"🚗 Detected license plate: {best_plate['plate']} → {region_info['name']}")
            
            return {
                'success': True,
                'plates_found': len(detected_plates),
                'plate': best_plate['plate'],
                'region_code': region_code,
                'region_name': region_info['name'],
                'coordinates': {
                    'latitude': region_info['lat'],
                    'longitude': region_info['lon'],
                    'source': 'license_plate',
                    'confidence': best_plate['confidence'],
                    'detected_plate': best_plate['plate']
                },
                'all_plates': detected_plates
            }
            
        except Exception as e:
            logger.error(f"Error detecting license plates: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _parse_russian_plate(self, text: str, confidence: float) -> Optional[Dict[str, Any]]:
        """
        Парсинг российского автомобильного номера
        
        Форматы:
        - А123АА77 (стандартный)
        - А123АА777 (новый формат)
        - А 123 АА 77 (с пробелами)
        """
        # Убираем пробелы и приводим к верхнему регистру
        clean_text = text.replace(' ', '').upper()
        
        # Паттерны российских номеров
        patterns = [
            # Стандартный формат: А123АА77
            r'^([АВЕКМНОРСТУХ])(\d{3})([АВЕКМНОРСТУХ]{2})(\d{2,3})$',
            # С латинскими буквами (OCR может спутать)
            r'^([ABEKMHOPCTYX])(\d{3})([ABEKMHOPCTYX]{2})(\d{2,3})$'
        ]
        
        for pattern in patterns:
            match = re.match(pattern, clean_text)
            if match:
                letter1, numbers, letters2, region = match.groups()
                
                # Нормализуем буквы (русские)
                letter1 = self._normalize_letter(letter1)
                letters2 = ''.join([self._normalize_letter(l) for l in letters2])
                
                # Формируем номер
                plate = f"{letter1}{numbers}{letters2}{region}"
                
                return {
                    'plate': plate,
                    'region': region,
                    'confidence': confidence
                }
        
        return None
    
    def _normalize_letter(self, letter: str) -> str:
        """Конвертация латинских букв в русские (для OCR ошибок)"""
        latin_to_cyrillic = {
            'A': 'А', 'B': 'В', 'E': 'Е', 'K': 'К',
            'M': 'М', 'H': 'Н', 'O': 'О', 'P': 'Р',
            'C': 'С', 'T': 'Т', 'Y': 'У', 'X': 'Х'
        }
        return latin_to_cyrillic.get(letter, letter)
