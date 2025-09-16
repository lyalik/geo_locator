import * as Notifications from 'expo-notifications';
import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import ApiService from './ApiService';

// Настройка поведения уведомлений
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
});

class NotificationService {
  constructor() {
    this.expoPushToken = null;
    this.notificationListener = null;
    this.responseListener = null;
  }

  async initialize() {
    try {
      // Регистрируем для push уведомлений
      this.expoPushToken = await this.registerForPushNotificationsAsync();
      
      if (this.expoPushToken) {
        console.log('📱 Push token получен:', this.expoPushToken);
        
        // Сохраняем токен в AsyncStorage
        await AsyncStorage.setItem('pushToken', this.expoPushToken);
        
        // Отправляем токен на сервер
        await this.sendTokenToServer(this.expoPushToken);
      }

      // Слушатель входящих уведомлений
      this.notificationListener = Notifications.addNotificationReceivedListener(notification => {
        console.log('📨 Получено уведомление:', notification);
        this.handleNotificationReceived(notification);
      });

      // Слушатель нажатий на уведомления
      this.responseListener = Notifications.addNotificationResponseReceivedListener(response => {
        console.log('👆 Нажатие на уведомление:', response);
        this.handleNotificationResponse(response);
      });

    } catch (error) {
      console.error('❌ Ошибка инициализации уведомлений:', error);
    }
  }

  async registerForPushNotificationsAsync() {
    let token;

    if (Platform.OS === 'android') {
      await Notifications.setNotificationChannelAsync('default', {
        name: 'default',
        importance: Notifications.AndroidImportance.MAX,
        vibrationPattern: [0, 250, 250, 250],
        lightColor: '#FF231F7C',
      });
    }

    // Проверяем разрешения на уведомления
    const { status: existingStatus } = await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus;
    
    if (existingStatus !== 'granted') {
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
    }
    
    if (finalStatus !== 'granted') {
      console.log('❌ Разрешение на уведомления не получено');
      return null;
    }
    
    try {
      token = (await Notifications.getExpoPushTokenAsync()).data;
    } catch (error) {
      console.log('⚠️ Ошибка получения push токена:', error.message);
      return null;
    }

    return token;
  }

  async sendTokenToServer(token) {
    try {
      const user = await AsyncStorage.getItem('user');
      if (user) {
        const userData = JSON.parse(user);
        
        // Отправляем токен на сервер для сохранения
        await ApiService.api.post('/api/notifications/save-push-token', {
          pushToken: token,
          platform: Platform.OS
        });
        
        console.log('✅ Push token отправлен на сервер');
      }
    } catch (error) {
      console.error('❌ Ошибка отправки токена на сервер:', error);
    }
  }

  handleNotificationReceived(notification) {
    const { data } = notification.request.content;
    
    // Обработка различных типов уведомлений
    switch (data?.type) {
      case 'violation_status_changed':
        this.handleViolationStatusNotification(data);
        break;
      case 'new_violation_detected':
        this.handleNewViolationNotification(data);
        break;
      default:
        console.log('📨 Обычное уведомление:', notification.request.content);
    }
  }

  handleNotificationResponse(response) {
    const { data } = response.notification.request.content;
    
    // Навигация в зависимости от типа уведомления
    if (data?.violation_id) {
      // Можно добавить навигацию к конкретному нарушению
      console.log('🔗 Переход к нарушению:', data.violation_id);
    }
  }

  handleViolationStatusNotification(data) {
    console.log('📋 Статус нарушения изменен:', data);
    // Можно обновить локальные данные или показать специальное уведомление
  }

  handleNewViolationNotification(data) {
    console.log('🚨 Новое нарушение обнаружено:', data);
    // Можно обновить карту или список нарушений
  }

  // Отправка локального уведомления
  async sendLocalNotification(title, body, data = {}) {
    try {
      await Notifications.scheduleNotificationAsync({
        content: {
          title,
          body,
          data,
          sound: 'default',
        },
        trigger: null, // Показать немедленно
      });
    } catch (error) {
      console.error('❌ Ошибка отправки локального уведомления:', error);
    }
  }

  // Очистка слушателей при размонтировании
  cleanup() {
    if (this.notificationListener) {
      Notifications.removeNotificationSubscription(this.notificationListener);
    }
    if (this.responseListener) {
      Notifications.removeNotificationSubscription(this.responseListener);
    }
  }

  // Получение токена
  getToken() {
    return this.expoPushToken;
  }

  // Проверка разрешений
  async checkPermissions() {
    const { status } = await Notifications.getPermissionsAsync();
    return status === 'granted';
  }

  // Запрос разрешений
  async requestPermissions() {
    const { status } = await Notifications.requestPermissionsAsync();
    return status === 'granted';
  }
}

export default new NotificationService();
