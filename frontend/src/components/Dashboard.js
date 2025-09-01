import React, { useState, useEffect } from 'react';
import {
  Box, Grid, Card, CardContent, Typography, Button, Tab, Tabs,
  Chip, Alert, CircularProgress, Paper, List, ListItem, ListItemText,
  ListItemIcon, IconButton, Dialog, DialogTitle, DialogContent, DialogActions
} from '@mui/material';
import {
  Map as MapIcon, Upload as UploadIcon, Analytics as AnalyticsIcon,
  Warning as WarningIcon, CheckCircle as CheckIcon, Schedule as ScheduleIcon,
  Visibility as ViewIcon, GetApp as DownloadIcon, Refresh as RefreshIcon,
  Home as PropertyIcon, LocationCity as UrbanIcon, Satellite as SatelliteIcon,
  TextFields as OCRIcon
} from '@mui/icons-material';
import InteractiveMap from './InteractiveMap';
import BatchViolationUploader from './BatchViolationUploader';
import ViolationUploader from './ViolationUploader';
import AnalyticsDashboard from './AnalyticsDashboard';
import PropertyAnalyzer from './PropertyAnalyzer';
import UrbanAnalyzer from './UrbanAnalyzer';
import SatelliteAnalyzer from './SatelliteAnalyzer';
import OCRAnalyzer from './OCRAnalyzer';
import MistralAnalyzer from './MistralAnalyzer';
import { api } from '../services/api';

