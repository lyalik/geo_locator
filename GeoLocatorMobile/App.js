import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { StatusBar } from 'expo-status-bar';
import { Ionicons } from '@expo/vector-icons';

// Импорт экранов с поддержкой веб-платформы
import {
  CameraScreen,
  MapScreen,
  HistoryScreen,
  ProfileScreen
} from './src/utils/PlatformComponents';

const Tab = createBottomTabNavigator();

export default function App() {
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
          component={HistoryScreen} 
          options={{ 
            title: 'История',
            headerTitle: 'Мои отчеты'
          }} 
        />
        <Tab.Screen 
          name="Profile" 
          component={ProfileScreen} 
          options={{ 
            title: 'Профиль',
            headerTitle: 'Мой профиль'
          }} 
        />
      </Tab.Navigator>
    </NavigationContainer>
  );
}
