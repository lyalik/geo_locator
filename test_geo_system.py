#!/usr/bin/env python3
"""
Комплексное тестирование геолокационной системы
"""
import os
import sys
import json
import requests
import logging
from datetime import datetime

# Добавляем путь к backend модулям
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.geo_aggregator_service import GeoAggregatorService
from backend.services.yandex_maps_service import YandexMapsService
from backend.services.dgis_service import DGISService
from backend.services.roscosmos_satellite_service import RoscosmosService
from backend.services.yandex_satellite_service import YandexSatelliteService
from backend.services.image_database_service import ImageDatabaseService

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GeoSystemTester:
    """Тестирование всех компонентов геолокационной системы"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'summary': {'passed': 0, 'failed': 0, 'total': 0}
        }
        
        # Тестовые координаты (Москва, Красная площадь)
        self.test_lat = 55.7558
        self.test_lon = 37.6176
        self.test_address = "Москва, Красная площадь"
        
    def run_all_tests(self):
        """Запуск всех тестов"""
        logger.info("🚀 Начинаем комплексное тестирование геолокационной системы")
        
        # Тесты отдельных сервисов
        self.test_yandex_maps_service()
        self.test_dgis_service()
        self.test_roscosmos_service()
        self.test_yandex_satellite_service()
        self.test_image_database_service()
        
        # Тест главного агрегатора
        self.test_geo_aggregator_service()
        
        # Тест API endpoints
        self.test_api_endpoints()
        
        # Выводим итоги
        self.print_summary()
        
        return self.results
    
    def test_yandex_maps_service(self):
        """Тест Yandex Maps сервиса"""
        test_name = "Yandex Maps Service"
        logger.info(f"🔍 Тестируем {test_name}")
        
        try:
            service = YandexMapsService()
            
            # Тест поиска мест
            search_result = service.search_places("кафе", self.test_lat, self.test_lon)
            
            # Тест геокодирования
            geocode_result = service.geocode(self.test_address)
            
            # Тест обратного геокодирования
            reverse_result = service.reverse_geocode(self.test_lat, self.test_lon)
            
            # Тест статической карты
            map_result = service.get_static_map(self.test_lat, self.test_lon)
            
            success = (
                search_result.get('source') == 'yandex_maps' and
                geocode_result.get('source') == 'yandex_geocoder' and
                reverse_result.get('source') == 'yandex_geocoder' and
                map_result.get('source') == 'yandex_static_map'
            )
            
            self.results['tests'][test_name] = {
                'status': 'PASSED' if success else 'FAILED',
                'details': {
                    'search': search_result.get('success', False),
                    'geocode': geocode_result.get('success', False),
                    'reverse_geocode': reverse_result.get('success', False),
                    'static_map': map_result.get('success', False)
                }
            }
            
            if success:
                self.results['summary']['passed'] += 1
                logger.info(f"✅ {test_name} - PASSED")
            else:
                self.results['summary']['failed'] += 1
                logger.error(f"❌ {test_name} - FAILED")
                
        except Exception as e:
            self.results['tests'][test_name] = {
                'status': 'ERROR',
                'error': str(e)
            }
            self.results['summary']['failed'] += 1
            logger.error(f"💥 {test_name} - ERROR: {e}")
        
        self.results['summary']['total'] += 1
    
    def test_dgis_service(self):
        """Тест 2GIS сервиса"""
        test_name = "2GIS Service"
        logger.info(f"🔍 Тестируем {test_name}")
        
        try:
            service = DGISService()
            
            # Тест поиска мест
            search_result = service.search_places("ресторан", self.test_lat, self.test_lon)
            
            # Тест геокодирования
            geocode_result = service.geocode(self.test_address)
            
            # Тест обратного геокодирования
            reverse_result = service.reverse_geocode(self.test_lat, self.test_lon)
            
            # Тест поиска ближайших мест
            nearby_result = service.find_nearby_places(self.test_lat, self.test_lon, "кафе")
            
            success = (
                search_result.get('source') == '2gis' and
                geocode_result.get('source') == '2gis' and
                reverse_result.get('source') == '2gis' and
                nearby_result.get('source') == '2gis'
            )
            
            self.results['tests'][test_name] = {
                'status': 'PASSED' if success else 'FAILED',
                'details': {
                    'search': search_result.get('success', False),
                    'geocode': geocode_result.get('success', False),
                    'reverse_geocode': reverse_result.get('success', False),
                    'nearby': nearby_result.get('success', False)
                }
            }
            
            if success:
                self.results['summary']['passed'] += 1
                logger.info(f"✅ {test_name} - PASSED")
            else:
                self.results['summary']['failed'] += 1
                logger.error(f"❌ {test_name} - FAILED")
                
        except Exception as e:
            self.results['tests'][test_name] = {
                'status': 'ERROR',
                'error': str(e)
            }
            self.results['summary']['failed'] += 1
            logger.error(f"💥 {test_name} - ERROR: {e}")
        
        self.results['summary']['total'] += 1
    
    def test_roscosmos_service(self):
        """Тест Роскосмос спутникового сервиса"""
        test_name = "Roscosmos Satellite Service"
        logger.info(f"🔍 Тестируем {test_name}")
        
        try:
            service = RoscosmosService()
            
            # Тест получения спутникового снимка
            satellite_result = service.get_satellite_image(self.test_lat, self.test_lon)
            
            # Тест поиска архивных снимков
            archive_result = service.search_archive(
                self.test_lat, self.test_lon, 
                "2023-01-01", "2023-12-31"
            )
            
            # Тест информации о спутниках
            info_result = service.get_satellite_info()
            
            success = (
                satellite_result.get('source') in ['roscosmos_geoportal', 'scanex_kosmosnimki', 'public_satellite'] and
                archive_result.get('source') == 'roscosmos_archive' and
                info_result.get('success', False)
            )
            
            self.results['tests'][test_name] = {
                'status': 'PASSED' if success else 'FAILED',
                'details': {
                    'satellite_image': satellite_result.get('success', False),
                    'archive_search': archive_result.get('success', False),
                    'satellite_info': info_result.get('success', False),
                    'preferred_source': satellite_result.get('source', 'none')
                }
            }
            
            if success:
                self.results['summary']['passed'] += 1
                logger.info(f"✅ {test_name} - PASSED")
            else:
                self.results['summary']['failed'] += 1
                logger.error(f"❌ {test_name} - FAILED")
                
        except Exception as e:
            self.results['tests'][test_name] = {
                'status': 'ERROR',
                'error': str(e)
            }
            self.results['summary']['failed'] += 1
            logger.error(f"💥 {test_name} - ERROR: {e}")
        
        self.results['summary']['total'] += 1
    
    def test_yandex_satellite_service(self):
        """Тест Яндекс Спутник сервиса"""
        test_name = "Yandex Satellite Service"
        logger.info(f"🔍 Тестируем {test_name}")
        
        try:
            service = YandexSatelliteService()
            
            # Тест получения спутникового снимка
            satellite_result = service.get_satellite_image(self.test_lat, self.test_lon)
            
            # Тест гибридного изображения
            hybrid_result = service.get_hybrid_image(self.test_lat, self.test_lon)
            
            # Тест информации о сервисе
            info_result = service.get_service_info()
            
            success = (
                satellite_result.get('source') == 'yandex_satellite' and
                hybrid_result.get('source') == 'yandex_satellite' and
                info_result.get('success', False)
            )
            
            self.results['tests'][test_name] = {
                'status': 'PASSED' if success else 'FAILED',
                'details': {
                    'satellite_image': satellite_result.get('success', False),
                    'hybrid_image': hybrid_result.get('success', False),
                    'service_info': info_result.get('success', False)
                }
            }
            
            if success:
                self.results['summary']['passed'] += 1
                logger.info(f"✅ {test_name} - PASSED")
            else:
                self.results['summary']['failed'] += 1
                logger.error(f"❌ {test_name} - FAILED")
                
        except Exception as e:
            self.results['tests'][test_name] = {
                'status': 'ERROR',
                'error': str(e)
            }
            self.results['summary']['failed'] += 1
            logger.error(f"💥 {test_name} - ERROR: {e}")
        
        self.results['summary']['total'] += 1
    
    def test_image_database_service(self):
        """Тест сервиса базы данных изображений"""
        test_name = "Image Database Service"
        logger.info(f"🔍 Тестируем {test_name}")
        
        try:
            service = ImageDatabaseService()
            
            # Тест подключения к базе данных
            connection_ok = hasattr(service, 'session') and service.session is not None
            
            # Тест поиска похожих изображений
            similar_result = service.find_similar_images(self.test_lat, self.test_lon, 1000)
            
            success = connection_ok and isinstance(similar_result, list)
            
            self.results['tests'][test_name] = {
                'status': 'PASSED' if success else 'FAILED',
                'details': {
                    'database_connection': connection_ok,
                    'similar_search': isinstance(similar_result, list),
                    'similar_count': len(similar_result) if isinstance(similar_result, list) else 0
                }
            }
            
            if success:
                self.results['summary']['passed'] += 1
                logger.info(f"✅ {test_name} - PASSED")
            else:
                self.results['summary']['failed'] += 1
                logger.error(f"❌ {test_name} - FAILED")
                
        except Exception as e:
            self.results['tests'][test_name] = {
                'status': 'ERROR',
                'error': str(e)
            }
            self.results['summary']['failed'] += 1
            logger.error(f"💥 {test_name} - ERROR: {e}")
        
        self.results['summary']['total'] += 1
    
    def test_geo_aggregator_service(self):
        """Тест главного агрегатора геолокации"""
        test_name = "Geo Aggregator Service"
        logger.info(f"🔍 Тестируем {test_name}")
        
        try:
            service = GeoAggregatorService()
            
            # Тест получения статистики
            stats_result = service.get_location_statistics()
            
            # Тест получения лучшего спутникового снимка
            satellite_result = service._get_best_satellite_image(self.test_lat, self.test_lon)
            
            success = (
                'available_services' in stats_result and
                satellite_result.get('success', False)
            )
            
            self.results['tests'][test_name] = {
                'status': 'PASSED' if success else 'FAILED',
                'details': {
                    'statistics': 'available_services' in stats_result,
                    'satellite_integration': satellite_result.get('success', False),
                    'services': stats_result.get('available_services', {})
                }
            }
            
            if success:
                self.results['summary']['passed'] += 1
                logger.info(f"✅ {test_name} - PASSED")
            else:
                self.results['summary']['failed'] += 1
                logger.error(f"❌ {test_name} - FAILED")
                
        except Exception as e:
            self.results['tests'][test_name] = {
                'status': 'ERROR',
                'error': str(e)
            }
            self.results['summary']['failed'] += 1
            logger.error(f"💥 {test_name} - ERROR: {e}")
        
        self.results['summary']['total'] += 1
    
    def test_api_endpoints(self):
        """Тест API endpoints (требует запущенного сервера)"""
        test_name = "API Endpoints"
        logger.info(f"🔍 Тестируем {test_name}")
        
        try:
            base_url = "http://localhost:5000"
            
            # Тест health endpoint
            health_response = requests.get(f"{base_url}/api/geo/health", timeout=5)
            health_ok = health_response.status_code == 200
            
            # Тест статистики
            stats_response = requests.get(f"{base_url}/api/geo/statistics", timeout=5)
            stats_ok = stats_response.status_code in [200, 401]  # 401 если требуется авторизация
            
            success = health_ok
            
            self.results['tests'][test_name] = {
                'status': 'PASSED' if success else 'FAILED',
                'details': {
                    'health_endpoint': health_ok,
                    'statistics_endpoint': stats_ok,
                    'server_running': health_ok
                }
            }
            
            if success:
                self.results['summary']['passed'] += 1
                logger.info(f"✅ {test_name} - PASSED")
            else:
                self.results['summary']['failed'] += 1
                logger.error(f"❌ {test_name} - FAILED")
                
        except requests.exceptions.ConnectionError:
            self.results['tests'][test_name] = {
                'status': 'SKIPPED',
                'reason': 'Server not running on localhost:5000'
            }
            logger.warning(f"⚠️ {test_name} - SKIPPED (server not running)")
        except Exception as e:
            self.results['tests'][test_name] = {
                'status': 'ERROR',
                'error': str(e)
            }
            self.results['summary']['failed'] += 1
            logger.error(f"💥 {test_name} - ERROR: {e}")
        
        self.results['summary']['total'] += 1
    
    def print_summary(self):
        """Вывод итогов тестирования"""
        logger.info("\n" + "="*60)
        logger.info("📊 ИТОГИ ТЕСТИРОВАНИЯ ГЕОЛОКАЦИОННОЙ СИСТЕМЫ")
        logger.info("="*60)
        
        total = self.results['summary']['total']
        passed = self.results['summary']['passed']
        failed = self.results['summary']['failed']
        
        logger.info(f"Всего тестов: {total}")
        logger.info(f"Пройдено: {passed} ✅")
        logger.info(f"Провалено: {failed} ❌")
        logger.info(f"Успешность: {(passed/total*100):.1f}%" if total > 0 else "0%")
        
        logger.info("\nДетали по тестам:")
        for test_name, result in self.results['tests'].items():
            status_emoji = {
                'PASSED': '✅',
                'FAILED': '❌',
                'ERROR': '💥',
                'SKIPPED': '⚠️'
            }.get(result['status'], '❓')
            
            logger.info(f"{status_emoji} {test_name}: {result['status']}")
            
            if 'details' in result:
                for key, value in result['details'].items():
                    logger.info(f"    {key}: {value}")
        
        logger.info("="*60)
        
        # Сохраняем результаты в файл
        with open('test_results.json', 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        logger.info("📄 Результаты сохранены в test_results.json")


if __name__ == "__main__":
    tester = GeoSystemTester()
    results = tester.run_all_tests()
    
    # Возвращаем код выхода в зависимости от результатов
    if results['summary']['failed'] == 0:
        sys.exit(0)  # Все тесты прошли
    else:
        sys.exit(1)  # Есть проваленные тесты
