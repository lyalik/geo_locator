import React, { useState, useEffect } from 'react';
import {
  Box, Grid, Card, CardContent, Typography, Button, Tab, Tabs,
  Chip, CircularProgress, Paper, Dialog, DialogTitle, DialogContent, DialogActions
} from '@mui/material';
import {
  Map as MapIcon, Upload as UploadIcon, Analytics as AnalyticsIcon,
  Warning as WarningIcon, CheckCircle as CheckIcon, Schedule as ScheduleIcon,
  GetApp as DownloadIcon, Refresh as RefreshIcon,
  Home as PropertyIcon, LocationCity as UrbanIcon, Satellite as SatelliteIcon,
  TextFields as OCRIcon
} from '@mui/icons-material';
import InteractiveMap from './InteractiveMap';
import ViolationUploader from './ViolationUploader';
import AnalyticsDashboard from './AnalyticsDashboard';
import PropertyAnalyzer from './PropertyAnalyzer';
import UrbanAnalyzer from './UrbanAnalyzer';
import SatelliteAnalyzer from './SatelliteAnalyzer';
import OCRAnalyzer from './OCRAnalyzer';
import { violations } from '../services/api';

const Dashboard = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [violationsData, setViolationsData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedViolation, setSelectedViolation] = useState(null);
  const [showViolationDialog, setShowViolationDialog] = useState(false);
  const [stats, setStats] = useState({
    total: 0,
    pending: 0,
    processed: 0,
    errors: 0,
    withCoordinates: 0,
    withoutCoordinates: 0
  });
  const [selectedCoordinates, setSelectedCoordinates] = useState(null);

  useEffect(() => {
    loadViolations();
  }, []);

  const loadViolations = async () => {
    setLoading(true);
    try {
      // Загружаем данные из базы данных через API
      console.log('🔄 Loading violations from database...');
      const response = await violations.getList();
      
      let dbViolations = [];
      let allDbViolations = [];
      
      if (response.data) {
        // API возвращает данные напрямую в response.data
        const rawViolations = Array.isArray(response.data) ? response.data : (response.data.data || []);
        console.log('✅ Loaded violations from database:', rawViolations.length);
        
        // Нормализуем данные из базы данных для отображения
        allDbViolations = rawViolations.map(result => ({
          id: result.violation_id || Math.random().toString(),
          category: result.violations?.[0]?.category || 'unknown',
          confidence: result.violations?.[0]?.confidence || 0,
          lat: result.location?.coordinates?.latitude,
          lon: result.location?.coordinates?.longitude,
          address: result.location?.address?.formatted || result.location?.address || 'Адрес не указан',
          created_at: result.metadata?.timestamp || new Date().toISOString(),
          status: 'processed',
          image_path: result.image_path,
          source: result.violations?.[0]?.source || 'google_vision',
          description: result.violations?.[0]?.category || '',
          severity: 'medium',
          bbox: result.violations?.[0]?.bbox,
          has_coordinates: !!(result.location?.coordinates?.latitude && result.location?.coordinates?.longitude)
        }));
        
        // Для карты используем только нарушения с координатами
        dbViolations = allDbViolations.filter(v => v.has_coordinates);
        
        console.log('📍 Violations with coordinates:', dbViolations.length);
        console.log('📊 Total violations:', allDbViolations.length);
      } else {
        console.warn('⚠️ Failed to load violations from database:', response.data);
      }
      
      setViolationsData(dbViolations);
      
      // Calculate stats from ALL violations (not just those with coordinates)
      const withCoordinates = allDbViolations.filter(v => v.has_coordinates).length;
      const withoutCoordinates = allDbViolations.length - withCoordinates;
      
      const newStats = {
        total: allDbViolations.length,
        pending: allDbViolations.filter(v => v.status === 'pending').length,
        processed: allDbViolations.filter(v => v.status === 'processed').length,
        errors: allDbViolations.filter(v => v.status === 'error').length,
        withCoordinates: withCoordinates,
        withoutCoordinates: withoutCoordinates
      };
      setStats(newStats);
      
      console.log('📊 Статистика нарушений:', {
        'Всего': newStats.total,
        'Обработано': newStats.processed,
        'В ожидании': newStats.pending,
        'Ошибки': newStats.errors,
        'С координатами': newStats.withCoordinates,
        'Без координат': newStats.withoutCoordinates
      });
      
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
    
    // Сохраняем данные в localStorage для персистентности
    try {
      const globalData = {
        single: window.GLOBAL_SINGLE_RESULTS,
        batch: window.GLOBAL_BATCH_RESULTS,
        timestamp: Date.now()
      };
      localStorage.setItem('geo_locator_violations', JSON.stringify(globalData));
    } catch (error) {
      console.warn('Failed to save violations to localStorage:', error);
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
    
    // Данные автоматически сохраняются в базу данных через API
    console.log('💾 New violation automatically saved to database via API');
    
    // Обновляем данные из базы данных
    setTimeout(() => {
      loadViolations();
    }, 1000);
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
    { label: 'Карта нарушений', icon: <MapIcon />, component: <InteractiveMap violations={violationsData} onViolationClick={handleViolationClick} onCoordinateSelect={setSelectedCoordinates} height={600} /> },
    { label: 'Анализ с ИИ', icon: <UploadIcon />, component: <ViolationUploader onUploadComplete={handleUploadComplete} /> },
    { label: 'Аналитика', icon: <AnalyticsIcon />, component: <AnalyticsDashboard violations={violationsData} /> },
    { label: 'Анализ недвижимости', icon: <PropertyIcon />, component: <PropertyAnalyzer coordinates={selectedCoordinates} onPropertySelect={(property) => { if (property.coordinates) setSelectedCoordinates({lat: property.coordinates[0], lon: property.coordinates[1]}); }} /> },
    { label: 'Городской контекст', icon: <UrbanIcon />, component: <UrbanAnalyzer coordinates={selectedCoordinates} /> },
    { label: 'Спутниковый анализ', icon: <SatelliteIcon />, component: <SatelliteAnalyzer coordinates={selectedCoordinates} /> },
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
