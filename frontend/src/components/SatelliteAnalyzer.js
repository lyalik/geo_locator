import React, { useState, useEffect } from 'react';
import {
  Box, Card, CardContent, Typography, Button, TextField, Grid,
  Tab, Tabs, Alert, CircularProgress, Dialog, DialogTitle,
  DialogContent, DialogActions, FormControl, InputLabel, Select,
  MenuItem, Chip, Paper, List, ListItem, ListItemText, Divider,
  LinearProgress, Switch, FormControlLabel
} from '@mui/material';
import {
  Satellite as SatelliteIcon, Timeline as TimelineIcon,
  Compare as CompareIcon, CloudDownload as DownloadIcon,
  Refresh as RefreshIcon, Settings as SettingsIcon,
  Visibility as ViewIcon, Analytics as AnalyticsIcon
} from '@mui/icons-material';
import { api } from '../services/api';

const SatelliteAnalyzer = ({ coordinates, onImageSelect }) => {
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Satellite image data
  const [satelliteImage, setSatelliteImage] = useState(null);
  const [imageAnalysis, setImageAnalysis] = useState(null);
  const [timeSeriesData, setTimeSeriesData] = useState([]);
  const [changeDetection, setChangeDetection] = useState(null);
  
  // Form states
  const [searchParams, setSearchParams] = useState({
    bbox: '',
    dateFrom: '',
    dateTo: '',
    resolution: 10,
    maxCloudCoverage: 20,
    bands: 'B02,B03,B04,B08'
  });
  
  const [timeSeriesParams, setTimeSeriesParams] = useState({
    startDate: '',
    endDate: '',
    intervalDays: 30
  });
  
  const [changeParams, setChangeParams] = useState({
    beforeDate: '',
    afterDate: ''
  });
  
  // Configuration
  const [showConfigDialog, setShowConfigDialog] = useState(false);
  const [credentials, setCredentials] = useState({
    clientId: '',
    clientSecret: ''
  });
  const [credentialsConfigured, setCredentialsConfigured] = useState(false);
  
  // Initialize coordinates
  useEffect(() => {
    if (coordinates) {
      const bbox = `${coordinates.lon - 0.01},${coordinates.lat - 0.01},${coordinates.lon + 0.01},${coordinates.lat + 0.01}`;
      setSearchParams(prev => ({ ...prev, bbox }));
    }
  }, [coordinates]);
  
  // Set default dates
  useEffect(() => {
    const today = new Date();
    const monthAgo = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000);
    const yearAgo = new Date(today.getTime() - 365 * 24 * 60 * 60 * 1000);
    
    setSearchParams(prev => ({
      ...prev,
      dateTo: today.toISOString().split('T')[0],
      dateFrom: monthAgo.toISOString().split('T')[0]
    }));
    
    setTimeSeriesParams(prev => ({
      ...prev,
      endDate: today.toISOString().split('T')[0],
      startDate: yearAgo.toISOString().split('T')[0]
    }));
    
    setChangeParams(prev => ({
      ...prev,
      afterDate: today.toISOString().split('T')[0],
      beforeDate: yearAgo.toISOString().split('T')[0]
    }));
  }, []);
  
  // Check service health
  useEffect(() => {
    checkServiceHealth();
  }, []);
  
  const checkServiceHealth = async () => {
    try {
      const response = await api.get('/api/sentinel/health');
      if (response.data.success) {
        setCredentialsConfigured(response.data.credentials_configured);
      }
    } catch (error) {
      console.error('Error checking service health:', error);
    }
  };
  
  const handleConfigureCredentials = async () => {
    try {
      setLoading(true);
      const response = await api.post('/api/sentinel/configure', credentials);
      
      if (response.data.success) {
        setCredentialsConfigured(true);
        setShowConfigDialog(false);
        setError(null);
      }
    } catch (error) {
      setError('Ошибка настройки учетных данных');
      console.error('Error configuring credentials:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const handleGetSatelliteImage = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const params = new URLSearchParams({
        bbox: searchParams.bbox,
        date_from: searchParams.dateFrom,
        date_to: searchParams.dateTo,
        resolution: searchParams.resolution,
        max_cloud_coverage: searchParams.maxCloudCoverage,
        bands: searchParams.bands
      });
      
      const response = await api.get(`/api/sentinel/satellite-image?${params}`);
      
      if (response.data.success) {
        setSatelliteImage(response.data.data);
        if (onImageSelect) {
          onImageSelect(response.data.data);
        }
      } else {
        setError(response.data.error || 'Не удалось получить спутниковый снимок');
      }
    } catch (error) {
      setError('Ошибка получения спутникового снимка');
      console.error('Error getting satellite image:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const handleAnalyzeImage = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const params = new URLSearchParams({
        bbox: searchParams.bbox,
        date_from: searchParams.dateFrom,
        date_to: searchParams.dateTo
      });
      
      const response = await api.get(`/api/sentinel/image-analysis?${params}`);
      
      if (response.data.success) {
        setImageAnalysis(response.data.data);
      } else {
        setError(response.data.error || 'Не удалось проанализировать изображение');
      }
    } catch (error) {
      setError('Ошибка анализа изображения');
      console.error('Error analyzing image:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const handleGetTimeSeries = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const params = new URLSearchParams({
        bbox: searchParams.bbox,
        start_date: timeSeriesParams.startDate,
        end_date: timeSeriesParams.endDate,
        interval_days: timeSeriesParams.intervalDays
      });
      
      const response = await api.get(`/api/sentinel/time-series?${params}`);
      
      if (response.data.success) {
        setTimeSeriesData(response.data.data);
      } else {
        setError(response.data.error || 'Не удалось получить временной ряд');
      }
    } catch (error) {
      setError('Ошибка получения временного ряда');
      console.error('Error getting time series:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const handleDetectChanges = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const params = new URLSearchParams({
        bbox: searchParams.bbox,
        before_date: changeParams.beforeDate,
        after_date: changeParams.afterDate
      });
      
      const response = await api.get(`/api/sentinel/change-detection?${params}`);
      
      if (response.data.success) {
        setChangeDetection(response.data.data);
      } else {
        setError(response.data.error || 'Не удалось выполнить детекцию изменений');
      }
    } catch (error) {
      setError('Ошибка детекции изменений');
      console.error('Error detecting changes:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const renderSatelliteImageTab = () => (
    <Box>
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Параметры поиска
              </Typography>
              
              <TextField
                fullWidth
                label="Область (bbox)"
                value={searchParams.bbox}
                onChange={(e) => setSearchParams(prev => ({ ...prev, bbox: e.target.value }))}
                margin="normal"
                placeholder="lon_min,lat_min,lon_max,lat_max"
              />
              
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    type="date"
                    label="Дата начала"
                    value={searchParams.dateFrom}
                    onChange={(e) => setSearchParams(prev => ({ ...prev, dateFrom: e.target.value }))}
                    margin="normal"
                    InputLabelProps={{ shrink: true }}
                  />
                </Grid>
                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    type="date"
                    label="Дата окончания"
                    value={searchParams.dateTo}
                    onChange={(e) => setSearchParams(prev => ({ ...prev, dateTo: e.target.value }))}
                    margin="normal"
                    InputLabelProps={{ shrink: true }}
                  />
                </Grid>
              </Grid>
              
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <FormControl fullWidth margin="normal">
                    <InputLabel>Разрешение (м)</InputLabel>
                    <Select
                      value={searchParams.resolution}
                      onChange={(e) => setSearchParams(prev => ({ ...prev, resolution: e.target.value }))}
                    >
                      <MenuItem value={10}>10м</MenuItem>
                      <MenuItem value={20}>20м</MenuItem>
                      <MenuItem value={60}>60м</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Макс. облачность (%)"
                    value={searchParams.maxCloudCoverage}
                    onChange={(e) => setSearchParams(prev => ({ ...prev, maxCloudCoverage: parseFloat(e.target.value) }))}
                    margin="normal"
                    inputProps={{ min: 0, max: 100 }}
                  />
                </Grid>
              </Grid>
              
              <TextField
                fullWidth
                label="Спектральные каналы"
                value={searchParams.bands}
                onChange={(e) => setSearchParams(prev => ({ ...prev, bands: e.target.value }))}
                margin="normal"
                placeholder="B02,B03,B04,B08"
              />
              
              <Box sx={{ mt: 2 }}>
                <Button
                  variant="contained"
                  onClick={handleGetSatelliteImage}
                  disabled={loading || !credentialsConfigured}
                  startIcon={<SatelliteIcon />}
                  fullWidth
                >
                  Получить снимок
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          {satelliteImage && (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Спутниковый снимок
                </Typography>
                
                <Box sx={{ mb: 2 }}>
                  <img
                    src={satelliteImage.image_url}
                    alt="Satellite"
                    style={{ width: '100%', maxHeight: '300px', objectFit: 'contain' }}
                  />
                </Box>
                
                <Typography variant="body2" color="text.secondary">
                  Дата съемки: {satelliteImage.acquisition_date}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Облачность: {satelliteImage.cloud_coverage}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Разрешение: {satelliteImage.resolution}м
                </Typography>
                
                <Box sx={{ mt: 2 }}>
                  <Chip label={`Каналы: ${satelliteImage.bands.join(', ')}`} size="small" />
                </Box>
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>
    </Box>
  );
  
  const renderAnalysisTab = () => (
    <Box>
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Анализ изображения
              </Typography>
              
              <Button
                variant="contained"
                onClick={handleAnalyzeImage}
                disabled={loading || !credentialsConfigured}
                startIcon={<AnalyticsIcon />}
                fullWidth
              >
                Анализировать
              </Button>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          {imageAnalysis && (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Результаты анализа
                </Typography>
                
                <List>
                  <ListItem>
                    <ListItemText
                      primary="Индекс растительности (NDVI)"
                      secondary={
                        <Box>
                          <LinearProgress
                            variant="determinate"
                            value={imageAnalysis.vegetation_index * 100}
                            sx={{ mt: 1 }}
                          />
                          <Typography variant="body2">
                            {(imageAnalysis.vegetation_index * 100).toFixed(1)}%
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItem>
                  <Divider />
                  
                  <ListItem>
                    <ListItemText
                      primary="Застроенная территория"
                      secondary={
                        <Box>
                          <LinearProgress
                            variant="determinate"
                            value={imageAnalysis.built_up_area * 100}
                            sx={{ mt: 1 }}
                          />
                          <Typography variant="body2">
                            {(imageAnalysis.built_up_area * 100).toFixed(1)}%
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItem>
                  <Divider />
                  
                  <ListItem>
                    <ListItemText
                      primary="Водные объекты"
                      secondary={
                        <Box>
                          <LinearProgress
                            variant="determinate"
                            value={imageAnalysis.water_bodies * 100}
                            sx={{ mt: 1 }}
                          />
                          <Typography variant="body2">
                            {(imageAnalysis.water_bodies * 100).toFixed(1)}%
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItem>
                  <Divider />
                  
                  <ListItem>
                    <ListItemText
                      primary="Открытая почва"
                      secondary={
                        <Box>
                          <LinearProgress
                            variant="determinate"
                            value={imageAnalysis.bare_soil * 100}
                            sx={{ mt: 1 }}
                          />
                          <Typography variant="body2">
                            {(imageAnalysis.bare_soil * 100).toFixed(1)}%
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>
    </Box>
  );
  
  const renderTimeSeriesTab = () => (
    <Box>
      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Временной ряд
              </Typography>
              
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    type="date"
                    label="Начальная дата"
                    value={timeSeriesParams.startDate}
                    onChange={(e) => setTimeSeriesParams(prev => ({ ...prev, startDate: e.target.value }))}
                    margin="normal"
                    InputLabelProps={{ shrink: true }}
                  />
                </Grid>
                <Grid item xs={6}>
                  <TextField
                    fullWidth
                    type="date"
                    label="Конечная дата"
                    value={timeSeriesParams.endDate}
                    onChange={(e) => setTimeSeriesParams(prev => ({ ...prev, endDate: e.target.value }))}
                    margin="normal"
                    InputLabelProps={{ shrink: true }}
                  />
                </Grid>
              </Grid>
              
              <TextField
                fullWidth
                type="number"
                label="Интервал (дни)"
                value={timeSeriesParams.intervalDays}
                onChange={(e) => setTimeSeriesParams(prev => ({ ...prev, intervalDays: parseInt(e.target.value) }))}
                margin="normal"
                inputProps={{ min: 1, max: 365 }}
              />
              
              <Button
                variant="contained"
                onClick={handleGetTimeSeries}
                disabled={loading || !credentialsConfigured}
                startIcon={<TimelineIcon />}
                fullWidth
                sx={{ mt: 2 }}
              >
                Получить временной ряд
              </Button>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={8}>
          {timeSeriesData.time_series && timeSeriesData.time_series.length > 0 && (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Результаты временного ряда
                </Typography>
                
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Всего периодов: {timeSeriesData.summary.total_periods}
                </Typography>
                
                <Grid container spacing={2}>
                  <Grid item xs={4}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="h6">
                        {(timeSeriesData.summary.avg_vegetation * 100).toFixed(1)}%
                      </Typography>
                      <Typography variant="body2">
                        Средняя растительность
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={4}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="h6">
                        {(timeSeriesData.summary.avg_built_up * 100).toFixed(1)}%
                      </Typography>
                      <Typography variant="body2">
                        Средняя застройка
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={4}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="h6">
                        {timeSeriesData.summary.avg_cloud_coverage.toFixed(1)}%
                      </Typography>
                      <Typography variant="body2">
                        Средняя облачность
                      </Typography>
                    </Paper>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>
    </Box>
  );
  
  const renderChangeDetectionTab = () => (
    <Box>
      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Детекция изменений
              </Typography>
              
              <TextField
                fullWidth
                type="date"
                label="Дата до"
                value={changeParams.beforeDate}
                onChange={(e) => setChangeParams(prev => ({ ...prev, beforeDate: e.target.value }))}
                margin="normal"
                InputLabelProps={{ shrink: true }}
              />
              
              <TextField
                fullWidth
                type="date"
                label="Дата после"
                value={changeParams.afterDate}
                onChange={(e) => setChangeParams(prev => ({ ...prev, afterDate: e.target.value }))}
                margin="normal"
                InputLabelProps={{ shrink: true }}
              />
              
              <Button
                variant="contained"
                onClick={handleDetectChanges}
                disabled={loading || !credentialsConfigured}
                startIcon={<CompareIcon />}
                fullWidth
                sx={{ mt: 2 }}
              >
                Детектировать изменения
              </Button>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={8}>
          {changeDetection && (
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Обнаруженные изменения
                </Typography>
                
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Typography variant="subtitle2" gutterBottom>
                      До ({changeDetection.before_period.date})
                    </Typography>
                    <List dense>
                      <ListItem>
                        <ListItemText
                          primary="Растительность"
                          secondary={`${(changeDetection.before_period.vegetation_index * 100).toFixed(1)}%`}
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemText
                          primary="Застройка"
                          secondary={`${(changeDetection.before_period.built_up_area * 100).toFixed(1)}%`}
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemText
                          primary="Водные объекты"
                          secondary={`${(changeDetection.before_period.water_bodies * 100).toFixed(1)}%`}
                        />
                      </ListItem>
                    </List>
                  </Grid>
                  
                  <Grid item xs={6}>
                    <Typography variant="subtitle2" gutterBottom>
                      После ({changeDetection.after_period.date})
                    </Typography>
                    <List dense>
                      <ListItem>
                        <ListItemText
                          primary="Растительность"
                          secondary={`${(changeDetection.after_period.vegetation_index * 100).toFixed(1)}%`}
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemText
                          primary="Застройка"
                          secondary={`${(changeDetection.after_period.built_up_area * 100).toFixed(1)}%`}
                        />
                      </ListItem>
                      <ListItem>
                        <ListItemText
                          primary="Водные объекты"
                          secondary={`${(changeDetection.after_period.water_bodies * 100).toFixed(1)}%`}
                        />
                      </ListItem>
                    </List>
                  </Grid>
                </Grid>
                
                <Typography variant="h6" sx={{ mt: 2 }} gutterBottom>
                  Изменения
                </Typography>
                
                {Object.entries(changeDetection.changes).map(([key, change]) => (
                  <Box key={key} sx={{ mb: 1 }}>
                    <Typography variant="body2">
                      {key === 'vegetation' ? 'Растительность' : 
                       key === 'built_up' ? 'Застройка' : 'Водные объекты'}:
                      <Chip
                        label={`${change.percentage.toFixed(1)}% (${change.significance})`}
                        size="small"
                        color={
                          change.significance === 'increase' ? 'success' :
                          change.significance === 'decrease' ? 'error' : 'default'
                        }
                        sx={{ ml: 1 }}
                      />
                    </Typography>
                  </Box>
                ))}
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>
    </Box>
  );
  
  return (
    <Box>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}
      
      {!credentialsConfigured && (
        <Alert 
          severity="warning" 
          sx={{ mb: 2 }}
          action={
            <Button color="inherit" size="small" onClick={() => setShowConfigDialog(true)}>
              Настроить
            </Button>
          }
        >
          Необходимо настроить учетные данные Sentinel Hub
        </Alert>
      )}
      
      {loading && <LinearProgress sx={{ mb: 2 }} />}
      
      <Paper sx={{ mb: 2 }}>
        <Tabs
          value={activeTab}
          onChange={(e, newValue) => setActiveTab(newValue)}
          variant="fullWidth"
        >
          <Tab icon={<SatelliteIcon />} label="Спутниковые снимки" />
          <Tab icon={<AnalyticsIcon />} label="Анализ" />
          <Tab icon={<TimelineIcon />} label="Временной ряд" />
          <Tab icon={<CompareIcon />} label="Детекция изменений" />
        </Tabs>
      </Paper>
      
      {activeTab === 0 && renderSatelliteImageTab()}
      {activeTab === 1 && renderAnalysisTab()}
      {activeTab === 2 && renderTimeSeriesTab()}
      {activeTab === 3 && renderChangeDetectionTab()}
      
      {/* Configuration Dialog */}
      <Dialog open={showConfigDialog} onClose={() => setShowConfigDialog(false)}>
        <DialogTitle>Настройка Sentinel Hub</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Client ID"
            value={credentials.clientId}
            onChange={(e) => setCredentials(prev => ({ ...prev, clientId: e.target.value }))}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Client Secret"
            type="password"
            value={credentials.clientSecret}
            onChange={(e) => setCredentials(prev => ({ ...prev, clientSecret: e.target.value }))}
            margin="normal"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowConfigDialog(false)}>Отмена</Button>
          <Button onClick={handleConfigureCredentials} disabled={loading}>
            Сохранить
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default SatelliteAnalyzer;
