# 🚀 **GeoLocator Mobile - Руководство по развертыванию**

## 📋 **Содержание**
1. [Системные требования](#системные-требования)
2. [Локальная разработка](#локальная-разработка)
3. [Веб-развертывание](#веб-развертывание)
4. [Мобильная сборка](#мобильная-сборка)
5. [Production развертывание](#production-развертывание)
6. [Troubleshooting](#troubleshooting)

---

## 🖥️ **Системные требования**

### **Минимальные требования:**
- **Node.js:** 18.20.6+ (рекомендуется 20.x)
- **npm:** 10.8.2+
- **RAM:** 4GB (рекомендуется 8GB)
- **Свободное место:** 2GB

### **Дополнительные инструменты:**
```bash
# Expo CLI (глобально)
npm install -g @expo/cli

# EAS CLI для production сборок (опционально)
npm install -g eas-cli

# Yarn как альтернатива npm (опционально)
npm install -g yarn
```

### **Для мобильной разработки:**
- **Android Studio** + Android SDK (для Android)
- **Xcode** (для iOS, только macOS)
- **Expo Go** приложение на мобильном устройстве

---

## 💻 **Локальная разработка**

### **1. Клонирование и установка:**
```bash
# Переход в папку проекта
cd /path/to/geo_locator/GeoLocatorMobile

# Установка зависимостей
npm install

# Или с Yarn
yarn install
```

### **2. Настройка backend URL:**
```javascript
// src/services/ApiService.js
const API_BASE_URL = 'http://localhost:5000';  // Локальный backend

// Для тестирования на реальном устройстве:
// const API_BASE_URL = 'http://192.168.1.100:5000';  // IP вашего компьютера
```

### **3. Запуск в режиме разработки:**
```bash
# Запуск всех платформ
npx expo start

# Только веб-версия
npx expo start --web

# Только Android
npx expo start --android

# Только iOS (macOS)
npx expo start --ios

# С очисткой кэша
npx expo start --clear
```

### **4. Доступные команды:**
```bash
# Проверка зависимостей
npx expo doctor

# Обновление зависимостей
npx expo install --fix

# Просмотр конфигурации
npx expo config

# Запуск тестов (если настроены)
npm test
```

---

## 🌐 **Веб-развертывание**

### **1. Локальная веб-сборка:**
```bash
# Сборка для production
npx expo export:web

# Результат в папке web-build/
ls web-build/
```

### **2. Развертывание на Netlify:**
```bash
# Установка Netlify CLI
npm install -g netlify-cli

# Сборка проекта
npx expo export:web

# Развертывание
netlify deploy --dir=web-build --prod

# Или через drag & drop на netlify.com
```

### **3. Развертывание на Vercel:**
```bash
# Установка Vercel CLI
npm install -g vercel

# Сборка и развертывание
npx expo export:web
vercel --prod

# Или подключить GitHub репозиторий к vercel.com
```

### **4. Развертывание на GitHub Pages:**
```bash
# Установка gh-pages
npm install --save-dev gh-pages

# Добавить в package.json:
{
  "scripts": {
    "predeploy": "npx expo export:web",
    "deploy": "gh-pages -d web-build"
  },
  "homepage": "https://yourusername.github.io/geo-locator-mobile"
}

# Развертывание
npm run deploy
```

### **5. Docker развертывание:**
```dockerfile
# Dockerfile
FROM node:18-alpine

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npx expo export:web

FROM nginx:alpine
COPY --from=0 /app/web-build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

```bash
# Сборка и запуск
docker build -t geo-locator-mobile .
docker run -p 80:80 geo-locator-mobile
```

---

## 📱 **Мобильная сборка**

### **1. Expo Go (Development):**
```bash
# Запуск для тестирования
npx expo start

# Сканирование QR-кода в Expo Go приложении
# iOS: Камера или Expo Go
# Android: Expo Go приложение
```

### **2. Development Build:**
```bash
# Создание development build
npx expo run:android  # Android
npx expo run:ios      # iOS (macOS only)

# Или через EAS Build
eas build --profile development --platform android
eas build --profile development --platform ios
```

### **3. Production Build (EAS Build):**
```bash
# Настройка EAS
eas login
eas build:configure

# Сборка для production
eas build --platform android --profile production
eas build --platform ios --profile production

# Сборка для обеих платформ
eas build --platform all --profile production
```

### **4. Конфигурация EAS (eas.json):**
```json
{
  "cli": {
    "version": ">= 5.2.0"
  },
  "build": {
    "development": {
      "developmentClient": true,
      "distribution": "internal"
    },
    "preview": {
      "distribution": "internal",
      "android": {
        "buildType": "apk"
      }
    },
    "production": {
      "android": {
        "buildType": "aab"
      }
    }
  },
  "submit": {
    "production": {
      "android": {
        "serviceAccountKeyPath": "../path/to/api-key.json",
        "track": "internal"
      },
      "ios": {
        "appleId": "your-apple-id@example.com",
        "ascAppId": "1234567890",
        "appleTeamId": "ABCDEFGHIJ"
      }
    }
  }
}
```

---

## 🏭 **Production развертывание**

### **1. Переменные окружения:**
```bash
# .env.production
API_BASE_URL=https://api.geolocator.ru
SENTRY_DSN=https://your-sentry-dsn
ANALYTICS_ID=GA-XXXXXXXXX
```

### **2. Оптимизация для production:**
```javascript
// app.json - production настройки
{
  "expo": {
    "name": "GeoLocator Mobile",
    "version": "1.0.0",
    "orientation": "portrait",
    "updates": {
      "fallbackToCacheTimeout": 0,
      "url": "https://u.expo.dev/your-project-id"
    },
    "runtimeVersion": "1.0.0",
    "extra": {
      "eas": {
        "projectId": "your-project-id"
      }
    }
  }
}
```

### **3. Мониторинг и аналитика:**
```bash
# Установка Sentry для отслеживания ошибок
npx expo install @sentry/react-native

# Установка аналитики
npx expo install expo-analytics-amplitude
```

### **4. Over-the-Air Updates:**
```bash
# Настройка EAS Update
eas update:configure

# Публикация обновления
eas update --branch production --message "Bug fixes and improvements"

# Откат к предыдущей версии
eas update --branch production --republish
```

---

## 🔧 **Настройка CI/CD**

### **1. GitHub Actions (.github/workflows/deploy.yml):**
```yaml
name: Deploy GeoLocator Mobile

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  web-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
          
      - name: Install dependencies
        run: npm ci
        
      - name: Build web
        run: npx expo export:web
        
      - name: Deploy to Netlify
        uses: nwtgck/actions-netlify@v2.0
        with:
          publish-dir: './web-build'
          production-branch: main
        env:
          NETLIFY_AUTH_TOKEN: ${{ secrets.NETLIFY_AUTH_TOKEN }}
          NETLIFY_SITE_ID: ${{ secrets.NETLIFY_SITE_ID }}

  mobile-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Expo
        uses: expo/expo-github-action@v8
        with:
          expo-version: latest
          token: ${{ secrets.EXPO_TOKEN }}
          
      - name: Install dependencies
        run: npm ci
        
      - name: Build Android
        run: eas build --platform android --non-interactive
```

### **2. Автоматическое тестирование:**
```bash
# Установка тестовых зависимостей
npm install --save-dev jest @testing-library/react-native

# package.json
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage"
  }
}
```

---

## 🛠️ **Troubleshooting**

### **Частые проблемы и решения:**

#### **1. Metro bundler не запускается:**
```bash
# Очистка кэша
npx expo start --clear
rm -rf node_modules
npm install

# Проверка портов
lsof -ti:8081 | xargs kill -9
```

#### **2. Ошибки с зависимостями:**
```bash
# Обновление до совместимых версий
npx expo install --fix

# Проверка совместимости
npx expo doctor
```

#### **3. Проблемы с веб-версией:**
```bash
# Установка веб-зависимостей
npx expo install react-dom react-native-web

# Проверка поддержки платформы
# Убедитесь что используете .web.js файлы для веб-специфичного кода
```

#### **4. Ошибки сборки Android:**
```bash
# Очистка Gradle кэша
cd android && ./gradlew clean
cd .. && npx expo run:android --clear

# Проверка Java версии
java -version  # Должна быть 11 или 17
```

#### **5. Проблемы с iOS (macOS):**
```bash
# Очистка iOS кэша
cd ios && rm -rf build
cd .. && npx expo run:ios --clear

# Обновление CocoaPods
cd ios && pod install --repo-update
```

#### **6. Проблемы с API подключением:**
```javascript
// Проверка# 1. Убедитесь что backend запущен на localhost:5001
cd ../backend && python app.py
// Проверка доступности backend
const checkBackend = async () => {
  try {
    const response = await fetch('http://your-backend-url/api/violations/analytics');
    console.log('Backend status:', response.status);
  } catch (error) {
    console.error('Backend unavailable:', error);
  }
};
```

### **Логи и отладка:**
```bash
# Просмотр логов Metro
npx expo start --verbose

# Логи устройства
npx expo logs --type device

# Логи симулятора
npx expo logs --type simulator
```

---

## 📊 **Мониторинг производительности**

### **1. Bundle анализ:**
```bash
# Анализ размера bundle
npx expo export:web --dump-assetmap

# Webpack Bundle Analyzer (для веб)
npm install --save-dev webpack-bundle-analyzer
```

### **2. Метрики производительности:**
```javascript
// Performance monitoring
import { Performance } from 'expo-performance';

Performance.mark('app-start');
// ... app logic
Performance.measure('app-load-time', 'app-start');
```

---

## 🔒 **Безопасность**

### **1. Защита API ключей:**
```javascript
// app.config.js
export default {
  expo: {
    extra: {
      apiUrl: process.env.API_URL || 'http://localhost:5000',
      // Никогда не храните секретные ключи в коде!
    }
  }
};
```

### **2. HTTPS в production:**
```javascript
// Принудительное использование HTTPS
const API_BASE_URL = __DEV__ 
  ? 'http://localhost:5000' 
  : 'https://api.geolocator.ru';
```

---

## 📈 **Масштабирование**

### **1. Code Splitting:**
```javascript
// Ленивая загрузка экранов
const CameraScreen = React.lazy(() => import('./screens/CameraScreen'));
const MapScreen = React.lazy(() => import('./screens/MapScreen'));
```

### **2. Кэширование:**
```javascript
// React Query для кэширования API
import { QueryClient, QueryClientProvider } from 'react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 минут
    },
  },
});
```

---

**📱 Мобильное приложение готово к развертыванию на всех платформах!**

*Обновлено: 16 сентября 2025 г.*
