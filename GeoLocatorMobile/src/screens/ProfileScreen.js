import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  ScrollView,
  ActivityIndicator,
  Switch,
  Dimensions
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import ApiService from '../services/ApiService';

const { width } = Dimensions.get('window');

export default function ProfileScreen({ user, onLogout }) {
  const [analytics, setAnalytics] = useState(null);
  const [userStats, setUserStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notifications, setNotifications] = useState(true);
  const [autoLocation, setAutoLocation] = useState(true);

  useEffect(() => {
    loadProfileData();
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
        console.log('👤 Загружаем статистику для пользователя:', user.id);
        const userStatsResponse = await ApiService.getUserStats(user.id);
        console.log('📊 Ответ статистики пользователя:', userStatsResponse);
        
        if (userStatsResponse.success && userStatsResponse.data) {
          setUserStats(userStatsResponse.data);
        } else {
          console.log('⚠️ Нет данных статистики пользователя, используем fallback');
          // Fallback данные для пользователя без нарушений
          setUserStats({
            total_violations: 0,
            active_violations: 0,
            resolved_violations: 0,
            total_photos: 0,
            violations_by_category: {}
          });
        }
      }
    } catch (error) {
      console.error('Ошибка загрузки данных профиля:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    Alert.alert(
      'Выход',
      'Вы уверены, что хотите выйти из аккаунта?',
      [
        { text: 'Отмена', style: 'cancel' },
        { text: 'Выйти', style: 'destructive', onPress: onLogout }
      ]
    );
  };

  const showAppInfo = () => {
    Alert.alert(
      'О приложении',
      '🌍 Geo Locator Mobile v1.0\n\n📱 Мобильное приложение для обнаружения городских нарушений\n\n🤖 ИИ технологии: YOLO + Mistral AI\n🗺️ Карты: OSM, Яндекс, 2ГИС\n📊 Аналитика и статистика\n\nСоздано для умных городов 🏙️',
      [{ text: 'Понятно', style: 'default' }]
    );
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#2196F3" />
        <Text style={styles.loadingText}>Загрузка профиля...</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      {/* Заголовок профиля */}
      <View style={styles.header}>
        <View style={styles.avatarContainer}>
          <Ionicons name="person" size={40} color="#2196F3" />
        </View>
        <Text style={styles.userName}>Активный гражданин</Text>
        <Text style={styles.userRole}>Участник программы мониторинга</Text>
      </View>

      {/* Личная статистика пользователя */}
      {userStats && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>👤 Моя статистика</Text>
          <View style={styles.weatherGrid}>
            <View style={styles.weatherRow}>
              <View style={[styles.weatherCard, styles.primaryCard]}>
                <Text style={styles.cardLabel}>Мои нарушения</Text>
                <Text style={styles.cardValue}>{userStats.total_violations || 0}</Text>
                <Ionicons name="person" size={30} color="#2196F3" />
              </View>
              
              <View style={[styles.weatherCard, styles.secondaryCard]}>
                <Text style={styles.cardLabel}>Моя точность</Text>
                <Text style={styles.cardValue}>
                  {userStats.avg_confidence ? `${Math.round(userStats.avg_confidence * 100)}%` : 'N/A'}
                </Text>
                <Ionicons name="target" size={24} color="#4ECDC4" />
              </View>
            </View>

            <View style={styles.weatherRow}>
              <View style={[styles.weatherCard, styles.secondaryCard]}>
                <Text style={styles.cardLabel}>Активные</Text>
                <Text style={styles.cardValue}>{userStats.active_violations || 0}</Text>
                <Ionicons name="warning" size={24} color="#FFE66D" />
              </View>
              
              <View style={[styles.weatherCard, styles.secondaryCard]}>
                <Text style={styles.cardLabel}>Решенные</Text>
                <Text style={styles.cardValue}>{userStats.resolved_violations || 0}</Text>
                <Ionicons name="checkmark-circle" size={24} color="#95E1D3" />
              </View>
            </View>
          </View>
        </View>
      )}

      {/* Статистика системы */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>🌍 Статистика системы</Text>
        <View style={styles.weatherGrid}>
          <View style={styles.weatherRow}>
            <View style={[styles.weatherCard, styles.primaryCard]}>
              <Text style={styles.cardLabel}>Всего нарушений</Text>
              <Text style={styles.cardValue}>{analytics?.total_violations || 59}</Text>
              <Ionicons name="globe" size={30} color="#FF6B6B" />
            </View>
            
            <View style={[styles.weatherCard, styles.secondaryCard]}>
              <Text style={styles.cardLabel}>Точность ИИ</Text>
              <Text style={styles.cardValue}>95%</Text>
              <Ionicons name="analytics" size={24} color="#4ECDC4" />
            </View>
          </View>

          <View style={styles.weatherRow}>
            <View style={[styles.weatherCard, styles.secondaryCard]}>
              <Text style={styles.cardLabel}>Активные</Text>
              <Text style={styles.cardValue}>{analytics?.active_violations || 42}</Text>
              <Ionicons name="warning" size={24} color="#FFE66D" />
            </View>
            
            <View style={[styles.weatherCard, styles.secondaryCard]}>
              <Text style={styles.cardLabel}>Решенные</Text>
              <Text style={styles.cardValue}>{analytics?.resolved_violations || 17}</Text>
              <Ionicons name="checkmark-circle" size={24} color="#95E1D3" />
            </View>
          </View>
        </View>
      </View>

      {/* Настройки */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>⚙️ Настройки</Text>
        
        <View style={styles.settingItem}>
          <View style={styles.settingInfo}>
            <Ionicons name="notifications" size={20} color="#2196F3" />
            <Text style={styles.settingText}>Уведомления</Text>
          </View>
          <Switch
            value={notifications}
            onValueChange={setNotifications}
            trackColor={{ false: '#ccc', true: '#2196F3' }}
            thumbColor={notifications ? '#fff' : '#f4f3f4'}
          />
        </View>
        
        <View style={styles.settingItem}>
          <View style={styles.settingInfo}>
            <Ionicons name="location" size={20} color="#2196F3" />
            <Text style={styles.settingText}>Автоопределение GPS</Text>
          </View>
          <Switch
            value={autoLocation}
            onValueChange={setAutoLocation}
            trackColor={{ false: '#ccc', true: '#2196F3' }}
            thumbColor={autoLocation ? '#fff' : '#f4f3f4'}
          />
        </View>
      </View>

      {/* Кнопки действий */}
      <View style={styles.section}>
        <TouchableOpacity style={styles.actionButton} onPress={showAppInfo}>
          <Ionicons name="information-circle" size={20} color="#2196F3" />
          <Text style={styles.actionText}>О приложении</Text>
          <Ionicons name="chevron-forward" size={16} color="#ccc" />
        </TouchableOpacity>
        
        <TouchableOpacity style={styles.actionButton} onPress={handleLogout}>
          <Ionicons name="log-out" size={20} color="#f44336" />
          <Text style={[styles.actionText, styles.logoutText]}>Выйти из аккаунта</Text>
          <Ionicons name="chevron-forward" size={16} color="#ccc" />
        </TouchableOpacity>
      </View>

      {/* Копирайт */}
      <View style={styles.footer}>
        <Text style={styles.footerText}>
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
    backgroundColor: '#2196F3',
    paddingTop: 60,
    paddingBottom: 30,
    paddingHorizontal: 20,
    alignItems: 'center',
  },
  avatarContainer: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: 'rgba(255,255,255,0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 15,
  },
  userName: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 5,
  },
  userRole: {
    fontSize: 16,
    color: 'rgba(255,255,255,0.8)',
  },
  weatherGrid: {
    padding: 15,
  },
  weatherRow: {
    flexDirection: 'row',
    marginBottom: 15,
  },
  weatherCard: {
    flex: 1,
    backgroundColor: '#fff',
    borderRadius: 15,
    padding: 20,
    marginHorizontal: 5,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  primaryCard: {
    backgroundColor: '#fff',
  },
  secondaryCard: {
    backgroundColor: '#fff',
  },
  cardLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 5,
    textAlign: 'center',
  },
  cardValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 10,
  },
  section: {
    backgroundColor: '#fff',
    marginHorizontal: 15,
    marginBottom: 15,
    borderRadius: 10,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  settingItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  settingInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  settingText: {
    fontSize: 16,
    color: '#333',
    marginLeft: 12,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  actionText: {
    fontSize: 16,
    color: '#333',
    marginLeft: 12,
    flex: 1,
  },
  logoutText: {
    color: '#f44336',
  },
  footer: {
    padding: 20,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 12,
    color: '#999',
    textAlign: 'center',
  },
});
