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
    lat: '',
    lon: '',
    radius: 1000,
    dateFrom: '',
    dateTo: '',
    resolution: 10,
    maxCloudCoverage: 20,
    bands: 'RGB',
    source: 'auto'  // Добавляем выбор источника
  });
  
  const [timeSeriesParams, setTimeSeriesParams] = useState({
    startDate: '',
    endDate: '',
    intervalDays: 30,
    source: 'auto'  // Добавляем выбор источника для временного ряда
  });
  
  const [changeParams, setChangeParams] = useState({
    beforeDate: '',
    afterDate: '',
    source: 'auto'  // Добавляем выбор источника для детекции изменений
  });
  
  // Configuration
  const [showConfigDialog, setShowConfigDialog] = useState(false);
  const [zoomDialogOpen, setZoomDialogOpen] = useState(false);
  const [availableSources, setAvailableSources] = useState({
    roscosmos: true,
    yandex: true,
    dgis: true,
    osm: true,
    auto: true
  });
  const [selectedImage, setSelectedImage] = useState(null);
  const [credentials, setCredentials] = useState({
    clientId: '',
    clientSecret: ''
  });
  const [credentialsConfigured, setCredentialsConfigured] = useState(false);
  
  // Initialize coordinates
  useEffect(() => {
    if (coordinates) {
      setSearchParams(prev => ({ 
        ...prev, 
        lat: coordinates.lat.toString(),
        lon: coordinates.lon.toString()
      }));
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
      const response = await api.get('/api/satellite/health');
      if (response.data.success) {
        setCredentialsConfigured(true); // Российские сервисы всегда готовы
      }
    } catch (error) {
      console.error('Error checking service health:', error);
      setCredentialsConfigured(true); // Fallback - считаем готовыми
    }
  };
  
  const handleConfigureCredentials = async () => {
    // Российские сервисы не требуют дополнительной настройки
    setCredentialsConfigured(true);
    setShowConfigDialog(false);
    setError(null);
  };
  
  const handleGetSatelliteImage = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Создаем bbox из координат и радиуса
      const lat = parseFloat(searchParams.lat);
      const lon = parseFloat(searchParams.lon);
      const radiusKm = searchParams.radius / 1000;
      const latOffset = radiusKm / 111; // примерно 111 км на градус широты
      const lonOffset = radiusKm / (111 * Math.cos(lat * Math.PI / 180));
      
      const lon_min = lon - lonOffset;
      const lat_min = lat - latOffset;
      const lon_max = lon + lonOffset;
      const lat_max = lat + latOffset;
      
      const response = await api.get('/api/satellite/image', {
        params: {
          bbox: `${lon_min},${lat_min},${lon_max},${lat_max}`,
          date_from: searchParams.dateFrom,
          date_to: searchParams.dateTo,
          resolution: searchParams.resolution,
          max_cloud_coverage: searchParams.maxCloudCoverage,
          bands: searchParams.bands,
          source: searchParams.source  // Передаем выбранный источник
        }
      });
      
      if (response.data.success) {
        const imageData = {
          ...response.data.data,
          acquisition_date: response.data.data.acquisition_date || new Date().toISOString(),
          source: response.data.data.source || 'Роскосмос',
          resolution: response.data.data.resolution || searchParams.resolution,
          cloud_coverage: response.data.data.cloud_coverage || 0
        };
        
        setSatelliteImage(imageData);
        console.log('Satellite image retrieved:', imageData);
        
        if (onImageSelect) {
          onImageSelect(imageData);
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
      
      // Создаем bbox из координат и радиуса
      const lat = parseFloat(searchParams.lat);
      const lon = parseFloat(searchParams.lon);
      const radiusKm = searchParams.radius / 1000;
      const latOffset = radiusKm / 111;
      const lonOffset = radiusKm / (111 * Math.cos(lat * Math.PI / 180));
      
      const bbox = `${lon - lonOffset},${lat - latOffset},${lon + lonOffset},${lat + latOffset}`;
      
      const params = {
        bbox: bbox,
        date_from: searchParams.dateFrom,
        date_to: searchParams.dateTo,
        analysis_type: 'comprehensive'
      };
      
      const response = await api.get('/api/satellite/analyze', { params });
      
      console.log('Satellite analysis response:', response.data);
      
      if (response.data.success && response.data.analysis) {
        const analysisData = {
          ...response.data.analysis,
          analysis_timestamp: new Date().toISOString(),
          source: response.data.analysis.source || 'Роскосмос',
          bbox: bbox
        };
        
        setImageAnalysis(analysisData);
        console.log('Satellite analysis completed:', analysisData);
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
      
      // Создаем bbox из координат и радиуса
      const lat = parseFloat(searchParams.lat);
      const lon = parseFloat(searchParams.lon);
      const radiusKm = searchParams.radius / 1000;
      const latOffset = radiusKm / 111;
      const lonOffset = radiusKm / (111 * Math.cos(lat * Math.PI / 180));
      
      const lon_min = lon - lonOffset;
      const lat_min = lat - latOffset;
      const lon_max = lon + lonOffset;
      const lat_max = lat + latOffset;
      
      const response = await api.get('/api/satellite/time-series', {
        params: {
          bbox: `${lon_min},${lat_min},${lon_max},${lat_max}`,
          start_date: timeSeriesParams.startDate,
          end_date: timeSeriesParams.endDate,
          interval_days: timeSeriesParams.intervalDays,
          source: timeSeriesParams.source  // Передаем выбранный источник
        }
      });
      
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
      
      // Создаем bbox из координат и радиуса
      const lat = parseFloat(searchParams.lat);
      const lon = parseFloat(searchParams.lon);
      const radiusKm = searchParams.radius / 1000;
      const latOffset = radiusKm / 111;
      const lonOffset = radiusKm / (111 * Math.cos(lat * Math.PI / 180));
      
      const lon_min = lon - lonOffset;
      const lat_min = lat - latOffset;
      const lon_max = lon + lonOffset;
      const lat_max = lat + latOffset;
      
      const response = await api.get('/api/satellite/change-detection', {
        params: {
          bbox: `${lon_min},${lat_min},${lon_max},${lat_max}`,
          date1: changeParams.beforeDate,
          date2: changeParams.afterDate,
          source: changeParams.source  // Передаем выбранный источник
        }
      });
      
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
              
              <Grid container spacing={2}>
                <Grid item xs={4}>
                  <TextField
                    fullWidth
                    label="Широта"
                    value={searchParams.lat}
                    onChange={(e) => setSearchParams(prev => ({ ...prev, lat: e.target.value }))}
                    margin="normal"
                    placeholder="55.7558"
                    type="number"
                    inputProps={{ step: 0.0001 }}
                  />
                </Grid>
                <Grid item xs={4}>
                  <TextField
                    fullWidth
                    label="Долгота"
                    value={searchParams.lon}
                    onChange={(e) => setSearchParams(prev => ({ ...prev, lon: e.target.value }))}
                    margin="normal"
                    placeholder="37.6176"
                    type="number"
                    inputProps={{ step: 0.0001 }}
                  />
                </Grid>
                <Grid item xs={4}>
                  <TextField
                    fullWidth
                    label="Радиус (м)"
                    value={searchParams.radius}
                    onChange={(e) => setSearchParams(prev => ({ ...prev, radius: parseInt(e.target.value) || 1000 }))}
                    margin="normal"
                    placeholder="1000"
                    type="number"
                    inputProps={{ min: 100, max: 10000, step: 100 }}
                  />
                </Grid>
              </Grid>
              
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
              
              <FormControl fullWidth margin="normal">
                <InputLabel>Тип снимка</InputLabel>
                <Select
                  value={searchParams.bands}
                  onChange={(e) => setSearchParams(prev => ({ ...prev, bands: e.target.value }))}
                >
                  <MenuItem value="RGB">RGB (видимый спектр)</MenuItem>
                  <MenuItem value="NIR">Ближний инфракрасный</MenuItem>
                  <MenuItem value="NDVI">Индекс растительности</MenuItem>
                  <MenuItem value="THERMAL">Тепловой канал</MenuItem>
                  <MenuItem value="MULTISPECTRAL">Мультиспектральный</MenuItem>
                </Select>
              </FormControl>
              
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
                
                <Box sx={{ mb: 2, position: 'relative' }}>
                  {satelliteImage.image_url ? (
                    <Box 
                      sx={{ 
                        cursor: 'pointer',
                        '&:hover': { opacity: 0.8 },
                        transition: 'opacity 0.2s'
                      }}
                      onClick={() => {
                        setSelectedImage(satelliteImage.image_url);
                        setImageDialogOpen(true);
                      }}
                    >
                      <img
                        src={satelliteImage.image_url}
                        alt="Российский спутниковый снимок"
                        style={{ 
                          width: '100%', 
                          maxHeight: '400px', 
                          objectFit: 'contain', 
                          borderRadius: '8px',
                          border: '2px solid #e0e0e0'
                        }}
                        onError={(e) => {
                          e.target.style.display = 'none';
                          e.target.parentNode.nextSibling.style.display = 'block';
                        }}
                      />
                      <Box 
                        sx={{
                          position: 'absolute',
                          top: 8,
                          right: 8,
                          bgcolor: 'rgba(0,0,0,0.7)',
                          color: 'white',
                          p: 1,
                          borderRadius: 1,
                          display: 'flex',
                          alignItems: 'center',
                          gap: 0.5
                        }}
                      >
                        <ViewIcon fontSize="small" />
                        <Typography variant="caption">Увеличить</Typography>
                      </Box>
                    </Box>
                  ) : (
                    <Box 
                      sx={{ 
                        p: 2, 
                        textAlign: 'center', 
                        bgcolor: 'grey.100', 
                        borderRadius: '8px',
                        border: '2px dashed',
                        borderColor: 'grey.300'
                      }}
                    >
                      <SatelliteIcon sx={{ fontSize: 48, color: 'grey.400', mb: 1 }} />
                      <Typography variant="body2" color="text.secondary">
                        Изображение недоступно
                      </Typography>
                    </Box>
                  )}
                  
                  <Box 
                    sx={{ 
                      display: 'none', 
                      p: 2, 
                      textAlign: 'center', 
                      bgcolor: 'grey.100', 
                      borderRadius: '8px',
                      border: '2px dashed',
                      borderColor: 'grey.300'
                    }}
                  >
                    <SatelliteIcon sx={{ fontSize: 48, color: 'grey.400', mb: 1 }} />
                    <Typography variant="body2" color="text.secondary">
                      Ошибка загрузки изображения
                    </Typography>
                  </Box>
                </Box>
                
                <Box sx={{ mb: 2 }}>
                  <Chip 
                    icon={<SatelliteIcon />}
                    label={`Источник: ${satelliteImage.source || 'Российские спутники'}`}
                    color="primary"
                    sx={{ mb: 1, mr: 1 }}
                  />
                  {satelliteImage.satellite_name && (
                    <Chip 
                      label={`Спутник: ${satelliteImage.satellite_name}`}
                      variant="outlined"
                      sx={{ mb: 1 }}
                    />
                  )}
                </Box>
                
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  <strong>Дата съемки:</strong> {satelliteImage.acquisition_date || 'Не указана'}
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  <strong>Облачность:</strong> {satelliteImage.cloud_coverage || 0}%
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  <strong>Разрешение:</strong> {satelliteImage.resolution || 'Не указано'}м
                </Typography>
                {satelliteImage.coordinates && (
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    <strong>Координаты:</strong> {satelliteImage.coordinates.lat?.toFixed(4)}, {satelliteImage.coordinates.lon?.toFixed(4)}
                  </Typography>
                )}
                
                <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  {satelliteImage.bands && satelliteImage.bands.length > 0 && (
                    <Chip label={`Каналы: ${satelliteImage.bands.join(', ')}`} size="small" />
                  )}
                  {satelliteImage.quality_score && (
                    <Chip 
                      label={`Качество: ${(satelliteImage.quality_score * 100).toFixed(0)}%`} 
                      size="small" 
                      color={satelliteImage.quality_score > 0.7 ? 'success' : 'warning'}
                    />
                  )}
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
                        <Box component="div">
                          <LinearProgress
                            variant="determinate"
                            value={imageAnalysis.vegetation_index * 100}
                            sx={{ mt: 1 }}
                          />
                          <Typography variant="body2" component="span">
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
                        <Box component="div">
                          <LinearProgress
                            variant="determinate"
                            value={imageAnalysis.built_up_area * 100}
                            sx={{ mt: 1 }}
                          />
                          <Typography variant="body2" component="span">
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
                        <Box component="div">
                          <LinearProgress
                            variant="determinate"
                            value={imageAnalysis.water_bodies * 100}
                            sx={{ mt: 1 }}
                          />
                          <Typography variant="body2" component="span">
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
                        <Box component="div">
                          <LinearProgress
                            variant="determinate"
                            value={imageAnalysis.bare_soil * 100}
                            sx={{ mt: 1 }}
                          />
                          <Typography variant="body2" component="span">
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
                        {timeSeriesData.summary.averages ? (timeSeriesData.summary.averages.vegetation_index * 100).toFixed(1) : '0.0'}%
                      </Typography>
                      <Typography variant="body2">
                        Средняя растительность
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={4}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="h6">
                        {timeSeriesData.summary.averages ? (timeSeriesData.summary.averages.built_up_area * 100).toFixed(1) : '0.0'}%
                      </Typography>
                      <Typography variant="body2">
                        Средняя застройка
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={4}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="h6">
                        {timeSeriesData.summary.averages ? timeSeriesData.summary.averages.cloud_coverage.toFixed(1) : '0.0'}%
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
          severity="info" 
          sx={{ mb: 2 }}
          action={
            <Button color="inherit" size="small" onClick={() => setShowConfigDialog(true)}>
              Проверить подключение
            </Button>
          }
        >
          Подключение к российским спутниковым сервисам
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
        <DialogTitle>Настройка российских спутниковых сервисов</DialogTitle>
        <DialogContent>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Российские спутниковые сервисы (Роскосмос, Яндекс) готовы к использованию.
            Дополнительная настройка не требуется.
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Доступные источники:
          </Typography>
          <ul>
            <li>Роскосмос (Ресурс-П, Канопус-В)</li>
            <li>Яндекс Спутник</li>
            <li>ScanEx (Космоснимки)</li>
          </ul>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowConfigDialog(false)}>Отмена</Button>
          <Button onClick={handleConfigureCredentials} disabled={loading}>
            Сохранить
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Image Zoom Dialog */}
      <Dialog 
        open={imageDialogOpen} 
        onClose={() => setImageDialogOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          Спутниковый снимок
          <Button
            onClick={() => selectedImage && window.open(selectedImage, '_blank')}
            sx={{ float: 'right' }}
            startIcon={<DownloadIcon />}
          >
            Открыть в новой вкладке
          </Button>
        </DialogTitle>
        <DialogContent>
          {selectedImage && (
            <Box sx={{ textAlign: 'center' }}>
              <img
                src={selectedImage}
                alt="Увеличенный спутниковый снимок"
                style={{ 
                  maxWidth: '100%', 
                  maxHeight: '70vh', 
                  objectFit: 'contain'
                }}
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setImageDialogOpen(false)}>Закрыть</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default SatelliteAnalyzer;
