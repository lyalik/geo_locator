import React, { useState, useRef, useEffect } from 'react';
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
import { CameraView, useCameraPermissions } from 'expo-camera';
import * as Location from 'expo-location';
import { Ionicons } from '@expo/vector-icons';
import ApiService from '../services/ApiService';

const { width, height } = Dimensions.get('window');

export default function CameraScreen() {
  const [permission, requestPermission] = useCameraPermissions();
  const [locationPermission, setLocationPermission] = useState(null);
  const [facing, setFacing] = useState('back');
  const [capturedImage, setCapturedImage] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [location, setLocation] = useState(null);
  const cameraRef = useRef(null);

  useEffect(() => {
    requestLocationPermission();
    getCurrentLocation();
  }, []);

  const requestLocationPermission = async () => {
    const { status } = await Location.requestForegroundPermissionsAsync();
    setLocationPermission(status === 'granted');
  };

  const getCurrentLocation = async () => {
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Ошибка', 'Необходимо разрешение на доступ к геолокации');
        return;
      }

      const currentLocation = await Location.getCurrentPositionAsync({});
      setLocation({
        latitude: currentLocation.coords.latitude,
        longitude: currentLocation.coords.longitude,
      });
    } catch (error) {
      console.error('Ошибка получения геолокации:', error);
    }
  };

  const takePicture = async () => {
    if (!cameraRef.current) return;

    try {
      const photo = await cameraRef.current.takePictureAsync({
        quality: 0.8,
        base64: true,
      });
      
      setCapturedImage(photo);
      await analyzeImage(photo);
    } catch (error) {
      Alert.alert('Ошибка', 'Не удалось сделать фото');
      console.error('Ошибка камеры:', error);
    }
  };

  const analyzeImage = async (photo) => {
    if (!photo) return;

    setIsAnalyzing(true);
    setAnalysisResult(null);

    try {
      // Создаем FormData для отправки изображения
      const formData = new FormData();
      
      // Для React Native Web нужно создать blob из base64
      if (photo.base64) {
        const response = await fetch(`data:image/jpeg;base64,${photo.base64}`);
        const blob = await response.blob();
        formData.append('file', blob, 'violation.jpg');
      } else {
        formData.append('file', {
          uri: photo.uri,
          type: 'image/jpeg',
          name: 'violation.jpg',
        });
      }

      // Добавляем координаты если доступны
      if (location) {
        formData.append('latitude', location.latitude.toString());
        formData.append('longitude', location.longitude.toString());
      }

      // Отправляем на анализ
      const result = await ApiService.detectViolation(formData);
      setAnalysisResult(result);

      if (result.success && result.data.violations.length > 0) {
        Alert.alert(
          'Нарушения обнаружены!', 
          `Найдено ${result.data.violations.length} нарушений`,
          [
            { text: 'OK', style: 'default' }
          ]
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

  const retakePhoto = () => {
    setCapturedImage(null);
    setAnalysisResult(null);
  };

  const toggleCameraFacing = () => {
    setFacing(current => (current === 'back' ? 'front' : 'back'));
  };

  if (!permission) {
    return <View style={styles.container}><Text>Запрос разрешений...</Text></View>;
  }

  if (!permission.granted) {
    return (
      <View style={styles.permissionContainer}>
        <Text style={styles.permissionText}>
          Необходимо разрешение на использование камеры
        </Text>
        <TouchableOpacity style={styles.permissionButton} onPress={requestPermission}>
          <Text style={styles.permissionButtonText}>Предоставить доступ</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (capturedImage) {
    return (
      <View style={styles.container}>
        <ScrollView contentContainerStyle={styles.resultContainer}>
          <Image source={{ uri: capturedImage.uri }} style={styles.capturedImage} />
          
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
                  
                  {location && (
                    <View style={styles.locationInfo}>
                      <Text style={styles.locationText}>
                        📍 Координаты: {location.latitude.toFixed(6)}, {location.longitude.toFixed(6)}
                      </Text>
                    </View>
                  )}
                </View>
              ) : (
                <Text style={styles.noViolations}>
                  ✅ Нарушений не обнаружено
                </Text>
              )}
            </View>
          )}

          <View style={styles.buttonContainer}>
            <TouchableOpacity style={styles.retakeButton} onPress={retakePhoto}>
              <Ionicons name="camera" size={24} color="white" />
              <Text style={styles.buttonText}>Снова</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <CameraView 
        style={styles.camera} 
        facing={facing}
        ref={cameraRef}
      />
      <View style={styles.cameraOverlay}>
          <View style={styles.topControls}>
            <TouchableOpacity style={styles.flipButton} onPress={toggleCameraFacing}>
              <Ionicons name="camera-reverse" size={28} color="white" />
            </TouchableOpacity>
          </View>

          <View style={styles.bottomControls}>
            <View style={styles.locationIndicator}>
              {location ? (
                <Text style={styles.locationText}>
                  📍 GPS: {location.latitude.toFixed(4)}, {location.longitude.toFixed(4)}
                </Text>
              ) : (
                <Text style={styles.locationText}>📍 Определение местоположения...</Text>
              )}
            </View>

            <TouchableOpacity style={styles.captureButton} onPress={takePicture}>
              <View style={styles.captureButtonInner} />
            </TouchableOpacity>

            <Text style={styles.instructionText}>
              Наведите камеру на нарушение и нажмите кнопку
            </Text>
          </View>
        </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  permissionContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#f5f5f5',
  },
  permissionText: {
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 20,
    color: '#333',
  },
  permissionButton: {
    backgroundColor: '#2196F3',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 8,
  },
  permissionButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  camera: {
    flex: 1,
  },
  cameraOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    flex: 1,
    justifyContent: 'space-between',
  },
  topControls: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    padding: 20,
    paddingTop: 50,
  },
  flipButton: {
    backgroundColor: 'rgba(0,0,0,0.5)',
    padding: 12,
    borderRadius: 25,
  },
  bottomControls: {
    alignItems: 'center',
    paddingBottom: 50,
  },
  locationIndicator: {
    backgroundColor: 'rgba(0,0,0,0.7)',
    paddingHorizontal: 15,
    paddingVertical: 8,
    borderRadius: 20,
    marginBottom: 20,
  },
  locationText: {
    color: 'white',
    fontSize: 12,
  },
  captureButton: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: 'white',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 20,
  },
  captureButtonInner: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#2196F3',
  },
  instructionText: {
    color: 'white',
    fontSize: 14,
    textAlign: 'center',
    backgroundColor: 'rgba(0,0,0,0.5)',
    paddingHorizontal: 15,
    paddingVertical: 8,
    borderRadius: 15,
  },
  resultContainer: {
    padding: 20,
  },
  capturedImage: {
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
