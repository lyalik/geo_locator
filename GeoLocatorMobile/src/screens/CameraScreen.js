import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  Dimensions,
  Image,
  ActivityIndicator,
  Platform,
  ScrollView,
  Animated,
  Vibration
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
  const [flashMode, setFlashMode] = useState('off');
  const [focusPoint, setFocusPoint] = useState(null);
  const [isReady, setIsReady] = useState(false);
  const cameraRef = useRef(null);
  const focusAnimation = useRef(new Animated.Value(0)).current;
  const shutterAnimation = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    requestLocationPermission();
    getCurrentLocation();
  }, []);

  const requestLocationPermission = async () => {
    const { status } = await Location.requestForegroundPermissionsAsync();
    setLocationPermission(status === 'granted');
  };

  const handleCameraReady = () => {
    setIsReady(true);
  };

  const handleFocusTap = (event) => {
    const { locationX, locationY } = event.nativeEvent;
    setFocusPoint({ x: locationX, y: locationY });
    
    // Анимация фокуса
    focusAnimation.setValue(0);
    Animated.timing(focusAnimation, {
      toValue: 1,
      duration: 300,
      useNativeDriver: true,
    }).start(() => {
      setTimeout(() => setFocusPoint(null), 1000);
    });
  };

  const toggleFlash = () => {
    setFlashMode(flashMode === 'off' ? 'on' : 'off');
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
    if (!cameraRef.current || isAnalyzing) return;

    try {
      // Анимация затвора
      Animated.sequence([
        Animated.timing(shutterAnimation, {
          toValue: 0.7,
          duration: 100,
          useNativeDriver: true,
        }),
        Animated.timing(shutterAnimation, {
          toValue: 1,
          duration: 100,
          useNativeDriver: true,
        })
      ]).start();

      // Вибрация для тактильной обратной связи
      Vibration.vibrate(50);

      const photo = await cameraRef.current.takePictureAsync({
        quality: 0.8,
        base64: true,
        skipProcessing: false,
      });
      
      setCapturedImage(photo);
      await analyzeImage(photo);
    } catch (error) {
      Alert.alert('Ошибка', 'Не удалось сделать фото');
      console.error('Ошибка камеры:', error);
    }
  };

  const analyzeImage = async (photo) => {
    if (!photo) {
      console.log('❌ Нет фото для анализа');
      return;
    }

    console.log('📸 Начинаем анализ фото:', {
      uri: photo.uri,
      hasBase64: !!photo.base64,
      width: photo.width,
      height: photo.height
    });

    setIsAnalyzing(true);
    setAnalysisResult(null);

    try {
      // Создаем FormData для отправки изображения
      const formData = new FormData();
      console.log('📦 Создаем FormData...');
      
      // Проверяем платформу для выбора способа отправки
      if (Platform.OS === 'web' && photo.base64) {
        console.log('🌐 Используем base64 для веб-версии');
        const response = await fetch(`data:image/jpeg;base64,${photo.base64}`);
        const blob = await response.blob();
        console.log('📄 Blob создан:', blob.size, 'bytes');
        formData.append('file', blob, 'violation.jpg');
      } else {
        console.log('📱 Используем URI для мобильной версии:', photo.uri);
        formData.append('file', {
          uri: photo.uri,
          type: 'image/jpeg',
          name: 'violation.jpg',
        });
      }

      // Добавляем координаты если доступны
      if (location) {
        console.log('📍 Добавляем координаты:', location.latitude, location.longitude);
        formData.append('latitude', location.latitude.toString());
        formData.append('longitude', location.longitude.toString());
      } else {
        console.log('📍 Координаты недоступны');
      }

      console.log('🚀 Отправляем запрос на анализ...');
      // Отправляем на анализ
      const result = await ApiService.detectViolation(formData);
      console.log('✅ Получен результат анализа:', result);
      setAnalysisResult(result);

      if (result.success && result.data.violations.length > 0) {
        console.log('🎯 Нарушения найдены:', result.data.violations.length);
        Alert.alert(
          'Нарушения обнаружены!', 
          `Найдено ${result.data.violations.length} нарушений`,
          [
            { text: 'OK', style: 'default' }
          ]
        );
      } else {
        console.log('✅ Нарушений не обнаружено');
        Alert.alert('Результат', 'Нарушений не обнаружено');
      }

    } catch (error) {
      console.error('❌ Ошибка анализа:', error);
      console.error('🔍 Error details:', {
        message: error.message,
        code: error.code,
        name: error.name,
        stack: error.stack
      });
      Alert.alert('Ошибка', 'Не удалось проанализировать изображение');
    } finally {
      setIsAnalyzing(false);
      console.log('🏁 Анализ завершен');
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
      <Animated.View style={[styles.cameraContainer, { opacity: shutterAnimation }]}>
        <CameraView
          style={styles.camera}
          facing={facing}
          flash={flashMode}
          ref={cameraRef}
          onCameraReady={handleCameraReady}
        >
          <TouchableOpacity
            style={styles.focusArea}
            activeOpacity={1}
            onPress={handleFocusTap}
          >
            <View style={styles.overlay}>
              <View style={styles.topControls}>
                <TouchableOpacity
                  style={styles.controlButton}
                  onPress={() => setFacing(facing === 'back' ? 'front' : 'back')}
                >
                  <Ionicons name="camera-reverse" size={24} color="white" />
                </TouchableOpacity>
                
                <TouchableOpacity
                  style={styles.controlButton}
                  onPress={toggleFlash}
                >
                  <Ionicons 
                    name={flashMode === 'on' ? 'flash' : 'flash-off'} 
                    size={24} 
                    color={flashMode === 'on' ? '#FFD700' : 'white'} 
                  />
                </TouchableOpacity>
              </View>

              {/* Индикатор фокуса */}
              {focusPoint && (
                <Animated.View
                  style={[
                    styles.focusIndicator,
                    {
                      left: focusPoint.x - 25,
                      top: focusPoint.y - 25,
                      opacity: focusAnimation,
                      transform: [{
                        scale: focusAnimation.interpolate({
                          inputRange: [0, 1],
                          outputRange: [1.5, 1],
                        })
                      }]
                    }
                  ]}
                >
                  <View style={styles.focusBox} />
                </Animated.View>
              )}

              <View style={styles.bottomControls}>
                {!isReady && (
                  <Text style={styles.instructionText}>
                    Подготовка камеры...
                  </Text>
                )}
                
                {isReady && !isAnalyzing && (
                  <Text style={styles.instructionText}>
                    Наведите камеру на объект для обнаружения нарушений
                  </Text>
                )}
                
                <TouchableOpacity
                  style={[
                    styles.captureButton,
                    isAnalyzing && styles.captureButtonDisabled
                  ]}
                  onPress={takePicture}
                  disabled={isAnalyzing || !isReady}
                >
                  {isAnalyzing ? (
                    <ActivityIndicator size="large" color="#2196F3" />
                  ) : (
                    <View style={styles.captureButtonInner} />
                  )}
                </TouchableOpacity>
                
                {location && (
                  <Text style={styles.locationText}>
                    📍 GPS: {location.latitude.toFixed(4)}, {location.longitude.toFixed(4)}
                  </Text>
                )}
              </View>
            </View>
          </TouchableOpacity>
        </CameraView>
      </Animated.View>
    </View>
  );
}

