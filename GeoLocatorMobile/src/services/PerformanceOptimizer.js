import * as ImageManipulator from 'expo-image-manipulator';
import AsyncStorage from '@react-native-async-storage/async-storage';

class PerformanceOptimizer {
  constructor() {
    this.CACHE_KEY = 'performance_cache';
    this.MAX_IMAGE_SIZE = 1920; // Максимальный размер изображения
    this.COMPRESSION_QUALITY = 0.8; // Качество сжатия
    this.CACHE_SIZE_LIMIT = 50 * 1024 * 1024; // 50MB лимит кэша
  }

  // Оптимизация изображения
  async optimizeImage(imageUri, options = {}) {
    try {
      const {
        maxSize = this.MAX_IMAGE_SIZE,
        quality = this.COMPRESSION_QUALITY,
        format = ImageManipulator.SaveFormat.JPEG
      } = options;

      console.log('🔧 Начинаем оптимизацию изображения:', {
        originalUri: imageUri,
        maxSize,
        quality,
        format
      });

      // Получаем информацию об изображении
      const imageInfo = await this.getImageInfo(imageUri);
      console.log('📊 Информация об изображении:', imageInfo);

      // Определяем нужно ли изменение размера
      const needsResize = imageInfo.width > maxSize || imageInfo.height > maxSize;
      
      if (!needsResize && quality >= 1.0) {
        console.log('✅ Изображение не требует оптимизации');
        return {
          uri: imageUri,
          optimized: false,
          originalSize: imageInfo,
          finalSize: imageInfo
        };
      }

      // Вычисляем новые размеры с сохранением пропорций
      let newWidth = imageInfo.width;
      let newHeight = imageInfo.height;

      if (needsResize) {
        const aspectRatio = imageInfo.width / imageInfo.height;
        
        if (imageInfo.width > imageInfo.height) {
          newWidth = Math.min(maxSize, imageInfo.width);
          newHeight = newWidth / aspectRatio;
        } else {
          newHeight = Math.min(maxSize, imageInfo.height);
          newWidth = newHeight * aspectRatio;
        }

        // Округляем до целых чисел
        newWidth = Math.round(newWidth);
        newHeight = Math.round(newHeight);
      }

      console.log('🎯 Новые размеры:', { newWidth, newHeight });

      // Применяем оптимизацию
      const manipulatorActions = [];

      if (needsResize) {
        manipulatorActions.push({
          resize: { width: newWidth, height: newHeight }
        });
      }

      const result = await ImageManipulator.manipulateAsync(
        imageUri,
        manipulatorActions,
        {
          compress: quality,
          format: format,
          base64: false
        }
      );

      const finalInfo = await this.getImageInfo(result.uri);

      console.log('✅ Оптимизация завершена:', {
        originalSize: `${imageInfo.width}x${imageInfo.height}`,
        finalSize: `${finalInfo.width}x${finalInfo.height}`,
        compressionRatio: ((imageInfo.fileSize - finalInfo.fileSize) / imageInfo.fileSize * 100).toFixed(1) + '%'
      });

      return {
        uri: result.uri,
        optimized: true,
        originalSize: imageInfo,
        finalSize: finalInfo,
        compressionRatio: (imageInfo.fileSize - finalInfo.fileSize) / imageInfo.fileSize
      };

    } catch (error) {
      console.error('❌ Ошибка оптимизации изображения:', error);
      return {
        uri: imageUri,
        optimized: false,
        error: error.message
      };
    }
  }

