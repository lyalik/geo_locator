import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  Alert,
  RefreshControl,
  Image,
  ActivityIndicator
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import ApiService from '../services/ApiService';

export default function HistoryScreen() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      setLoading(true);
      const response = await ApiService.getUserHistory();
      
      if (response.success && response.data) {
        // Сортируем по дате создания (новые сначала)
        const sortedHistory = response.data.sort((a, b) => 
          new Date(b.created_at) - new Date(a.created_at)
        );
        setHistory(sortedHistory);
      }
    } catch (error) {
      console.error('Ошибка загрузки истории:', error);
      Alert.alert('Ошибка', 'Не удалось загрузить историю');
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadHistory();
    setRefreshing(false);
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Дата неизвестна';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('ru-RU', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return 'Дата неизвестна';
    }
  };

  const getCategoryName = (category) => {
    const categoryMap = {
      'illegal_parking': 'Неправильная парковка',
      'garbage': 'Мусор',
      'road_damage': 'Повреждение дороги',
      'illegal_construction': 'Незаконная стройка',
      'broken_lighting': 'Сломанное освещение',
      'damaged_playground': 'Поврежденная площадка',
      'illegal_advertising': 'Незаконная реклама',
      'broken_pavement': 'Разбитый тротуар',
    };
    return categoryMap[category] || category || 'Нарушение';
  };

  const getCategoryIcon = (category) => {
    const iconMap = {
      'illegal_parking': 'car',
      'garbage': 'trash',
      'road_damage': 'construct',
      'illegal_construction': 'business',
      'broken_lighting': 'bulb',
      'damaged_playground': 'fitness',
      'illegal_advertising': 'megaphone',
      'broken_pavement': 'walk',
    };
    return iconMap[category] || 'alert-circle';
  };

  const getStatusColor = (confidence) => {
    if (!confidence) return '#666';
    if (confidence > 0.8) return '#4caf50'; // Зеленый - высокая уверенность
    if (confidence > 0.6) return '#ff9800'; // Оранжевый - средняя уверенность
    return '#f44336'; // Красный - низкая уверенность
  };

  const renderHistoryItem = ({ item }) => (
    <TouchableOpacity 
      style={styles.historyItem}
      onPress={() => {
        Alert.alert(
          'Детали нарушения',
          `Категория: ${getCategoryName(item.category)}\n` +
          `Дата: ${formatDate(item.created_at)}\n` +
          `Уверенность: ${item.confidence ? Math.round(item.confidence * 100) + '%' : 'Неизвестно'}\n` +
          `Координаты: ${item.latitude?.toFixed(6) || 'Неизвестно'}, ${item.longitude?.toFixed(6) || 'Неизвестно'}`
        );
      }}
    >
      <View style={styles.itemHeader}>
        <View style={styles.iconContainer}>
          <Ionicons 
            name={getCategoryIcon(item.category)} 
            size={24} 
            color="#2196F3" 
          />
        </View>
        
        <View style={styles.itemInfo}>
          <Text style={styles.categoryText}>
            {getCategoryName(item.category)}
          </Text>
          <Text style={styles.dateText}>
            {formatDate(item.created_at)}
          </Text>
          {item.address && (
            <Text style={styles.addressText} numberOfLines={1}>
              📍 {item.address}
            </Text>
          )}
        </View>

        <View style={styles.statusContainer}>
          {item.confidence && (
            <View style={[
              styles.confidenceBadge,
              { backgroundColor: getStatusColor(item.confidence) }
            ]}>
              <Text style={styles.confidenceText}>
                {Math.round(item.confidence * 100)}%
              </Text>
            </View>
          )}
          <Ionicons name="chevron-forward" size={20} color="#ccc" />
        </View>
      </View>

      {item.source && (
        <View style={styles.sourceContainer}>
          <Text style={styles.sourceText}>
            🤖 Обнаружено: {item.source}
          </Text>
        </View>
      )}
    </TouchableOpacity>
  );

  const renderEmptyState = () => (
    <View style={styles.emptyContainer}>
      <Ionicons name="document-text-outline" size={80} color="#ccc" />
      <Text style={styles.emptyTitle}>История пуста</Text>
      <Text style={styles.emptyText}>
        Сделайте фото нарушения в разделе "Камера", чтобы увидеть историю здесь
      </Text>
    </View>
  );

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#2196F3" />
        <Text style={styles.loadingText}>Загрузка истории...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Мои отчеты</Text>
        <Text style={styles.headerSubtitle}>
          Всего записей: {history.length}
        </Text>
      </View>

      <FlatList
        data={history}
        renderItem={renderHistoryItem}
        keyExtractor={(item, index) => `history-${item.id || index}`}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            colors={['#2196F3']}
          />
        }
        ListEmptyComponent={renderEmptyState}
        contentContainerStyle={history.length === 0 ? styles.emptyList : null}
        showsVerticalScrollIndicator={false}
      />

      {history.length > 0 && (
        <View style={styles.footer}>
          <TouchableOpacity 
            style={styles.exportButton}
            onPress={() => {
              Alert.alert(
                'Экспорт данных',
                'Функция экспорта в PDF будет добавлена в следующей версии',
                [{ text: 'OK', style: 'default' }]
              );
            }}
          >
            <Ionicons name="download" size={20} color="white" />
            <Text style={styles.exportButtonText}>Экспорт в PDF</Text>
          </TouchableOpacity>
        </View>
      )}
    </View>
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
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  historyItem: {
    backgroundColor: 'white',
    marginHorizontal: 15,
    marginVertical: 5,
    borderRadius: 10,
    padding: 15,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  itemHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  iconContainer: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#e3f2fd',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 15,
  },
  itemInfo: {
    flex: 1,
  },
  categoryText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },
  dateText: {
    fontSize: 12,
    color: '#666',
    marginBottom: 2,
  },
  addressText: {
    fontSize: 12,
    color: '#2196F3',
  },
  statusContainer: {
    alignItems: 'center',
  },
  confidenceBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    marginBottom: 5,
  },
  confidenceText: {
    fontSize: 12,
    color: 'white',
    fontWeight: 'bold',
  },
  sourceContainer: {
    marginTop: 10,
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
  },
  sourceText: {
    fontSize: 12,
    color: '#666',
    fontStyle: 'italic',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  emptyList: {
    flex: 1,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#666',
    marginTop: 20,
    marginBottom: 10,
  },
  emptyText: {
    fontSize: 14,
    color: '#999',
    textAlign: 'center',
    lineHeight: 20,
  },
  footer: {
    padding: 20,
    backgroundColor: 'white',
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
  },
  exportButton: {
    backgroundColor: '#2196F3',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 15,
    borderRadius: 10,
  },
  exportButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
    marginLeft: 10,
  },
});
