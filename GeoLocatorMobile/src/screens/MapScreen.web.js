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
import { Ionicons } from '@expo/vector-icons';
import ApiService from '../services/ApiService';

const { width, height } = Dimensions.get('window');

export default function MapScreen() {
  const [violations, setViolations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedViolation, setSelectedViolation] = useState(null);
  const [modalVisible, setModalVisible] = useState(false);

  useEffect(() => {
    loadViolations();
  }, []);

  const loadViolations = async () => {
    try {
      setLoading(true);
      const response = await ApiService.getAllViolations();
      
      if (response.success && response.data) {
        const validViolations = response.data.filter(violation => 
          violation.latitude && 
          violation.longitude && 
          !isNaN(violation.latitude) && 
          !isNaN(violation.longitude)
        );
        setViolations(validViolations);
      }
    } catch (error) {
      console.error('Ошибка загрузки нарушений:', error);
      Alert.alert('Ошибка', 'Не удалось загрузить данные о нарушениях');
    } finally {
      setLoading(false);
    }
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

  const openInYandexMaps = (lat, lng) => {
    const url = `https://yandex.ru/maps/?pt=${lng},${lat}&z=16&l=map`;
    if (typeof window !== 'undefined') {
      window.open(url, '_blank');
    }
  };

  const renderViolationCard = (violation, index) => (
    <TouchableOpacity
      key={`violation-${violation.id || index}`}
      style={styles.violationCard}
      onPress={() => showViolationDetails(violation)}
    >
      <View style={styles.cardHeader}>
        <Text style={styles.categoryTitle}>
          {getCategoryName(violation.category)}
        </Text>
        <Text style={styles.dateText}>
          {formatDate(violation.created_at)}
        </Text>
      </View>
      
      <View style={styles.cardContent}>
        <Text style={styles.coordinatesText}>
          📍 {parseFloat(violation.latitude).toFixed(6)}, {parseFloat(violation.longitude).toFixed(6)}
        </Text>
        
        {violation.confidence && (
          <Text style={styles.confidenceText}>
            🎯 Уверенность: {Math.round(violation.confidence * 100)}%
          </Text>
        )}
        
        {violation.source && (
          <Text style={styles.sourceText}>
            🤖 Источник: {violation.source}
          </Text>
        )}
      </View>
      
      <TouchableOpacity
        style={styles.mapButton}
        onPress={(e) => {
          e.stopPropagation();
          openInYandexMaps(violation.latitude, violation.longitude);
        }}
      >
        <Ionicons name="map" size={16} color="#2196F3" />
        <Text style={styles.mapButtonText}>Открыть на карте</Text>
      </TouchableOpacity>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      {loading && (
        <View style={styles.loadingOverlay}>
          <ActivityIndicator size="large" color="#2196F3" />
          <Text style={styles.loadingText}>Загрузка нарушений...</Text>
        </View>
      )}

      <View style={styles.header}>
        <Text style={styles.headerTitle}>Карта нарушений</Text>
        <Text style={styles.headerSubtitle}>
          📍 Найдено нарушений: {violations.length}
        </Text>
        <Text style={styles.webNotice}>
          💻 Веб-версия: список нарушений с возможностью открытия на Яндекс.Картах
        </Text>
      </View>

      <ScrollView style={styles.violationsList}>
        {violations.map(renderViolationCard)}
      </ScrollView>

      <View style={styles.controls}>
        <TouchableOpacity 
          style={styles.controlButton} 
          onPress={loadViolations}
        >
          <Ionicons name="refresh" size={24} color="white" />
        </TouchableOpacity>
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

                  <TouchableOpacity
                    style={styles.actionButton}
                    onPress={() => {
                      openInYandexMaps(selectedViolation.latitude, selectedViolation.longitude);
                    }}
                  >
                    <Ionicons name="map" size={20} color="white" />
                    <Text style={styles.actionButtonText}>Открыть на Яндекс.Картах</Text>
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
    backgroundColor: '#f5f5f5',
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
  header: {
    backgroundColor: 'white',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  webNotice: {
    fontSize: 12,
    color: '#2196F3',
    marginTop: 8,
    fontStyle: 'italic',
  },
  violationsList: {
    flex: 1,
    padding: 15,
  },
  violationCard: {
    backgroundColor: 'white',
    borderRadius: 10,
    padding: 15,
    marginBottom: 10,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  categoryTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    flex: 1,
  },
  dateText: {
    fontSize: 12,
    color: '#666',
  },
  cardContent: {
    marginBottom: 10,
  },
  coordinatesText: {
    fontSize: 12,
    color: '#2196F3',
    marginBottom: 4,
  },
  confidenceText: {
    fontSize: 12,
    color: '#4caf50',
    marginBottom: 4,
  },
  sourceText: {
    fontSize: 12,
    color: '#666',
    fontStyle: 'italic',
  },
  mapButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#e3f2fd',
    padding: 8,
    borderRadius: 6,
  },
  mapButtonText: {
    fontSize: 12,
    color: '#2196F3',
    marginLeft: 4,
    fontWeight: 'bold',
  },
  controls: {
    position: 'absolute',
    right: 20,
    bottom: 20,
  },
  controlButton: {
    backgroundColor: '#2196F3',
    width: 50,
    height: 50,
    borderRadius: 25,
    justifyContent: 'center',
    alignItems: 'center',
    elevation: 5,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
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