const styles = StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: 'black',
    },
    cameraContainer: {
      flex: 1,
    },
    camera: {
      flex: 1,
    },
    focusArea: {
      flex: 1,
    },
    overlay: {
      flex: 1,
      backgroundColor: 'transparent',
    },
    topControls: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      paddingTop: 50,
      paddingHorizontal: 20,
    },
    controlButton: {
      width: 50,
      height: 50,
      borderRadius: 25,
      backgroundColor: 'rgba(0,0,0,0.7)',
      justifyContent: 'center',
      alignItems: 'center',
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.3,
      shadowRadius: 4,
      elevation: 5,
    },
    focusIndicator: {
      position: 'absolute',
      width: 50,
      height: 50,
      justifyContent: 'center',
      alignItems: 'center',
    },
    focusBox: {
      width: 50,
      height: 50,
      borderWidth: 2,
      borderColor: '#FFD700',
      backgroundColor: 'transparent',
    },
    bottomControls: {
      position: 'absolute',
      bottom: 0,
      left: 0,
      right: 0,
      alignItems: 'center',
      paddingBottom: 50,
    },
    locationText: {
      color: 'white',
      fontSize: 12,
      backgroundColor: 'rgba(0,0,0,0.5)',
      paddingHorizontal: 10,
      paddingVertical: 5,
      borderRadius: 10,
      marginTop: 10,
    },
    captureButton: {
      width: 80,
      height: 80,
      borderRadius: 40,
      backgroundColor: 'white',
      justifyContent: 'center',
      alignItems: 'center',
      marginBottom: 20,
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.3,
      shadowRadius: 6,
      elevation: 8,
    },
    captureButtonDisabled: {
      backgroundColor: 'rgba(255,255,255,0.5)',
    },
    captureButtonInner: {
      width: 60,
      height: 60,
      borderRadius: 30,
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
