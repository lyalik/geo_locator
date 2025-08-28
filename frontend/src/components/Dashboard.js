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
      // Mock data for now - replace with actual API call
      const mockViolations = [
        {
          id: 1,
          category: 'illegal_construction',
          confidence: 0.85,
          lat: 55.7558,
          lon: 37.6176,
          address: 'Красная площадь, 1, Москва',
          created_at: '2024-01-15T10:30:00Z',
          status: 'processed',
          image_path: '/uploads/violation1.jpg'
        },
        {
          id: 2,
          category: 'unauthorized_signage',
          confidence: 0.92,
          lat: 55.7500,
          lon: 37.6200,
          address: 'Тверская улица, 15, Москва',
          created_at: '2024-01-14T15:45:00Z',
          status: 'processed',
          image_path: '/uploads/violation2.jpg'
        },
        {
          id: 3,
          category: 'blocked_entrance',
          confidence: 0.78,
          lat: 55.7600,
          lon: 37.6100,
          address: 'Арбат, 25, Москва',
          created_at: '2024-01-13T09:15:00Z',
          status: 'pending',
          image_path: '/uploads/violation3.jpg'
        }
      ];
      
      setViolations(mockViolations);
      
      // Calculate stats
      const newStats = {
        total: mockViolations.length,
        pending: mockViolations.filter(v => v.status === 'pending').length,
        processed: mockViolations.filter(v => v.status === 'processed').length,
        errors: mockViolations.filter(v => v.status === 'error').length
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
    // Add new violations to the list
    const newViolations = results.map((result, index) => ({
      id: violations.length + index + 1,
      ...result.data,
      created_at: new Date().toISOString(),
      status: 'processed'
    }));
    
    setViolations(prev => [...prev, ...newViolations]);
    loadViolations(); // Refresh stats
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
