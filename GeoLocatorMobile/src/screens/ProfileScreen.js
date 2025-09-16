import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  ScrollView,
  ActivityIndicator,
  Switch
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import ApiService from '../services/ApiService';

export default function ProfileScreen({ user, onLogout }) {
  const [analytics, setAnalytics] = useState(null);
  const [userStats, setUserStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [serverStatus, setServerStatus] = useState(null);
  const [notifications, setNotifications] = useState(true);
  const [autoLocation, setAutoLocation] = useState(true);

  useEffect(() => {
    loadProfileData();
    checkServerStatus();
  }, []);

  const loadProfileData = async () => {
    try {
      setLoading(true);
      
      // Загружаем общую аналитику системы
      const analyticsResponse = await ApiService.getAnalytics();
      if (analyticsResponse.success && analyticsResponse.data) {
        setAnalytics(analyticsResponse.data);
      }
      
      // Загружаем персональную статистику пользователя
      if (user && user.id) {
        try {
          const userStatsResponse = await ApiService.getUserStats(user.id);
          if (userStatsResponse.success && userStatsResponse.data) {
            setUserStats(userStatsResponse.data);
          }
        } catch (statsError) {
          console.error('Ошибка загрузки статистики пользователя:', statsError);
        }
      }
    } catch (error) {
      console.error('Ошибка загрузки данных профиля:', error);
    } finally {
      setLoading(false);
    }
  };

  const checkServerStatus = async () => {
    try {
      const status = await ApiService.checkServerStatus();
      setServerStatus(status);
    } catch (error) {
      console.error('Ошибка проверки статуса сервера:', error);
      setServerStatus({
        online: false,
        message: 'Не удалось проверить статус сервера'
      });
    }
  };

  const handleRefresh = async () => {
    await loadProfileData();
    await checkServerStatus();
  };

  const showAbout = () => {
    Alert.alert(
      'О приложении',
      'GeoLocator Mobile v1.0.0\n\n' +
      'Мобильное приложение для детекции нарушений городской среды с использованием ИИ.\n\n' +
      'Технологии:\n' +
      '• YOLOv8 для детекции объектов\n' +
      '• Mistral AI для анализа\n' +
      '• Яндекс Карты и 2GIS\n' +
      '• React Native + Expo\n\n' +
      'Разработано для хакатона 2025',
      [{ text: 'OK', style: 'default' }]
    );
  };

  const showHelp = () => {
    Alert.alert(
      'Справка',
      'Как пользоваться приложением:\n\n' +
      '📷 Камера - Сделайте фото нарушения для автоматического анализа\n\n' +
      '🗺️ Карта - Просматривайте все обнаруженные нарушения на интерактивной карте\n\n' +
      '📋 История - Смотрите свои предыдущие отчеты и экспортируйте данные\n\n' +
      '👤 Профиль - Настройки приложения и статистика\n\n' +
      'Для работы требуется подключение к интернету и разрешения на камеру и геолокацию.',
      [{ text: 'Понятно', style: 'default' }]
    );
  };

  const renderStatCard = (title, value, icon, color = '#2196F3') => (
    <View style={[styles.statCard, { borderLeftColor: color }]}>
      <View style={styles.statIcon}>
        <Ionicons name={icon} size={24} color={color} />
      </View>
      <View style={styles.statInfo}>
        <Text style={styles.statValue}>{value}</Text>
        <Text style={styles.statTitle}>{title}</Text>
      </View>
    </View>
  );

  const renderServiceStatus = (name, status, icon) => (
    <View style={styles.serviceItem}>
      <Ionicons 
        name={icon} 
        size={20} 
        color={status ? '#4caf50' : '#f44336'} 
      />
      <Text style={styles.serviceName}>{name}</Text>
      <View style={[
        styles.statusDot,
        { backgroundColor: status ? '#4caf50' : '#f44336' }
      ]} />
    </View>
  );

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#2196F3" />
        <Text style={styles.loadingText}>Загрузка профиля...</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      {/* Заголовок профиля */}
      <View style={styles.header}>
        <View style={styles.avatarContainer}>
          <Ionicons name="person" size={40} color="#2196F3" />
        </View>
        <Text style={styles.userName}>Активный гражданин</Text>
        <Text style={styles.userRole}>Участник программы мониторинга</Text>
      </View>

      {/* Персональная статистика */}
      {userStats && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>📊 Моя статистика</Text>
          
          <View style={styles.statsGrid}>
            {renderStatCard(
              'Мои нарушения',
              userStats.total_violations || 0,
              'alert-circle',
              '#f44336'
            )}
            
            {renderStatCard(
              'Активные',
              userStats.active_violations || 0,
              'warning',
              '#ff9800'
            )}
            
            {renderStatCard(
              'Решенные',
              userStats.resolved_violations || 0,
              'checkmark-circle',
              '#4caf50'
            )}
            
            {renderStatCard(
              'Средняя точность',
              userStats.avg_confidence 
                ? `${Math.round(userStats.avg_confidence * 100)}%`
                : 'Н/Д',
              'analytics',
              '#2196F3'
            )}
          </View>
          
          {/* Последние нарушения пользователя */}
          {userStats.recent_violations && userStats.recent_violations.length > 0 && (
            <View style={styles.recentViolations}>
              <Text style={styles.recentTitle}>Последние нарушения:</Text>
              {userStats.recent_violations.slice(0, 3).map((violation, index) => (
                <View key={index} style={styles.recentItem}>
                  <Ionicons 
                    name="alert-circle" 
                    size={16} 
                    color="#f44336" 
                  />
                  <Text style={styles.recentText}>
                    {violation.category || 'Нарушение'} - {new Date(violation.created_at).toLocaleDateString('ru-RU')}
                  </Text>
                </View>
              ))}
            </View>
          )}
        </View>
      )}
      
      {/* Статистика системы */}
      {analytics && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>📈 Статистика системы</Text>
          
          <View style={styles.statsGrid}>
            {renderStatCard(
              'Всего нарушений',
              analytics.summary?.total_violations || 0,
              'globe',
              '#6c757d'
            )}
            
            {renderStatCard(
              'Всего фото',
              analytics.summary?.total_photos || 0,
              'camera',
              '#6c757d'
            )}
            
            {renderStatCard(
              'За неделю',
              analytics.summary?.recent_violations || 0,
              'trending-up',
              '#6c757d'
            )}
            
            {renderStatCard(
              'Общая точность',
              analytics.summary?.avg_confidence 
                ? `${Math.round(analytics.summary.avg_confidence * 100)}%`
                : 'Н/Д',
              'stats-chart',
              '#6c757d'
            )}
          </View>
        </View>
      )}

      {/* Статус сервисов */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>🔧 Статус сервисов</Text>
        
        <View style={styles.servicesContainer}>
          {serverStatus && (
            <>
              {renderServiceStatus(
                'Сервер приложений',
                serverStatus.online,
                'server'
              )}
              
              {analytics?.services && (
                <>
                  {renderServiceStatus(
                    'YOLO детектор',
                    analytics.services.yolo_detector,
                    'eye'
                  )}
                  {renderServiceStatus(
                    'Mistral AI',
                    analytics.services.mistral_ai,
                    'bulb'
                  )}
                  
                  {renderServiceStatus(
                    'База данных',
                    analytics.services.database,
                    'library'
                  )}
                  
                  {renderServiceStatus(
                    'Геолокация',
                    analytics.services.geolocation,
                    'location'
                  )}
                </>
              )}
            </>
          )}
        </View>
        
        <TouchableOpacity style={styles.refreshButton} onPress={handleRefresh}>
          <Ionicons name="refresh" size={16} color="#2196F3" />
          <Text style={styles.refreshText}>Обновить статус</Text>
        </TouchableOpacity>
      </View>

      {/* Настройки */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>⚙️ Настройки</Text>
        
        <View style={styles.settingItem}>
          <View style={styles.settingInfo}>
            <Ionicons name="notifications" size={20} color="#666" />
            <Text style={styles.settingText}>Уведомления</Text>
          </View>
          <Switch
            value={notifications}
            onValueChange={setNotifications}
            trackColor={{ false: '#ccc', true: '#2196F3' }}
            thumbColor={notifications ? '#fff' : '#fff'}
          />
        </View>
        
        <View style={styles.settingItem}>
          <View style={styles.settingInfo}>
            <Ionicons name="location" size={20} color="#666" />
            <Text style={styles.settingText}>Автоопределение местоположения</Text>
          </View>
          <Switch
            value={autoLocation}
            onValueChange={setAutoLocation}
            trackColor={{ false: '#ccc', true: '#2196F3' }}
            thumbColor={autoLocation ? '#fff' : '#fff'}
          />
        </View>
      </View>

      {/* Информация пользователя */}
      {user && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>👤 Профиль пользователя</Text>
          
          <View style={styles.userInfo}>
            <View style={styles.userAvatar}>
              <Ionicons name="person" size={40} color="#2196F3" />
            </View>
            <View style={styles.userDetails}>
              <Text style={styles.userNameProfile}>{user?.username || 'Пользователь'}</Text>
              <Text style={styles.userEmail}>{user?.email || 'Не указан'}</Text>
              <Text style={styles.userStatus}>
                {user?.id && typeof user.id === 'string' && user.id.startsWith('guest_') ? 'Гостевой аккаунт' : 'Зарегистрированный пользователь'}
              </Text>
              {userStats && (
                <Text style={styles.userJoinDate}>
                  Участник с {userStats.join_date ? new Date(userStats.join_date).toLocaleDateString('ru-RU') : 'недавнего времени'}
                </Text>
              )}
            </View>
          </View>
        </View>
      )}

      {/* Действия */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>📱 Приложение</Text>
        
        <TouchableOpacity style={styles.actionItem} onPress={showHelp}>
          <Ionicons name="help-circle" size={20} color="#2196F3" />
          <Text style={styles.actionText}>Справка</Text>
          <Ionicons name="chevron-forward" size={16} color="#ccc" />
        </TouchableOpacity>
        
        <TouchableOpacity style={styles.actionItem} onPress={showAbout}>
          <Ionicons name="information-circle" size={20} color="#2196F3" />
          <Text style={styles.actionText}>О приложении</Text>
          <Ionicons name="chevron-forward" size={16} color="#ccc" />
        </TouchableOpacity>
        
        <TouchableOpacity 
          style={styles.actionItem} 
          onPress={() => {
            Alert.alert(
              'Обратная связь',
              'Отправить отзыв или сообщить о проблеме?\n\nEmail: support@geolocator.ru\nTelegram: @geolocator_support',
              [{ text: 'OK', style: 'default' }]
            );
          }}
        >
          <Ionicons name="mail" size={20} color="#2196F3" />
          <Text style={styles.actionText}>Обратная связь</Text>
          <Ionicons name="chevron-forward" size={16} color="#ccc" />
        </TouchableOpacity>

        {onLogout && (
          <TouchableOpacity 
            style={[styles.actionItem, styles.logoutButton]} 
            onPress={() => {
              Alert.alert(
                'Выход',
                'Вы уверены, что хотите выйти из аккаунта?',
                [
                  { text: 'Отмена', style: 'cancel' },
                  { text: 'Выйти', style: 'destructive', onPress: onLogout }
                ]
              );
            }}
          >
            <Ionicons name="log-out" size={20} color="#f44336" />
            <Text style={[styles.actionText, styles.logoutText]}>Выйти из аккаунта</Text>
            <Ionicons name="chevron-forward" size={16} color="#ccc" />
          </TouchableOpacity>
        )}
      </View>

      {/* Версия */}
      <View style={styles.footer}>
        <Text style={styles.versionText}>
          GeoLocator Mobile v1.0.0
        </Text>
        <Text style={styles.copyrightText}>
          © 2025 Hackathon Team AI_Python_Web
        </Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
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
  header: {
    backgroundColor: 'white',
    alignItems: 'center',
    padding: 30,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  avatarContainer: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#e3f2fd',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 15,
  },
  userName: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 5,
  },
  userRole: {
    fontSize: 14,
    color: '#666',
  },
  section: {
    backgroundColor: 'white',
    marginTop: 10,
    paddingHorizontal: 20,
    paddingVertical: 15,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  statCard: {
    width: '48%',
    backgroundColor: '#f8f9fa',
    borderRadius: 10,
    padding: 15,
    marginBottom: 10,
    borderLeftWidth: 4,
    flexDirection: 'row',
    alignItems: 'center',
  },
  statIcon: {
    marginRight: 10,
  },
  statInfo: {
    flex: 1,
  },
  statValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  statTitle: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  servicesContainer: {
    backgroundColor: '#f8f9fa',
    borderRadius: 10,
    padding: 15,
  },
  serviceItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
  },
  serviceName: {
    flex: 1,
    fontSize: 14,
    color: '#333',
    marginLeft: 10,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  refreshButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 15,
    paddingVertical: 10,
  },
  refreshText: {
    fontSize: 14,
    color: '#2196F3',
    marginLeft: 5,
  },
  settingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  settingInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  settingText: {
    fontSize: 14,
    color: '#333',
    marginLeft: 15,
  },
  actionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  actionText: {
    flex: 1,
    fontSize: 14,
    color: '#333',
    marginLeft: 15,
  },
  footer: {
    alignItems: 'center',
    padding: 30,
  },
  versionText: {
    fontSize: 12,
    color: '#999',
    marginBottom: 5,
  },
  copyrightText: {
    fontSize: 12,
    color: '#ccc',
  },
  userInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 15,
  },
  userAvatar: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#f0f8ff',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 15,
  },
  userDetails: {
    flex: 1,
  },
  userName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },
  userEmail: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  userStatus: {
    fontSize: 12,
    color: '#2196F3',
    fontWeight: '500',
  },
  logoutButton: {
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
    marginTop: 10,
  },
  logoutText: {
    color: '#f44336',
  },
  recentViolations: {
    marginTop: 15,
    padding: 15,
    backgroundColor: '#f8f9fa',
    borderRadius: 10,
  },
  recentTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#495057',
    marginBottom: 10,
  },
  recentItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 4,
  },
  recentText: {
    fontSize: 12,
    color: '#6c757d',
    marginLeft: 8,
    flex: 1,
  },
  userNameProfile: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },
  userJoinDate: {
    fontSize: 11,
    color: '#28a745',
    marginTop: 2,
  },
});
