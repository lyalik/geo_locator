import { Platform } from 'react-native';

// Экраны, которые работают на всех платформах
import HistoryScreen from '../screens/HistoryScreen';
import ProfileScreen from '../screens/ProfileScreen';

// Веб-версии экранов
import CameraScreenWeb from '../screens/CameraScreen.web';
import MapScreenWeb from '../screens/MapScreen.web';

// Мобильные версии экранов (только для не-веб платформ)
let CameraScreenMobile, MapScreenMobile;

if (Platform.OS !== 'web') {
  CameraScreenMobile = require('../screens/CameraScreen').default;
  MapScreenMobile = require('../screens/MapScreen').default;
}

// Экспорт с условной логикой
export const CameraScreen = Platform.OS === 'web' ? CameraScreenWeb : CameraScreenMobile;
export const MapScreen = Platform.OS === 'web' ? MapScreenWeb : MapScreenMobile;

export {
  HistoryScreen,
  ProfileScreen
};
