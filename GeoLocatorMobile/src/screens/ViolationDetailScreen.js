import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Image,
  TouchableOpacity,
  Alert,
  TextInput,
  ActivityIndicator,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import ApiService from '../services/ApiService';

const ViolationDetailScreen = ({ route, navigation }) => {
  const { violationId } = route.params;
  const [violation, setViolation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [notes, setNotes] = useState('');
  const [status, setStatus] = useState('');
  const [user, setUser] = useState(null);

  useEffect(() => {
    loadUserData();
    loadViolationDetails();
  }, []);

  const loadUserData = async () => {
    try {
      const userData = await AsyncStorage.getItem('user');
      if (userData) {
        setUser(JSON.parse(userData));
      }
    } catch (error) {
      console.error('Ошибка загрузки данных пользователя:', error);
    }
  };

  const loadViolationDetails = async () => {
    try {
      setLoading(true);
      const response = await ApiService.getViolationDetails(violationId);
      
      if (response.success && response.data) {
        setViolation(response.data);
        setNotes(response.data.notes || '');
        setStatus(response.data.status || 'active');
      } else {
        Alert.alert('Ошибка', 'Не удалось загрузить детали нарушения');
      }
    } catch (error) {
      console.error('Ошибка загрузки деталей нарушения:', error);
      Alert.alert('Ошибка', 'Не удалось загрузить детали нарушения');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!user) {
      Alert.alert('Ошибка', 'Необходимо войти в систему');
      return;
    }

    try {
      const updateData = {
        notes: notes,
        status: status,
        user_id: user.id
      };

      const response = await ApiService.updateViolation(violationId, updateData);
      
      if (response.success) {
        setViolation({ ...violation, notes, status });
        setEditing(false);
        Alert.alert('Успех', 'Нарушение обновлено');
      } else {
        Alert.alert('Ошибка', response.message || 'Не удалось обновить нарушение');
      }
    } catch (error) {
      console.error('Ошибка обновления нарушения:', error);
      Alert.alert('Ошибка', 'Не удалось обновить нарушение');
    }
  };

  const handleDelete = () => {
    Alert.alert(
      'Подтверждение',
      'Вы уверены, что хотите удалить это нарушение?',
      [
        { text: 'Отмена', style: 'cancel' },
        { text: 'Удалить', style: 'destructive', onPress: confirmDelete },
      ]
    );
  };

  const confirmDelete = async () => {
    if (!user) {
      Alert.alert('Ошибка', 'Необходимо войти в систему');
      return;
    }

    try {
      const response = await ApiService.deleteViolation(violationId, user.id);
      
      if (response.success) {
        Alert.alert('Успех', 'Нарушение удалено', [
          { text: 'OK', onPress: () => navigation.goBack() }
        ]);
      } else {
        Alert.alert('Ошибка', response.message || 'Не удалось удалить нарушение');
      }
    } catch (error) {
      console.error('Ошибка удаления нарушения:', error);
      Alert.alert('Ошибка', 'Не удалось удалить нарушение');
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Неизвестно';
    const date = new Date(dateString);
    return date.toLocaleString('ru-RU');
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return '#ff6b6b';
      case 'resolved': return '#51cf66';
      case 'pending': return '#ffd43b';
      case 'deleted': return '#868e96';
      default: return '#495057';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'active': return 'Активное';
      case 'resolved': return 'Решено';
      case 'pending': return 'В ожидании';
      case 'deleted': return 'Удалено';
      default: return 'Неизвестно';
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Загрузка деталей нарушения...</Text>
      </View>
    );
  }

  if (!violation) {
    return (
      <View style={styles.errorContainer}>
        <Ionicons name="alert-circle" size={64} color="#ff6b6b" />
        <Text style={styles.errorText}>Нарушение не найдено</Text>
        <TouchableOpacity style={styles.backButton} onPress={() => navigation.goBack()}>
          <Text style={styles.backButtonText}>Назад</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>

      {/* Violation Image */}
      {violation.image_path && (
        <View style={styles.imageContainer}>
          <Image
            source={{ uri: violation.image_path }}
            style={styles.violationImage}
            resizeMode="cover"
          />
        </View>
      )}

      {/* Basic Info */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Основная информация</Text>
        
        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>ID:</Text>
          <Text style={styles.infoValue}>{violation.id}</Text>
        </View>

        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>Категория:</Text>
          <Text style={styles.infoValue}>{violation.category || 'Не указана'}</Text>
        </View>

        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>Статус:</Text>
          <View style={styles.statusContainer}>
            {editing ? (
              <View style={styles.statusPicker}>
                {['active', 'resolved', 'pending'].map((statusOption) => (
                  <TouchableOpacity
                    key={statusOption}
                    style={[
                      styles.statusOption,
                      status === statusOption && styles.statusOptionSelected
                    ]}
                    onPress={() => setStatus(statusOption)}
                  >
                    <Text style={[
                      styles.statusOptionText,
                      status === statusOption && styles.statusOptionTextSelected
                    ]}>
                      {getStatusText(statusOption)}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            ) : (
              <View style={[styles.statusBadge, { backgroundColor: getStatusColor(violation.status) }]}>
                <Text style={styles.statusText}>{getStatusText(violation.status)}</Text>
              </View>
            )}
          </View>
        </View>

        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>Уверенность:</Text>
          <Text style={styles.infoValue}>
            {violation.confidence ? `${Math.round(violation.confidence * 100)}%` : 'Не указана'}
          </Text>
        </View>

        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>Дата создания:</Text>
          <Text style={styles.infoValue}>{formatDate(violation.created_at)}</Text>
        </View>
      </View>

      {/* Location Info */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>📍 Местоположение</Text>
        
        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>Координаты:</Text>
          <Text style={styles.infoValue}>
            {violation.location?.latitude && violation.location?.longitude 
              ? `${violation.location.latitude.toFixed(6)}, ${violation.location.longitude.toFixed(6)}`
              : violation.latitude && violation.longitude
              ? `${violation.latitude.toFixed(6)}, ${violation.longitude.toFixed(6)}`
              : 'Не определены'
            }
          </Text>
        </View>

        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>Адрес:</Text>
          <Text style={styles.infoValue}>
            {violation.location?.address || violation.address || 'Не определен'}
          </Text>
        </View>

        {violation.source && (
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Источник:</Text>
            <Text style={styles.infoValue}>
              {violation.source === 'yolo' ? '🎯 YOLO' : 
               violation.source === 'mistral' ? '🤖 Mistral AI' : 
               violation.source}
            </Text>
          </View>
        )}
      </View>

      {/* Notes Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Заметки</Text>
        {editing ? (
          <TextInput
            style={styles.notesInput}
            value={notes}
            onChangeText={setNotes}
            placeholder="Добавьте заметки о нарушении..."
            multiline
            numberOfLines={4}
            textAlignVertical="top"
          />
        ) : (
          <Text style={styles.notesText}>
            {violation.notes || 'Заметки отсутствуют'}
          </Text>
        )}
      </View>

      {/* Description */}
      {violation.description && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Описание</Text>
          <Text style={styles.descriptionText}>{violation.description}</Text>
        </View>
      )}

      <View style={styles.bottomPadding} />
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f8f9fa',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#495057',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f8f9fa',
    padding: 20,
  },
  errorText: {
    fontSize: 18,
    color: '#495057',
    marginTop: 16,
    marginBottom: 24,
  },
  backButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
  },
  backButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: '600',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#e9ecef',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#212529',
    flex: 1,
    textAlign: 'center',
    marginHorizontal: 16,
  },
  headerActions: {
    flexDirection: 'row',
  },
  actionButton: {
    padding: 8,
    marginLeft: 8,
  },
  imageContainer: {
    backgroundColor: 'white',
    padding: 16,
  },
  violationImage: {
    width: '100%',
    height: 250,
    borderRadius: 12,
  },
  section: {
    backgroundColor: 'white',
    margin: 16,
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#212529',
    marginBottom: 16,
  },
  infoRow: {
    flexDirection: 'row',
    marginBottom: 12,
    alignItems: 'flex-start',
  },
  infoLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: '#6c757d',
    width: 100,
    marginRight: 12,
  },
  infoValue: {
    fontSize: 14,
    color: '#212529',
    flex: 1,
  },
  statusContainer: {
    flex: 1,
  },
  statusBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    alignSelf: 'flex-start',
  },
  statusText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '600',
  },
  statusPicker: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  statusOption: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#dee2e6',
    marginRight: 8,
    marginBottom: 8,
  },
  statusOptionSelected: {
    backgroundColor: '#007AFF',
    borderColor: '#007AFF',
  },
  statusOptionText: {
    fontSize: 12,
    color: '#495057',
  },
  statusOptionTextSelected: {
    color: 'white',
  },
  notesInput: {
    borderWidth: 1,
    borderColor: '#dee2e6',
    borderRadius: 8,
    padding: 12,
    fontSize: 14,
    minHeight: 100,
    backgroundColor: '#f8f9fa',
  },
  notesText: {
    fontSize: 14,
    color: '#495057',
    lineHeight: 20,
  },
  descriptionText: {
    fontSize: 14,
    color: '#495057',
    lineHeight: 20,
  },
  bottomPadding: {
    height: 20,
  },
});

export default ViolationDetailScreen;
