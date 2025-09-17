import React, { useState, useEffect } from 'react';
import { View, Text, ActivityIndicator } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import { StatusBar } from 'expo-status-bar';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import NotificationService from './src/services/NotificationService';

// Импорт экранов с поддержкой веб-платформы
import {
  CameraScreen,
  MapScreen,
  HistoryScreen,
  ProfileScreen
} from './src/utils/PlatformComponents';
import LoginScreen from './src/screens/LoginScreen';
import ViolationDetailScreen from './src/screens/ViolationDetailScreen';

const Tab = createBottomTabNavigator();
const Stack = createStackNavigator();

// Stack Navigator для History с ViolationDetail
function HistoryStack() {
  return (
    <Stack.Navigator>
      <Stack.Screen 
        name="HistoryMain" 
        component={HistoryScreen}
        options={{ headerShown: false }}
      />
      <Stack.Screen 
        name="ViolationDetail" 
        component={ViolationDetailScreen}
        options={{ 
          title: 'Детали нарушения',
          headerStyle: { backgroundColor: '#2196F3' },
          headerTintColor: '#fff',
          headerTitleStyle: { fontWeight: 'bold' }
        }}
      />
    </Stack.Navigator>
  );
}

export default function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuthState();
    initializeNotifications();
  }, []);

  const initializeNotifications = async () => {
    try {
      await NotificationService.initialize();
    } catch (error) {
      console.error('Ошибка инициализации уведомлений:', error);
    }
  };

  const checkAuthState = async () => {
    try {
      console.log('🔍 Проверка состояния авторизации...');
      const userData = await AsyncStorage.getItem('user');
      console.log('👤 Данные пользователя из AsyncStorage:', userData);
      
      if (userData) {
        const parsedUser = JSON.parse(userData);
        console.log('✅ Пользователь найден:', parsedUser);
        setUser(parsedUser);
      } else {
        console.log('❌ Пользователь не найден, показываем экран логина');
      }
    } catch (error) {
      console.error('❌ Ошибка проверки состояния авторизации:', error);
    } finally {
      console.log('🏁 Завершение проверки авторизации, loading = false');
      setLoading(false);
    }
  };

  const handleLogin = async (userData) => {
    try {
      await AsyncStorage.setItem('user', JSON.stringify(userData));
      setUser(userData);
    } catch (error) {
      console.error('Error saving user data:', error);
    }
  };

  const handleLogout = async () => {
    try {
      await AsyncStorage.removeItem('user');
      await AsyncStorage.removeItem('authToken');
      NotificationService.cleanup();
      setUser(null);
    } catch (error) {
      console.error('Error removing user data:', error);
    }
  };

  if (loading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#f5f5f5' }}>
        <ActivityIndicator size="large" color="#2196F3" />
        <Text style={{ marginTop: 16, fontSize: 16, color: '#666' }}>
          Загрузка приложения...
        </Text>
      </View>
    );
  }

  if (!user) {
    return <LoginScreen onLogin={handleLogin} />;
  }

  return (
    <NavigationContainer>
      <StatusBar style="auto" />
      <Tab.Navigator
        screenOptions={({ route }) => ({
          tabBarIcon: ({ focused, color, size }) => {
            let iconName;

            if (route.name === 'Camera') {
              iconName = focused ? 'camera' : 'camera-outline';
            } else if (route.name === 'Map') {
              iconName = focused ? 'map' : 'map-outline';
            } else if (route.name === 'History') {
              iconName = focused ? 'list' : 'list-outline';
            } else if (route.name === 'Profile') {
              iconName = focused ? 'person' : 'person-outline';
            }

            return <Ionicons name={iconName} size={size} color={color} />;
          },
          tabBarActiveTintColor: '#2196F3',
          tabBarInactiveTintColor: 'gray',
          headerStyle: {
            backgroundColor: '#2196F3',
          },
          headerTintColor: '#fff',
          headerTitleStyle: {
            fontWeight: 'bold',
          },
        })}
      >
        <Tab.Screen 
          name="Camera" 
          component={CameraScreen} 
          options={{ 
            title: 'Камера',
            headerTitle: 'Детекция нарушений'
          }} 
        />
        <Tab.Screen 
          name="Map" 
          component={MapScreen} 
          options={{ 
            title: 'Карта',
            headerTitle: 'Карта нарушений'
          }} 
        />
        <Tab.Screen 
          name="History" 
          component={HistoryStack} 
          options={{ 
            title: 'История',
            headerTitle: 'Мои отчеты'
          }} 
        />
        <Tab.Screen 
          name="Profile" 
          options={{ 
            title: 'Профиль',
            headerTitle: 'Мой профиль'
          }} 
        >
          {() => <ProfileScreen user={user} onLogout={handleLogout} />}
        </Tab.Screen>
      </Tab.Navigator>
    </NavigationContainer>
  );
}