  // Получение информации об изображении
  async getImageInfo(imageUri) {
    try {
      // Для Expo используем fetch для получения размера файла
      const response = await fetch(imageUri);
      const blob = await response.blob();
      
      return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => {
          resolve({
            width: img.width,
            height: img.height,
            fileSize: blob.size,
            type: blob.type
          });
        };
        img.onerror = reject;
        img.src = imageUri;
      });
    } catch (error) {
      console.warn('⚠️ Не удалось получить полную информацию об изображении:', error);
      return {
        width: 0,
        height: 0,
        fileSize: 0,
        type: 'unknown'
      };
    }
  }

  // Создание превью изображения
  async createThumbnail(imageUri, size = 200) {
    try {
      console.log('🖼️ Создаем превью:', { imageUri, size });

      const result = await ImageManipulator.manipulateAsync(
        imageUri,
        [{ resize: { width: size, height: size } }],
        {
          compress: 0.7,
          format: ImageManipulator.SaveFormat.JPEG,
          base64: true
        }
      );

      return {
        uri: result.uri,
        base64: result.base64,
        size: size
      };
    } catch (error) {
      console.error('❌ Ошибка создания превью:', error);
      return null;
    }
  }

  // Пакетная оптимизация изображений
  async batchOptimizeImages(imageUris, options = {}) {
    console.log(`🔄 Начинаем пакетную оптимизацию ${imageUris.length} изображений`);
    
    const results = [];
    let totalOriginalSize = 0;
    let totalFinalSize = 0;

    for (let i = 0; i < imageUris.length; i++) {
      const imageUri = imageUris[i];
      console.log(`📸 Обрабатываем изображение ${i + 1}/${imageUris.length}`);
      
      try {
        const result = await this.optimizeImage(imageUri, options);
        results.push(result);
        
        if (result.originalSize && result.finalSize) {
          totalOriginalSize += result.originalSize.fileSize || 0;
          totalFinalSize += result.finalSize.fileSize || 0;
        }
      } catch (error) {
        console.error(`❌ Ошибка обработки изображения ${i + 1}:`, error);
        results.push({
          uri: imageUri,
          optimized: false,
          error: error.message
        });
      }
    }

    const totalCompressionRatio = totalOriginalSize > 0 
      ? (totalOriginalSize - totalFinalSize) / totalOriginalSize 
      : 0;

    console.log('✅ Пакетная оптимизация завершена:', {
      processed: results.length,
      totalCompressionRatio: (totalCompressionRatio * 100).toFixed(1) + '%',
      savedBytes: totalOriginalSize - totalFinalSize
    });

    return {
      results,
      stats: {
        processed: results.length,
        optimized: results.filter(r => r.optimized).length,
        totalOriginalSize,
        totalFinalSize,
        totalCompressionRatio,
        savedBytes: totalOriginalSize - totalFinalSize
      }
    };
  }

  // Кэширование результатов анализа
  async cacheAnalysisResult(imageUri, analysisResult) {
    try {
      const cacheKey = this.generateCacheKey(imageUri);
      const cacheData = {
        timestamp: Date.now(),
        imageUri,
        result: analysisResult
      };

      const existingCache = await this.getCache();
      existingCache[cacheKey] = cacheData;

      // Проверяем размер кэша и очищаем при необходимости
      await this.cleanupCache(existingCache);
      
      await AsyncStorage.setItem(this.CACHE_KEY, JSON.stringify(existingCache));
      console.log('💾 Результат анализа закэширован:', cacheKey);
    } catch (error) {
      console.error('❌ Ошибка кэширования:', error);
    }
  }

  // Получение закэшированного результата
  async getCachedAnalysisResult(imageUri) {
    try {
      const cacheKey = this.generateCacheKey(imageUri);
      const cache = await this.getCache();
      
      const cachedData = cache[cacheKey];
      if (cachedData) {
        // Проверяем возраст кэша (24 часа)
        const maxAge = 24 * 60 * 60 * 1000;
        if (Date.now() - cachedData.timestamp < maxAge) {
          console.log('🎯 Найден кэшированный результат:', cacheKey);
          return cachedData.result;
        } else {
          console.log('⏰ Кэшированный результат устарел:', cacheKey);
          delete cache[cacheKey];
          await AsyncStorage.setItem(this.CACHE_KEY, JSON.stringify(cache));
        }
      }
      
      return null;
    } catch (error) {
      console.error('❌ Ошибка получения кэша:', error);
      return null;
    }
  }

  // Получение всего кэша
  async getCache() {
    try {
      const cacheJson = await AsyncStorage.getItem(this.CACHE_KEY);
      return cacheJson ? JSON.parse(cacheJson) : {};
    } catch (error) {
      console.error('❌ Ошибка чтения кэша:', error);
      return {};
    }
  }

  // Очистка кэша
  async cleanupCache(cache = null) {
    try {
      if (!cache) {
        cache = await this.getCache();
      }

      const entries = Object.entries(cache);
      let totalSize = JSON.stringify(cache).length;

      if (totalSize > this.CACHE_SIZE_LIMIT) {
        console.log('🧹 Превышен лимит кэша, начинаем очистку');
        
        // Сортируем по времени (старые сначала)
        entries.sort((a, b) => a[1].timestamp - b[1].timestamp);
        
        // Удаляем старые записи пока не достигнем лимита
        while (totalSize > this.CACHE_SIZE_LIMIT * 0.8 && entries.length > 0) {
          const [key] = entries.shift();
          delete cache[key];
          totalSize = JSON.stringify(cache).length;
        }

        await AsyncStorage.setItem(this.CACHE_KEY, JSON.stringify(cache));
        console.log('✅ Кэш очищен, новый размер:', totalSize);
      }
    } catch (error) {
      console.error('❌ Ошибка очистки кэша:', error);
    }
  }

  // Генерация ключа кэша
  generateCacheKey(imageUri) {
    // Простой хэш на основе URI
    let hash = 0;
    for (let i = 0; i < imageUri.length; i++) {
      const char = imageUri.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Конвертируем в 32-битное целое
    }
    return `cache_${Math.abs(hash)}`;
  }

  // Получение статистики производительности
  async getPerformanceStats() {
    try {
      const cache = await this.getCache();
      const cacheSize = JSON.stringify(cache).length;
      const cacheEntries = Object.keys(cache).length;

      return {
        cacheSize: cacheSize,
        cacheSizeMB: (cacheSize / (1024 * 1024)).toFixed(2),
        cacheEntries: cacheEntries,
        cacheSizeLimit: this.CACHE_SIZE_LIMIT,
        cacheLimitMB: (this.CACHE_SIZE_LIMIT / (1024 * 1024)).toFixed(2),
        cacheUsagePercent: ((cacheSize / this.CACHE_SIZE_LIMIT) * 100).toFixed(1)
      };
    } catch (error) {
      console.error('❌ Ошибка получения статистики:', error);
      return {
        cacheSize: 0,
        cacheSizeMB: '0.00',
        cacheEntries: 0,
        cacheSizeLimit: this.CACHE_SIZE_LIMIT,
        cacheLimitMB: (this.CACHE_SIZE_LIMIT / (1024 * 1024)).toFixed(2),
        cacheUsagePercent: '0.0'
      };
    }
  }

  // Очистка всего кэша
  async clearAllCache() {
    try {
      await AsyncStorage.removeItem(this.CACHE_KEY);
      console.log('🗑️ Весь кэш очищен');
      return true;
    } catch (error) {
      console.error('❌ Ошибка очистки кэша:', error);
      return false;
    }
  }
}

export default new PerformanceOptimizer();
