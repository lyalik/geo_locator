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
  const [mapRegion, setMapRegion] = useState({
    latitude: 55.7558, // Москва по умолчанию
    longitude: 37.6176,
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
    }
  };

  const loadViolations = async () => {
    try {
      setLoading(true);
      const response = await ApiService.getAllViolations();
      
      if (response.success && response.data) {
        // Извлекаем нарушения из структуры данных API
        const allViolations = [];
        
        response.data.forEach(item => {
          if (item.violations && Array.isArray(item.violations)) {
            item.violations.forEach(violation => {
              // Проверяем координаты из location или metadata
              const coords = item.location?.coordinates;
              if (coords && coords.latitude && coords.longitude) {
                allViolations.push({
                  ...violation,
                  id: `${item.violation_id}-${violation.category}`,
                  latitude: coords.latitude,
                  longitude: coords.longitude,
                  created_at: item.metadata?.timestamp,
                  address: item.location?.address?.formatted_address
                });
              }
            });
          }
        });
        
        setViolations(allViolations);
      }
    } catch (error) {
      console.error('Ошибка загрузки нарушений:', error);
      Alert.alert('Ошибка', 'Не удалось загрузить данные о нарушениях');
    } finally {
      setLoading(false);
    }
  };

  const centerOnUserLocation = () => {
    if (location) {
      setMapRegion({
        ...location,
        latitudeDelta: 0.01,
        longitudeDelta: 0.01,
      });
    }
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
      {loading && (
        <View style={styles.loadingOverlay}>
          <ActivityIndicator size="large" color="#2196F3" />
          <Text style={styles.loadingText}>Загрузка карты...</Text>
        </View>
      )}

      <YandexMapView
        style={styles.map}
        region={mapRegion}
        violations={violations}
        onMarkerPress={showViolationDetails}
      />

      {/* Кнопки управления */}
      <View style={styles.controls}>
        <TouchableOpacity 
          style={styles.controlButton} 
          onPress={centerOnUserLocation}
        >
          <Ionicons name="locate" size={24} color="white" />
        </TouchableOpacity>

        <TouchableOpacity 
          style={styles.controlButton} 
          onPress={loadViolations}
        >
          <Ionicons name="refresh" size={24} color="white" />
        </TouchableOpacity>
      </View>

      {/* Статистика */}
      <View style={styles.statsContainer}>
        <Text style={styles.statsText}>
          📍 Нарушений на карте: {violations.length}
        </Text>
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
  map: {
    flex: 1,
  },
  loadingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(255,255,255,0.8)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000,
  },
  loadingText: {
    marginTop: 10,
    fontSize: 16,
    color: '#666',
  },
  controls: {
    position: 'absolute',
    right: 20,
    top: 100,
    flexDirection: 'column',
  },
  controlButton: {
    backgroundColor: '#2196F3',
    width: 50,
    height: 50,
    borderRadius: 25,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 10,
    elevation: 5,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
  },
  statsContainer: {
    position: 'absolute',
    bottom: 20,
    left: 20,
    right: 20,
    backgroundColor: 'rgba(0,0,0,0.7)',
    padding: 10,
    borderRadius: 10,
  },
  statsText: {
    color: 'white',
    fontSize: 14,
    textAlign: 'center',
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
