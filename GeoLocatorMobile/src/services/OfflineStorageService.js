import AsyncStorage from '@react-native-async-storage/async-storage';
import * as FileSystem from 'expo-file-system/legacy';
import * as Network from 'expo-network';

class OfflineStorageService {
  constructor() {
    this.OFFLINE_PHOTOS_KEY = 'offline_photos';
    this.PHOTOS_DIR = FileSystem.documentDirectory + 'offline_photos/';
  }

  // Инициализация директории для офлайн фото
  async initializeOfflineStorage() {
    try {
      const dirInfo = await FileSystem.getInfoAsync(this.PHOTOS_DIR);
      if (!dirInfo.exists) {
        await FileSystem.makeDirectoryAsync(this.PHOTOS_DIR, { intermediates: true });
        console.log('📁 Создана директория для офлайн фото:', this.PHOTOS_DIR);
      }
    } catch (error) {
      console.error('❌ Ошибка инициализации офлайн хранилища:', error);
    }
  }

  // Проверка состояния сети
  async isOnline() {
    try {
      const networkState = await Network.getNetworkStateAsync();
      return networkState.isConnected && networkState.isInternetReachable;
    } catch (error) {
      console.error('❌ Ошибка проверки сети:', error);
      return false;
    }
  }

  // Сохранение фото в офлайн режиме
  async savePhotoOffline(photoUri, location, metadata = {}) {
    try {
      const timestamp = Date.now();
      const fileName = `photo_${timestamp}.jpg`;
      const offlinePhotoPath = this.PHOTOS_DIR + fileName;

      // Копируем фото в постоянную директорию
      await FileSystem.copyAsync({
        from: photoUri,
        to: offlinePhotoPath
      });

      // Создаем объект с метаданными
      const offlinePhoto = {
        id: timestamp.toString(),
        localPath: offlinePhotoPath,
        originalUri: photoUri,
        location: location,
        timestamp: timestamp,
        uploaded: false,
        metadata: {
          ...metadata,
          savedOffline: true,
          deviceInfo: {
            platform: 'mobile',
            timestamp: new Date().toISOString()
          }
        }
      };

      // Сохраняем в список офлайн фото
      await this.addToOfflineList(offlinePhoto);

      console.log('💾 Фото сохранено офлайн:', fileName);
      return offlinePhoto;
    } catch (error) {
      console.error('❌ Ошибка сохранения фото офлайн:', error);
      throw error;
    }
  }

  // Добавление фото в список офлайн фото
  async addToOfflineList(photo) {
    try {
      const existingPhotos = await this.getOfflinePhotos();
      const updatedPhotos = [...existingPhotos, photo];
      await AsyncStorage.setItem(this.OFFLINE_PHOTOS_KEY, JSON.stringify(updatedPhotos));
    } catch (error) {
      console.error('❌ Ошибка добавления в офлайн список:', error);
      throw error;
    }
  }

  // Получение списка офлайн фото
  async getOfflinePhotos() {
    try {
      const photosJson = await AsyncStorage.getItem(this.OFFLINE_PHOTOS_KEY);
      return photosJson ? JSON.parse(photosJson) : [];
    } catch (error) {
      console.error('❌ Ошибка получения офлайн фото:', error);
      return [];
    }
  }

  // Получение количества неотправленных фото
  async getPendingPhotosCount() {
    try {
      const photos = await this.getOfflinePhotos();
      return photos.filter(photo => !photo.uploaded).length;
    } catch (error) {
      console.error('❌ Ошибка подсчета неотправленных фото:', error);
      return 0;
    }
  }

