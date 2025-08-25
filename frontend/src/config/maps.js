// API Keys and map configurations
export const MAP_CONFIG = {
  yandex: {
    apiKey: process.env.REACT_APP_YANDEX_MAPS_API_KEY || 'YOUR_YANDEX_MAPS_API_KEY',
    version: '2.1',
    lang: 'ru_RU',
    coordorder: 'latlong',
    mode: 'release'
  },
  dgis: {
    apiKey: process.env.REACT_APP_DGIS_API_KEY || 'YOUR_DGIS_API_KEY',
    version: '1.0',
    lang: 'ru'
  }
};

// Default map center (Moscow)
export const DEFAULT_MAP_CENTER = [55.7558, 37.6173];
export const DEFAULT_ZOOM = 12;
