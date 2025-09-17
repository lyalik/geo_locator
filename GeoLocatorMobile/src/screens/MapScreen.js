import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Alert,
  TouchableOpacity,
  Modal,
  ScrollView,
  ActivityIndicator,
  Dimensions
} from 'react-native';
import * as Location from 'expo-location';
import { Ionicons } from '@expo/vector-icons';
import ApiService from '../services/ApiService';
import YandexMapView from '../components/YandexMapView';

const { width, height } = Dimensions.get('window');

export default function MapScreen() {
  const [location, setLocation] = useState(null);
  const [violations, setViolations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedViolation, setSelectedViolation] = useState(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [showOSMContext, setShowOSMContext] = useState(false);
  const [mapType, setMapType] = useState('standard'); // standard, satellite, hybrid
  const [showMapTypeSelector, setShowMapTypeSelector] = useState(false);
  const [osmBuildings, setOsmBuildings] = useState([]);
  const [loadingOSM, setLoadingOSM] = useState(false);
  const [mapRegion, setMapRegion] = useState({
    latitude: 45.0355, // Краснодар по умолчанию
    longitude: 38.9753,
    latitudeDelta: 0.0922,
    longitudeDelta: 0.0421,
  });

  useEffect(() => {
    initializeMap();
  }, []);

  const initializeMap = async () => {
    await getCurrentLocation();
    await loadViolations();
  };

  const getCurrentLocation = async () => {
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Ошибка', 'Необходимо разрешение на доступ к геолокации');
        return;
      }

      const currentLocation = await Location.getCurrentPositionAsync({});
      const userLocation = {
        latitude: currentLocation.coords.latitude,
        longitude: currentLocation.coords.longitude,
      };
      
      setLocation(userLocation);
      setMapRegion({
        ...userLocation,
        latitudeDelta: 0.01,
        longitudeDelta: 0.01,
      });
    } catch (error) {
      console.error('Ошибка получения геолокации:', error);
      Alert.alert('Ошибка', 'Не удалось определить ваше местоположение');
    }
  };

  const centerOnUserLocation = async () => {
    try {
      console.log('📍 Центрирование на пользователе...');
      setLoading(true);
      
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Ошибка', 'Необходимо разрешение на доступ к геолокации');
        return;
      }

      const currentLocation = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.High,
      });
      
      const userLocation = {
        latitude: currentLocation.coords.latitude,
        longitude: currentLocation.coords.longitude,
      };
      
      console.log('📍 Местоположение пользователя:', userLocation);
      
      setLocation(userLocation);
      setMapRegion({
        ...userLocation,
        latitudeDelta: 0.01,
        longitudeDelta: 0.01,
      });
      
      Alert.alert('Успех', 'Карта центрирована на вашем местоположении');
    } catch (error) {
      console.error('❌ Ошибка центрирования на пользователе:', error);
      Alert.alert('Ошибка', 'Не удалось определить ваше местоположение');
    } finally {
      setLoading(false);
    }
  };

  const searchLocation = async () => {
    Alert.prompt(
      'Поиск места',
      'Введите адрес или название места:',
      [
        { text: 'Отмена', style: 'cancel' },
        { 
          text: 'Найти', 
          onPress: async (searchText) => {
            if (!searchText) return;
            
            try {
              setLoading(true);
              const response = await ApiService.geocodeAddress(searchText);
              
              if (response.success && response.data && response.data.length > 0) {
                const result = response.data[0];
                const newRegion = {
                  latitude: result.latitude,
                  longitude: result.longitude,
                  latitudeDelta: 0.01,
                  longitudeDelta: 0.01,
                };
                setMapRegion(newRegion);
                Alert.alert('Найдено', `Место найдено: ${result.address || searchText}`);
              } else {
                Alert.alert('Не найдено', 'Место не найдено. Попробуйте другой запрос.');
              }
            } catch (error) {
              console.error('Ошибка поиска:', error);
              Alert.alert('Ошибка', 'Не удалось выполнить поиск');
            } finally {
              setLoading(false);
            }
          }
        }
      ],
      'plain-text'
    );
  };

  const loadViolations = async () => {
    try {
      setLoading(true);
      const response = await ApiService.getViolationsWithCoordinates();
      
      if (response.success && response.data) {
        // Обрабатываем данные нарушений
        const violationsWithCoords = response.data.map(item => ({
          id: item.violation_id || item.id,
          category: item.category || 'Нарушение',
          confidence: item.confidence || 0,
          latitude: parseFloat(item.latitude),
          longitude: parseFloat(item.longitude),
          created_at: item.created_at || item.timestamp,
          address: item.address || '',
          source: item.source || 'system'
        })).filter(item => 
          item.latitude && item.longitude && 
          !isNaN(item.latitude) && !isNaN(item.longitude)
        );
        
        console.log(`📍 Загружено ${violationsWithCoords.length} нарушений с координатами`);
        console.log('Первые 3 нарушения:', violationsWithCoords.slice(0, 3));
        setViolations(violationsWithCoords);
        
        // Если включен OSM контекст, загружаем OSM данные
        if (showOSMContext) {
          await loadOSMBuildings();
        }
      }
    } catch (error) {
      console.error('Ошибка загрузки нарушений:', error);
      Alert.alert('Ошибка', 'Не удалось загрузить данные о нарушениях');
    } finally {
      setLoading(false);
    }
  };

  const loadOSMBuildings = async () => {
    try {
      setLoadingOSM(true);
      console.log('🏢 Загружаем OSM здания...');
      
      // Получаем OSM здания в текущей области карты
      const bbox = `${mapRegion.longitude - mapRegion.longitudeDelta},${mapRegion.latitude - mapRegion.latitudeDelta},${mapRegion.longitude + mapRegion.longitudeDelta},${mapRegion.latitude + mapRegion.latitudeDelta}`;
      
      const response = await ApiService.getOSMBuildings(bbox, 50);
      
      if (response.success && response.data) {
        const buildings = response.data.map(building => ({
          id: building.osm_id || building.id,
          name: building.name || building.tags?.name || 'Здание',
          latitude: parseFloat(building.lat || building.latitude),
          longitude: parseFloat(building.lon || building.longitude),
          levels: building.levels || building.tags?.['building:levels'],
          height: building.height || building.tags?.height,
          amenity: building.amenity || building.tags?.amenity,
          building_type: building.building_type || building.tags?.building
        })).filter(building => 
          building.latitude && building.longitude && 
          !isNaN(building.latitude) && !isNaN(building.longitude)
        );
        
        console.log(`✅ Загружено ${buildings.length} OSM зданий`);
        setOsmBuildings(buildings);
      }
    } catch (error) {
      console.error('❌ Ошибка загрузки OSM зданий:', error);
      // Мок-данные для демо
      const mockBuildings = [
        { id: 1, name: 'Красная площадь', latitude: 55.7558, longitude: 37.6176, levels: 1, amenity: 'historic' },
        { id: 2, name: 'ГУМ', latitude: 55.7520, longitude: 37.6156, levels: 3, amenity: 'shop' },
        { id: 3, name: 'Большой театр', latitude: 55.7539, longitude: 37.6208, levels: 4, amenity: 'theatre' }
      ];
      setOsmBuildings(mockBuildings);
    } finally {
      setLoadingOSM(false);
    }
  };

  const toggleOSMContext = async () => {
    const newShowOSM = !showOSMContext;
    setShowOSMContext(newShowOSM);
    
    if (newShowOSM && osmBuildings.length === 0) {
      await loadOSMBuildings();
    }
  };

  const handleViolationPress = async (violation) => {
    console.log('📍 Клик по нарушению:', violation.id);
    
    // Если включен OSM контекст, получаем дополнительную информацию
    if (showOSMContext) {
      try {
        const osmContext = await ApiService.getOSMUrbanContext(
          violation.latitude, 
          violation.longitude
        );
        
        if (osmContext.success) {
          violation.osmContext = osmContext.data;
          console.log('✅ OSM контекст получен для нарушения');
        }
      } catch (error) {
        console.warn('⚠️ Не удалось получить OSM контекст:', error.message);
      }
    }
    
    setSelectedViolation(violation);
    setModalVisible(true);
  };


  const getMarkerColor = (category) => {
    const colorMap = {
      'illegal_parking': '#f44336', // Красный
      'garbage': '#ff9800', // Оранжевый
      'road_damage': '#9c27b0', // Фиолетовый
      'illegal_construction': '#e91e63', // Розовый
      'broken_lighting': '#3f51b5', // Синий
      'damaged_playground': '#009688', // Бирюзовый
      'illegal_advertising': '#795548', // Коричневый
      'broken_pavement': '#607d8b', // Серый
    };
    return colorMap[category] || '#2196F3'; // Синий по умолчанию
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Дата неизвестна';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('ru-RU', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return 'Дата неизвестна';
    }
  };

  const getCategoryName = (category) => {
    const categoryMap = {
      'illegal_parking': 'Неправильная парковка',
      'garbage': 'Мусор',
      'road_damage': 'Повреждение дороги',
      'illegal_construction': 'Незаконная стройка',
      'broken_lighting': 'Сломанное освещение',
      'damaged_playground': 'Поврежденная площадка',
      'illegal_advertising': 'Незаконная реклама',
      'broken_pavement': 'Разбитый тротуар',
    };
    return categoryMap[category] || category || 'Нарушение';
  };

  const showViolationDetails = (violation) => {
    setSelectedViolation(violation);
    setModalVisible(true);
  };

  return (
    <View style={styles.container}>
      {loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#2196F3" />
          <Text style={styles.loadingText}>Загрузка карты...</Text>
        </View>
      ) : (
        <>
          {/* Панель управления */}
          <View style={styles.controlPanel}>
            {/* Переключатель OSM контекста */}
            <TouchableOpacity
              style={[styles.controlButton, showOSMContext && styles.controlButtonActive]}
              onPress={toggleOSMContext}
            >
              <Ionicons 
                name="map" 
                size={20} 
                color={showOSMContext ? "#4CAF50" : "#666"} 
              />
              <Text style={[styles.controlButtonText, showOSMContext && styles.controlButtonTextActive]}>
                OSM
              </Text>
              {loadingOSM && (
                <ActivityIndicator size="small" color="#4CAF50" style={{ marginLeft: 5 }} />
              )}
            </TouchableOpacity>
            
            {/* Переключатель типов карт */}
            <TouchableOpacity
              style={styles.controlButton}
              onPress={() => setShowMapTypeSelector(!showMapTypeSelector)}
            >
              <Ionicons name="layers" size={20} color="#666" />
              <Text style={styles.controlButtonText}>Карта</Text>
            </TouchableOpacity>
            
            {/* Счетчик нарушений */}
            <View style={styles.violationCounter}>
              <Ionicons name="warning" size={16} color="#f44336" />
              <Text style={styles.violationCounterText}>{violations.length}</Text>
            </View>
          </View>
          
          {/* Переключатель источников карт */}
          {showMapTypeSelector && (
            <View style={styles.mapTypeSelector}>
              <TouchableOpacity
                style={[
                  styles.mapTypeButton,
                  mapType === 'standard' && styles.mapTypeButtonActive
                ]}
                onPress={() => setMapType('standard')}
              >
                <Text style={styles.mapTypeButtonText}>OpenStreetMap</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[
                  styles.mapTypeButton,
                  mapType === 'yandex' && styles.mapTypeButtonActive
                ]}
                onPress={() => setMapType('yandex')}
              >
                <Text style={styles.mapTypeButtonText}>Яндекс Карты</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[
                  styles.mapTypeButton,
                  mapType === '2gis' && styles.mapTypeButtonActive
                ]}
                onPress={() => setMapType('2gis')}
              >
                <Text style={styles.mapTypeButtonText}>2ГИС</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[
                  styles.mapTypeButton,
                  mapType === 'satellite' && styles.mapTypeButtonActive
                ]}
                onPress={() => setMapType('satellite')}
              >
                <Text style={styles.mapTypeButtonText}>Спутник</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[
                  styles.mapTypeButton,
                  mapType === 'hybrid' && styles.mapTypeButtonActive
                ]}
                onPress={() => setMapType('hybrid')}
              >
                <Text style={styles.mapTypeButtonText}>Гибрид</Text>
              </TouchableOpacity>
            </View>
          )}
          
          <YandexMapView
            region={mapRegion}
            violations={violations}
            osmBuildings={showOSMContext ? osmBuildings : []}
            userLocation={location}
            mapType={mapType}
            onViolationPress={handleViolationPress}
            onRegionChange={setMapRegion}
          />
          
          {/* Кнопка поиска */}
          <TouchableOpacity
            style={styles.searchButton}
            onPress={searchLocation}
          >
            <Ionicons name="search" size={24} color="white" />
          </TouchableOpacity>

          {/* Кнопка центрирования на пользователе */}
          <TouchableOpacity
            style={styles.centerButton}
            onPress={centerOnUserLocation}
          >
            <Ionicons name="locate" size={24} color="white" />
          </TouchableOpacity>

          {/* Кнопка обновления */}
          <TouchableOpacity
            style={styles.refreshButton}
            onPress={loadViolations}
          >
            <Ionicons name="refresh" size={24} color="white" />
          </TouchableOpacity>

          {/* Кнопка полноэкранного режима */}
          <TouchableOpacity
            style={styles.fullscreenButton}
            onPress={() => Alert.alert('Полноэкранный режим', 'Функция будет добавлена в следующей версии')}
          >
            <Ionicons name="expand" size={24} color="white" />
          </TouchableOpacity>
        </>
      )}

      {/* Статистика */}
      <View style={styles.statsContainer}>
        <Text style={styles.statsText}>
          📍 Нарушений на карте: {violations.length}
        </Text>
        {showOSMContext && (
          <Text style={styles.statsText}>
            🏢 OSM зданий: {osmBuildings.length}
          </Text>
        )}
      </View>

      {/* Модальное окно с деталями нарушения */}
      <Modal
        animationType="slide"
        transparent={true}
        visible={modalVisible}
        onRequestClose={() => setModalVisible(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <ScrollView>
              {selectedViolation && (
                <>
                  <View style={styles.modalHeader}>
                    <Text style={styles.modalTitle}>
                      {getCategoryName(selectedViolation.category)}
                    </Text>
                    <TouchableOpacity
                      style={styles.closeButton}
                      onPress={() => setModalVisible(false)}
                    >
                      <Ionicons name="close" size={24} color="#666" />
                    </TouchableOpacity>
                  </View>

                  <View style={styles.detailItem}>
                    <Text style={styles.detailLabel}>📅 Дата обнаружения:</Text>
                    <Text style={styles.detailValue}>
                      {formatDate(selectedViolation.created_at)}
                    </Text>
                  </View>

                  <View style={styles.detailItem}>
                    <Text style={styles.detailLabel}>📍 Координаты:</Text>
                    <Text style={styles.detailValue}>
                      {parseFloat(selectedViolation.latitude).toFixed(6)}, {parseFloat(selectedViolation.longitude).toFixed(6)}
                    </Text>
                  </View>

                  {selectedViolation.confidence && (
                    <View style={styles.detailItem}>
                      <Text style={styles.detailLabel}>🎯 Уверенность:</Text>
                      <Text style={styles.detailValue}>
                        {Math.round(selectedViolation.confidence * 100)}%
                      </Text>
                    </View>
                  )}

                  {selectedViolation.source && (
                    <View style={styles.detailItem}>
                      <Text style={styles.detailLabel}>🤖 Источник:</Text>
                      <Text style={styles.detailValue}>
                        {selectedViolation.source}
                      </Text>
                    </View>
                  )}

                  {selectedViolation.address && (
                    <View style={styles.detailItem}>
                      <Text style={styles.detailLabel}>🏠 Адрес:</Text>
                      <Text style={styles.detailValue}>
                        {selectedViolation.address}
                      </Text>
                    </View>
                  )}

                  <TouchableOpacity
                    style={styles.actionButton}
                    onPress={() => {
                      // Здесь можно добавить функционал для создания отчета
                      Alert.alert('Функция', 'Создание отчета будет добавлено');
                    }}
                  >
                    <Ionicons name="document-text" size={20} color="white" />
                    <Text style={styles.actionButtonText}>Создать отчет</Text>
                  </TouchableOpacity>
                </>
              )}
            </ScrollView>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
  },
  loadingText: {
    marginTop: 10,
    fontSize: 16,
    color: '#666',
  },
  controlPanel: {
    position: 'absolute',
    top: 50,
    left: 20,
    right: 20,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    zIndex: 1000,
  },
  controlButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.22,
    shadowRadius: 2.22,
  },
  controlButtonActive: {
    backgroundColor: '#e8f5e8',
    borderColor: '#4CAF50',
    borderWidth: 1,
  },
  controlButtonText: {
    fontSize: 12,
    color: '#666',
    marginLeft: 5,
    fontWeight: '500',
  },
  controlButtonTextActive: {
    color: '#4CAF50',
  },
  violationCounter: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(244, 67, 54, 0.1)',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 15,
    borderColor: '#f44336',
    borderWidth: 1,
  },
  violationCounterText: {
    fontSize: 12,
    color: '#f44336',
    marginLeft: 4,
    fontWeight: 'bold',
  },
  mapTypeSelector: {
    position: 'absolute',
    top: 100,
    right: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    borderRadius: 8,
    elevation: 5,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    zIndex: 1000,
  },
  mapTypeButton: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  mapTypeButtonActive: {
    backgroundColor: '#e3f2fd',
  },
  mapTypeButtonText: {
    fontSize: 14,
    color: '#333',
    fontWeight: '500',
  },
  searchButton: {
    position: 'absolute',
    bottom: 280,
    right: 20,
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#FF9800',
    justifyContent: 'center',
    alignItems: 'center',
    elevation: 5,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
  },
  centerButton: {
    position: 'absolute',
    bottom: 220,
    right: 20,
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#2196F3',
    justifyContent: 'center',
    alignItems: 'center',
    elevation: 5,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
  },
  refreshButton: {
    position: 'absolute',
    bottom: 160,
    right: 20,
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#4CAF50',
    justifyContent: 'center',
    alignItems: 'center',
    elevation: 5,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
  },
  fullscreenButton: {
    position: 'absolute',
    bottom: 100,
    right: 20,
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#9C27B0',
    justifyContent: 'center',
    alignItems: 'center',
    elevation: 5,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
  },
  statsContainer: {
    position: 'absolute',
    bottom: 20,
    left: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    padding: 10,
    borderRadius: 8,
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.22,
    shadowRadius: 2.22,
  },
  statsText: {
    fontSize: 14,
    color: '#333',
    fontWeight: '500',
  },
  calloutContainer: {
    width: 200,
    padding: 10,
  },
  calloutTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    marginBottom: 5,
  },
  calloutDate: {
    fontSize: 12,
    color: '#666',
    marginBottom: 5,
  },
  calloutTap: {
    fontSize: 11,
    color: '#2196F3',
    fontStyle: 'italic',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: 'white',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: height * 0.7,
    padding: 20,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    flex: 1,
  },
  closeButton: {
    padding: 5,
  },
  detailItem: {
    marginBottom: 15,
  },
  detailLabel: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#666',
    marginBottom: 5,
  },
  detailValue: {
    fontSize: 14,
    color: '#333',
  },
  actionButton: {
    backgroundColor: '#2196F3',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 15,
    borderRadius: 10,
    marginTop: 20,
  },
  actionButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
    marginLeft: 10,
  },
});