  // Синхронизация офлайн фото с сервером
  async syncOfflinePhotos(uploadFunction) {
    try {
      const isConnected = await this.isOnline();
      if (!isConnected) {
        console.log('📡 Нет подключения к интернету для синхронизации');
        return { success: false, message: 'Нет подключения к интернету' };
      }

      const offlinePhotos = await this.getOfflinePhotos();
      const pendingPhotos = offlinePhotos.filter(photo => !photo.uploaded);

      if (pendingPhotos.length === 0) {
        console.log('✅ Нет фото для синхронизации');
        return { success: true, message: 'Все фото уже синхронизированы', uploaded: 0 };
      }

      console.log(`🔄 Начинаем синхронизацию ${pendingPhotos.length} фото...`);

      let uploadedCount = 0;
      const errors = [];

      for (const photo of pendingPhotos) {
        try {
          // Проверяем, что файл еще существует
          const fileInfo = await FileSystem.getInfoAsync(photo.localPath);
          if (!fileInfo.exists) {
            console.warn(`⚠️ Файл не найден: ${photo.localPath}`);
            await this.markPhotoAsUploaded(photo.id);
            continue;
          }

          // Загружаем фото на сервер
          const result = await uploadFunction(photo);
          
          if (result.success) {
            await this.markPhotoAsUploaded(photo.id);
            uploadedCount++;
            console.log(`✅ Фото ${photo.id} успешно загружено`);
          } else {
            errors.push(`Ошибка загрузки ${photo.id}: ${result.error}`);
          }
        } catch (error) {
          console.error(`❌ Ошибка загрузки фото ${photo.id}:`, error);
          errors.push(`Ошибка загрузки ${photo.id}: ${error.message}`);
        }
      }

      const result = {
        success: uploadedCount > 0,
        uploaded: uploadedCount,
        total: pendingPhotos.length,
        errors: errors
      };

      if (uploadedCount > 0) {
        console.log(`✅ Синхронизация завершена: ${uploadedCount}/${pendingPhotos.length} фото загружено`);
      }

      return result;
    } catch (error) {
      console.error('❌ Ошибка синхронизации офлайн фото:', error);
      return { success: false, message: error.message };
    }
  }

  // Отметить фото как загруженное
  async markPhotoAsUploaded(photoId) {
    try {
      const photos = await this.getOfflinePhotos();
      const updatedPhotos = photos.map(photo => 
        photo.id === photoId ? { ...photo, uploaded: true, uploadedAt: Date.now() } : photo
      );
      await AsyncStorage.setItem(this.OFFLINE_PHOTOS_KEY, JSON.stringify(updatedPhotos));
    } catch (error) {
      console.error('❌ Ошибка отметки фото как загруженного:', error);
    }
  }

  // Очистка старых загруженных фото
  async cleanupUploadedPhotos(maxAge = 7 * 24 * 60 * 60 * 1000) { // 7 дней по умолчанию
    try {
      const photos = await this.getOfflinePhotos();
      const now = Date.now();
      const photosToKeep = [];
      const photosToDelete = [];

      for (const photo of photos) {
        if (photo.uploaded && photo.uploadedAt && (now - photo.uploadedAt) > maxAge) {
          photosToDelete.push(photo);
        } else {
          photosToKeep.push(photo);
        }
      }

      // Удаляем файлы
      for (const photo of photosToDelete) {
        try {
          const fileInfo = await FileSystem.getInfoAsync(photo.localPath);
          if (fileInfo.exists) {
            await FileSystem.deleteAsync(photo.localPath);
            console.log(`🗑️ Удален старый файл: ${photo.localPath}`);
          }
        } catch (error) {
          console.warn(`⚠️ Не удалось удалить файл ${photo.localPath}:`, error);
        }
      }

      // Обновляем список
      await AsyncStorage.setItem(this.OFFLINE_PHOTOS_KEY, JSON.stringify(photosToKeep));

      console.log(`🧹 Очистка завершена: удалено ${photosToDelete.length} старых фото`);
      return { deleted: photosToDelete.length, kept: photosToKeep.length };
    } catch (error) {
      console.error('❌ Ошибка очистки старых фото:', error);
      return { deleted: 0, kept: 0 };
    }
  }

  // Получение статистики офлайн хранилища
  async getStorageStats() {
    try {
      const photos = await this.getOfflinePhotos();
      const pending = photos.filter(photo => !photo.uploaded);
      const uploaded = photos.filter(photo => photo.uploaded);

      // Подсчет размера директории
      let totalSize = 0;
      try {
        const dirInfo = await FileSystem.readDirectoryAsync(this.PHOTOS_DIR);
        for (const fileName of dirInfo) {
          const filePath = this.PHOTOS_DIR + fileName;
          const fileInfo = await FileSystem.getInfoAsync(filePath);
          if (fileInfo.exists) {
            totalSize += fileInfo.size || 0;
          }
        }
      } catch (error) {
        console.warn('⚠️ Не удалось подсчитать размер директории:', error);
      }

      return {
        totalPhotos: photos.length,
        pendingPhotos: pending.length,
        uploadedPhotos: uploaded.length,
        totalSizeBytes: totalSize,
        totalSizeMB: (totalSize / (1024 * 1024)).toFixed(2),
        storageDir: this.PHOTOS_DIR
      };
    } catch (error) {
      console.error('❌ Ошибка получения статистики:', error);
      return {
        totalPhotos: 0,
        pendingPhotos: 0,
        uploadedPhotos: 0,
        totalSizeBytes: 0,
        totalSizeMB: '0.00',
        storageDir: this.PHOTOS_DIR
      };
    }
  }
}

export default new OfflineStorageService();
