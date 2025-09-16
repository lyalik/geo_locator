import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  Image,
  ScrollView,
  ActivityIndicator,
  Dimensions
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import ApiService from '../services/ApiService';

const { width, height } = Dimensions.get('window');

export default function CameraScreen() {
  const [selectedImage, setSelectedImage] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file && file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const imageData = {
          uri: e.target.result,
          name: file.name,
          type: file.type,
          file: file
        };
        setSelectedImage(imageData);
        analyzeImage(imageData);
      };
      reader.readAsDataURL(file);
    } else {
      Alert.alert('Ошибка', 'Пожалуйста, выберите изображение');
    }
  };

  const analyzeImage = async (imageData) => {
    if (!imageData) return;

    setIsAnalyzing(true);
    setAnalysisResult(null);

    try {
      // Создаем FormData для отправки изображения
      const formData = new FormData();
      formData.append('file', imageData.file);

      // Добавляем тестовые координаты для веб-версии
      formData.append('latitude', '55.7558'); // Москва
      formData.append('longitude', '37.6176');

      // Отправляем на анализ
      const result = await ApiService.detectViolation(formData);
      setAnalysisResult(result);

      if (result.success && result.data.violations.length > 0) {
        Alert.alert(
          'Нарушения обнаружены!', 
          `Найдено ${result.data.violations.length} нарушений`,
          [{ text: 'OK', style: 'default' }]
        );
      } else {
        Alert.alert('Результат', 'Нарушений не обнаружено');
      }

    } catch (error) {
      console.error('Ошибка анализа:', error);
      Alert.alert('Ошибка', 'Не удалось проанализировать изображение');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const resetSelection = () => {
    setSelectedImage(null);
    setAnalysisResult(null);
  };

  if (selectedImage) {
    return (
      <View style={styles.container}>
        <ScrollView contentContainerStyle={styles.resultContainer}>
          <Image source={{ uri: selectedImage.uri }} style={styles.selectedImage} />
          
          {isAnalyzing && (
            <View style={styles.analyzingContainer}>
              <ActivityIndicator size="large" color="#2196F3" />
              <Text style={styles.analyzingText}>Анализ изображения...</Text>
            </View>
          )}

          {analysisResult && (
            <View style={styles.resultCard}>
              <Text style={styles.resultTitle}>Результат анализа</Text>
              
              {analysisResult.success && analysisResult.data.violations.length > 0 ? (
                <View>
                  <Text style={styles.violationsFound}>
                    Найдено нарушений: {analysisResult.data.violations.length}
                  </Text>
                  
                  {analysisResult.data.violations.map((violation, index) => (
                    <View key={index} style={styles.violationItem}>
                      <Text style={styles.violationType}>
                        📍 {violation.category || 'Нарушение'}
                      </Text>
                      <Text style={styles.violationConfidence}>
                        Уверенность: {Math.round((violation.confidence || 0) * 100)}%
                      </Text>
                      {violation.source && (
                        <Text style={styles.violationSource}>
                          Источник: {violation.source}
                        </Text>
                      )}
                    </View>
                  ))}
                  
                  <View style={styles.locationInfo}>
                    <Text style={styles.locationText}>
                      📍 Координаты: 55.7558, 37.6176 (тестовые для веб-версии)
                    </Text>
                  </View>
                </View>
              ) : (
                <Text style={styles.noViolations}>
                  ✅ Нарушений не обнаружено
                </Text>
              )}
            </View>
          )}

          <View style={styles.buttonContainer}>
            <TouchableOpacity style={styles.retakeButton} onPress={resetSelection}>
              <Ionicons name="camera" size={24} color="white" />
              <Text style={styles.buttonText}>Выбрать другое фото</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.webCameraContainer}>
        <View style={styles.uploadArea}>
          <Ionicons name="cloud-upload" size={80} color="#ccc" />
          <Text style={styles.uploadTitle}>Загрузка изображения</Text>
          <Text style={styles.uploadSubtitle}>
            💻 Веб-версия: выберите фото нарушения с устройства
          </Text>
          
          <input
            type="file"
            accept="image/*"
            onChange={handleFileSelect}
            style={styles.hiddenInput}
            id="image-upload"
          />
          
          <TouchableOpacity 
            style={styles.uploadButton}
            onPress={() => document.getElementById('image-upload').click()}
          >
            <Ionicons name="image" size={24} color="white" />
            <Text style={styles.uploadButtonText}>Выбрать фото</Text>
          </TouchableOpacity>
          
          <View style={styles.infoContainer}>
            <Text style={styles.infoTitle}>ℹ️ Как это работает:</Text>
            <Text style={styles.infoText}>
              1. Выберите фото нарушения с вашего устройства
            </Text>
            <Text style={styles.infoText}>
              2. Изображение будет отправлено на ИИ-анализ
            </Text>
            <Text style={styles.infoText}>
              3. Система определит тип и серьезность нарушения
            </Text>
            <Text style={styles.infoText}>
              4. Результат будет сохранен в базе данных
            </Text>
          </View>
          
          <View style={styles.supportedFormats}>
            <Text style={styles.formatsTitle}>Поддерживаемые форматы:</Text>
            <Text style={styles.formatsText}>JPG, PNG, GIF, WebP</Text>
          </View>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  webCameraContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  uploadArea: {
    backgroundColor: 'white',
    borderRadius: 20,
    padding: 40,
    alignItems: 'center',
    maxWidth: 400,
    width: '100%',
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  uploadTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 20,
    marginBottom: 10,
  },
  uploadSubtitle: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    marginBottom: 30,
  },
  hiddenInput: {
    display: 'none',
  },
  uploadButton: {
    backgroundColor: '#2196F3',
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 30,
    paddingVertical: 15,
    borderRadius: 25,
    marginBottom: 30,
  },
  uploadButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
    marginLeft: 10,
  },
  infoContainer: {
    backgroundColor: '#f8f9fa',
    borderRadius: 10,
    padding: 20,
    marginBottom: 20,
    width: '100%',
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 10,
  },
  infoText: {
    fontSize: 14,
    color: '#666',
    marginBottom: 5,
  },
  supportedFormats: {
    alignItems: 'center',
  },
  formatsTitle: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#999',
    marginBottom: 5,
  },
  formatsText: {
    fontSize: 12,
    color: '#ccc',
  },
  resultContainer: {
    padding: 20,
  },
  selectedImage: {
    width: width - 40,
    height: (width - 40) * 0.75,
    borderRadius: 10,
    marginBottom: 20,
  },
  analyzingContainer: {
    alignItems: 'center',
    padding: 20,
  },
  analyzingText: {
    marginTop: 10,
    fontSize: 16,
    color: '#666',
  },
  resultCard: {
    backgroundColor: 'white',
    padding: 20,
    borderRadius: 10,
    marginBottom: 20,
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  resultTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 15,
    color: '#333',
  },
  violationsFound: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#f44336',
    marginBottom: 10,
  },
  noViolations: {
    fontSize: 16,
    color: '#4caf50',
    textAlign: 'center',
  },
  violationItem: {
    backgroundColor: '#f5f5f5',
    padding: 12,
    borderRadius: 8,
    marginBottom: 8,
  },
  violationType: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333',
  },
  violationConfidence: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  violationSource: {
    fontSize: 12,
    color: '#2196F3',
    marginTop: 2,
  },
  locationInfo: {
    backgroundColor: '#e3f2fd',
    padding: 10,
    borderRadius: 8,
    marginTop: 10,
  },
  locationText: {
    fontSize: 12,
    color: '#2196F3',
  },
  buttonContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
  },
  retakeButton: {
    backgroundColor: '#2196F3',
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 25,
  },
  buttonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
    marginLeft: 8,
  },
});
