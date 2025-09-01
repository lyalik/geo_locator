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
    try {
      setLoading(true);
      
      // Загружаем реальные данные из глобальных хранилищ
      const batchResults = window.GLOBAL_BATCH_RESULTS || [];
      const singleResults = window.GLOBAL_SINGLE_RESULTS || [];
      
      // Преобразуем результаты загрузки в формат нарушений
      const realViolations = [...batchResults, ...singleResults].flatMap((result, index) => {
        if (result.violations && result.violations.length > 0) {
          return result.violations.map((violation, vIndex) => ({
            id: `real_${index}_${vIndex}`,
            category: violation.category || 'unknown_violation',
            confidence: violation.confidence || 0,
            lat: result.location?.coordinates?.latitude || result.location?.coordinates?.[0] || null,
            lon: result.location?.coordinates?.longitude || result.location?.coordinates?.[1] || null,
            address: result.location?.address?.formatted || result.location?.address || 'Адрес не определен',
            created_at: result.uploadTime || result.metadata?.timestamp || new Date().toISOString(),
            status: 'processed',
            image_path: result.image || result.image_path || '/uploads/default.jpg',
            violation_id: result.violation_id,
            source: violation.source || 'yolo',
            description: violation.description || '',
            severity: violation.severity || 'medium'
          }));
        }
        return [];
      });
      
      // Mock данные для демонстрации (если нет реальных)
      const mockViolations = realViolations.length === 0 ? [
        {
          id: 'mock_1',
          category: 'parking_violation',
          confidence: 0.94,
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
      ] : [];
      
      const allViolations = [...realViolations, ...mockViolations];
      setViolations(allViolations);
      
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
    // Обновляем глобальные хранилища
    if (!window.GLOBAL_SINGLE_RESULTS) window.GLOBAL_SINGLE_RESULTS = [];
    if (!window.GLOBAL_BATCH_RESULTS) window.GLOBAL_BATCH_RESULTS = [];
    
    // Добавляем результаты в соответствующее хранилище
    results.forEach(result => {
      if (results.length === 1) {
        window.GLOBAL_SINGLE_RESULTS.push(result);
      } else {
        window.GLOBAL_BATCH_RESULTS.push(result);
      }
    });
    
    // Перезагружаем данные для синхронизации
    loadViolations();
  };

  const formatCategory = (category) => {
    const categories = {
      illegal_construction: 'Незаконное строительство',
      unauthorized_signage: 'Несанкционированные вывески',
      blocked_entrance: 'Заблокированный вход',
      improper_waste_disposal: 'Неправильная утилизация отходов',
      unauthorized_modification: 'Несанкционированные изменения'
    };
    return categories[category] || category;
  };

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
          <Tab icon={<MapIcon />} label="Карта нарушений" />
          <Tab icon={<UploadIcon />} label="Загрузка одного фото" />
          <Tab icon={<UploadIcon />} label="Пакетная загрузка" />
          <Tab icon={<AnalyticsIcon />} label="Аналитика" />
          <Tab icon={<PropertyIcon />} label="Анализ недвижимости" />
          <Tab icon={<UrbanIcon />} label="Городской контекст" />
          <Tab icon={<SatelliteIcon />} label="Спутниковые снимки" />
          <Tab icon={<OCRIcon />} label="OCR Анализ" />
        </Tabs>
      </Paper>

      {/* Tab Panels */}
      <TabPanel value={activeTab} index={0}>
        <Paper sx={{ height: 600 }}>
          <InteractiveMap
            violations={violations}
            onViolationClick={handleViolationClick}
            height={600}
          />
        </Paper>
      </TabPanel>

      <TabPanel value={activeTab} index={1}>
        <ViolationUploader onUploadComplete={handleUploadComplete} />
      </TabPanel>

      <TabPanel value={activeTab} index={2}>
        <BatchViolationUploader onUploadComplete={handleUploadComplete} />
      </TabPanel>

      <TabPanel value={activeTab} index={3}>
        <AnalyticsDashboard violations={violations} />
      </TabPanel>

      <TabPanel value={activeTab} index={4}>
        <PropertyAnalyzer 
          coordinates={violations.length > 0 ? {
            lat: violations[0].location?.coordinates?.[0] || 55.7558,
            lon: violations[0].location?.coordinates?.[1] || 37.6176
          } : null}
          onPropertySelect={(property) => {
            console.log('Selected property:', property);
          }}
        />
      </TabPanel>

      <TabPanel value={activeTab} index={5}>
        <UrbanAnalyzer 
          coordinates={violations.length > 0 ? {
            lat: violations[0].location?.coordinates?.[0] || 55.7558,
            lon: violations[0].location?.coordinates?.[1] || 37.6176
          } : null}
          onLocationSelect={(location) => {
            console.log('Selected location:', location);
          }}
        />
      </TabPanel>

      <TabPanel value={activeTab} index={6}>
        <SatelliteAnalyzer 
          coordinates={violations.length > 0 ? {
            lat: violations[0].location?.coordinates?.[0] || 55.7558,
            lon: violations[0].location?.coordinates?.[1] || 37.6176
          } : null}
          onImageSelect={(image) => {
            console.log('Selected satellite image:', image);
          }}
        />
      </TabPanel>

      <TabPanel value={activeTab} index={7}>
        <OCRAnalyzer />
      </TabPanel>

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
                  <strong>Адрес:</strong> {selectedViolation.address}
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