const Dashboard = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [violations, setViolations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedViolation, setSelectedViolation] = useState(null);
  const [showViolationDialog, setShowViolationDialog] = useState(false);
  const [stats, setStats] = useState({
    total: 0,
    pending: 0,
    processed: 0,
    errors: 0
  });

  useEffect(() => {
    loadViolations();
  }, []);

  const loadViolations = async () => {
    setLoading(true);
    try {
      // Загружаем данные из localStorage
      const savedViolations = localStorage.getItem('geo_locator_violations');
      let persistedViolations = [];
      
      if (savedViolations) {
        try {
          persistedViolations = JSON.parse(savedViolations);
          console.log('Loaded violations from localStorage:', persistedViolations.length);
        } catch (e) {
          console.error('Error parsing saved violations:', e);
          localStorage.removeItem('geo_locator_violations');
        }
      }
      
      // Загружаем данные из глобальных переменных
      const batchResults = window.GLOBAL_BATCH_RESULTS || [];
      const singleResults = window.GLOBAL_SINGLE_RESULTS || [];
      
      // Объединяем все результаты
      const allGlobalResults = [...batchResults, ...singleResults];
      
      // Нормализуем данные для отображения
      const realViolations = allGlobalResults.map(result => ({
        id: result.violation_id || result.id || Math.random().toString(),
        category: result.category || 'unknown',
        confidence: result.confidence || 0,
        lat: result.location?.coordinates?.latitude || result.lat,
        lon: result.location?.coordinates?.longitude || result.lon,
        address: result.location?.address?.formatted || result.location?.address || result.address,
        created_at: result.uploadTime || result.created_at || new Date().toISOString(),
        status: result.status || 'processed',
        image_path: result.image || result.annotated_image_path || result.image_path,
        source: result.source || 'api',
        description: result.description || '',
        severity: result.severity || 'medium'
      }));
      
      // Объединяем сохраненные и новые данные, избегая дубликатов
      const allViolationsMap = new Map();
      
      // Добавляем сохраненные данные
      persistedViolations.forEach(v => allViolationsMap.set(v.id, v));
      
      // Добавляем новые данные (перезаписывают существующие с тем же ID)
      realViolations.forEach(v => allViolationsMap.set(v.id, v));
      
      // Добавляем mock данные только если нет других данных
      if (allViolationsMap.size === 0) {
        const mockViolations = [
          {
            id: 'mock_1',
            category: 'illegal_construction',
            confidence: 0.85,
            lat: 55.7558,
            lon: 37.6176,
            address: 'Красная площадь, 1, Москва',
            created_at: '2024-01-15T10:30:00Z',
            status: 'processed',
            image_path: '/uploads/violation1.jpg',
            source: 'mock',
            description: 'Нарушение парковки в неположенном месте',
            severity: 'high'
          },
          {
            id: 'mock_2',
            category: 'unauthorized_modification',
            confidence: 0.71,
            lat: 55.7500,
            lon: 37.6200,
            address: 'Тверская улица, 15, Москва',
            created_at: '2024-01-14T15:45:00Z',
            status: 'processed',
            image_path: '/uploads/violation2.jpg',
            source: 'mock',
            description: 'Несанкционированные изменения фасада',
            severity: 'medium'
          }
        ];
        mockViolations.forEach(v => allViolationsMap.set(v.id, v));
      }
      
      const allViolations = Array.from(allViolationsMap.values());
      setViolations(allViolations);
      
      // Сохраняем в localStorage
      localStorage.setItem('geo_locator_violations', JSON.stringify(allViolations));
      
      // Calculate stats from all violations
      const newStats = {
        total: allViolations.length,
        pending: allViolations.filter(v => v.status === 'pending').length,
        processed: allViolations.filter(v => v.status === 'processed').length,
        errors: allViolations.filter(v => v.status === 'error').length
      };
      setStats(newStats);
      
    } catch (error) {
      console.error('Error loading violations:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleViolationClick = (violation) => {
    setSelectedViolation(violation);
    setShowViolationDialog(true);
  };

  const handleUploadComplete = (results) => {
    console.log('Dashboard handleUploadComplete called with:', results);
    
    // Инициализируем глобальные хранилища если их нет
    if (!window.GLOBAL_SINGLE_RESULTS) {
      window.GLOBAL_SINGLE_RESULTS = [];
    }
    if (!window.GLOBAL_BATCH_RESULTS) {
      window.GLOBAL_BATCH_RESULTS = [];
    }

    // Обрабатываем как массив результатов, так и одиночный результат
    const resultsArray = Array.isArray(results) ? results : [results];
    
    resultsArray.forEach(result => {
      // Извлекаем нарушения из результата
      const resultViolations = result.violations || [];
      
      // Создаем отдельную запись для каждого нарушения
      if (resultViolations.length > 0) {
        resultViolations.forEach(violation => {
          const normalizedResult = {
            id: `${result.violation_id || result.id || Date.now()}_${violation.category || 'unknown'}`,
            category: violation.category || violation.type || 'unknown',
            confidence: violation.confidence || 0,
            lat: result.location?.coordinates?.latitude || result.lat,
            lon: result.location?.coordinates?.longitude || result.lon,
            address: result.location?.address?.formatted || result.location?.address || result.address,
            created_at: result.uploadTime || new Date().toISOString(),
            status: 'processed',
            image_path: result.image || result.annotated_image_path || result.image_path,
            source: violation.source || result.source || 'upload',
            description: violation.description || result.description || '',
            severity: violation.severity || result.severity || 'medium',
            violations: [violation],
            metadata: result.metadata || {},
            fileName: result.fileName
          };

          // Добавляем в оба глобальных хранилища
          window.GLOBAL_SINGLE_RESULTS.push(normalizedResult);
          window.GLOBAL_BATCH_RESULTS.push(normalizedResult);
          
          console.log('Added violation to global storage:', normalizedResult);
        });
      }
      // НЕ добавляем запись если нарушений не найдено
    });

    console.log('Global storage now has:', window.GLOBAL_SINGLE_RESULTS.length, 'results');
    
    // Сохраняем в localStorage сразу после добавления
    const currentSaved = localStorage.getItem('geo_locator_violations');
    let savedViolations = [];
    if (currentSaved) {
      try {
        savedViolations = JSON.parse(currentSaved);
      } catch (e) {
        console.error('Error parsing saved violations:', e);
      }
    }
    
    // Добавляем новые нарушения в сохраненные данные
    const allSavedMap = new Map();
    savedViolations.forEach(v => allSavedMap.set(v.id, v));
    
    // Добавляем новые данные из глобального хранилища
    [...window.GLOBAL_SINGLE_RESULTS, ...window.GLOBAL_BATCH_RESULTS].forEach(result => {
      if (result.id) {
        allSavedMap.set(result.id, result);
      }
    });
    
    const updatedViolations = Array.from(allSavedMap.values());
    localStorage.setItem('geo_locator_violations', JSON.stringify(updatedViolations));
    console.log('Saved to localStorage:', updatedViolations.length, 'violations');
    
    // Принудительно обновляем состояние
    setTimeout(() => {
      loadViolations();
    }, 100);
  };

  const formatCategory = (category) => {
    const categories = {
      illegal_construction: 'Незаконное строительство',
      unauthorized_signage: 'Несанкционированная реклама',
      blocked_entrance: 'Заблокированный вход',
      improper_waste_disposal: 'Неправильная утилизация отходов',
      unauthorized_modification: 'Несанкционированные изменения'
    };
    return categories[category] || category;
  };

  const tabs = [
    { label: 'Карта нарушений', icon: <MapIcon />, component: <InteractiveMap violations={violations} onViolationClick={handleViolationClick} height={600} /> },
    { label: 'Анализ с ИИ', icon: <UploadIcon />, component: <ViolationUploader onUploadComplete={handleUploadComplete} /> },
    { label: 'Аналитика', icon: <AnalyticsIcon />, component: <AnalyticsDashboard violations={violations} /> },
    { label: 'Анализ недвижимости', icon: <PropertyIcon />, component: <PropertyAnalyzer /> },
    { label: 'Городской контекст', icon: <UrbanIcon />, component: <UrbanAnalyzer /> },
    { label: 'Спутниковый анализ', icon: <SatelliteIcon />, component: <SatelliteAnalyzer /> },
    { label: 'OCR анализ', icon: <OCRIcon />, component: <OCRAnalyzer /> }
  ];

  const getStatusIcon = (status) => {
    switch (status) {
      case 'processed': return <CheckIcon color="success" />;
      case 'error': return <WarningIcon color="error" />;
      case 'pending': return <ScheduleIcon color="action" />;
      default: return <ScheduleIcon color="action" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'processed': return 'success';
      case 'error': return 'error';
      case 'pending': return 'warning';
      default: return 'default';
    }
  };

  const TabPanel = ({ children, value, index }) => (
    <div hidden={value !== index}>
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          Панель управления нарушениями
        </Typography>
        <Button
          startIcon={<RefreshIcon />}
          onClick={loadViolations}
          variant="outlined"
        >
          Обновить
        </Button>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Всего нарушений
              </Typography>
              <Typography variant="h4">
                {stats.total}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Обработано
              </Typography>
              <Typography variant="h4" color="success.main">
                {stats.processed}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                В ожидании
              </Typography>
              <Typography variant="h4" color="warning.main">
                {stats.pending}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Ошибки
              </Typography>
              <Typography variant="h4" color="error.main">
                {stats.errors}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={activeTab}
          onChange={(e, newValue) => setActiveTab(newValue)}
          variant="fullWidth"
        >
          {tabs.map((tab, index) => (
            <Tab key={index} icon={tab.icon} label={tab.label} />
          ))}
        </Tabs>
      </Paper>

      {/* Tab Panels */}
      {tabs.map((tab, index) => (
        <TabPanel key={index} value={activeTab} index={index}>
          <Box sx={{ height: '600px', width: '100%' }}>
            {tab.component}
          </Box>
        </TabPanel>
      ))}

      {/* Violation Detail Dialog */}
      <Dialog
        open={showViolationDialog}
        onClose={() => setShowViolationDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Детали нарушения
          {selectedViolation && (
            <Chip
              label={getStatusColor(selectedViolation.status)}
              color={getStatusColor(selectedViolation.status)}
              sx={{ ml: 2 }}
            />
          )}
        </DialogTitle>
        <DialogContent>
          {selectedViolation && (
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                {selectedViolation.image_path && (
                  <img
                    src={selectedViolation.image_path}
                    alt="Нарушение"
                    style={{ width: '100%', maxHeight: 300, objectFit: 'cover' }}
                  />
                )}
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom>
                  {formatCategory(selectedViolation.category)}
                </Typography>
                <Typography variant="body1" paragraph>
                  <strong>Адрес:</strong> {typeof selectedViolation.address === 'object' ? 
                    selectedViolation.address.formatted || JSON.stringify(selectedViolation.address) : 
                    selectedViolation.address}
                </Typography>
                <Typography variant="body1" paragraph>
                  <strong>Координаты:</strong> {selectedViolation.lat}, {selectedViolation.lon}
                </Typography>
                <Typography variant="body1" paragraph>
                  <strong>Уверенность:</strong> {(selectedViolation.confidence * 100).toFixed(1)}%
                </Typography>
                <Typography variant="body1" paragraph>
                  <strong>Дата:</strong> {new Date(selectedViolation.created_at).toLocaleString('ru-RU')}
                </Typography>
                <Typography variant="body1" paragraph>
                  <strong>Статус:</strong> 
                  <Chip
                    label={selectedViolation.status}
                    color={getStatusColor(selectedViolation.status)}
                    size="small"
                    sx={{ ml: 1 }}
                  />
                </Typography>
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowViolationDialog(false)}>
            Закрыть
          </Button>
          <Button startIcon={<DownloadIcon />} variant="outlined">
            Скачать отчет
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Dashboard;
