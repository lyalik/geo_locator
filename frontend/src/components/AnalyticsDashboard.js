import React, { useState, useEffect } from 'react';
import {
  Box, Grid, Card, CardContent, Typography, Paper, Select, MenuItem,
  FormControl, InputLabel, Button, Chip, LinearProgress, Alert
} from '@mui/material';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, Area, AreaChart
} from 'recharts';
import {
  TrendingUp as TrendingUpIcon, Assessment as AssessmentIcon,
  Speed as SpeedIcon, Storage as StorageIcon, Refresh as RefreshIcon,
  Satellite as SatelliteIcon, Public as PublicIcon
} from '@mui/icons-material';
import { api } from '../services/api';

const AnalyticsDashboard = ({ violations = [] }) => {
  const [timeRange, setTimeRange] = useState('7d');
  const [loading, setLoading] = useState(false);
  const [cacheStats, setCacheStats] = useState(null);
  const [performanceStats, setPerformanceStats] = useState(null);
  const [satelliteStats, setSatelliteStats] = useState(null);
  const [realViolationsData, setRealViolationsData] = useState([]);

  useEffect(() => {
    loadAnalyticsData();
  }, [timeRange, violations]);

  const loadAnalyticsData = async () => {
    setLoading(true);
    try {
      // Загружаем реальные данные нарушений из глобального хранилища
      await loadRealViolationsData();
      
      // Load cache statistics
      const cacheResponse = await fetch('http://localhost:5000/api/cache/info');
      if (cacheResponse.ok) {
        const cacheData = await cacheResponse.json();
        setCacheStats(cacheData.data);
      }

      // Load satellite service statistics
      await loadSatelliteStats();

      // Generate performance stats from violations data
      generatePerformanceStats();
    } catch (error) {
      console.error('Error loading analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadRealViolationsData = async () => {
    try {
      // Получаем данные из глобальных хранилищ результатов
      const batchResults = window.GLOBAL_BATCH_RESULTS || [];
      const singleResults = window.GLOBAL_SINGLE_RESULTS || [];
      
      // Объединяем все результаты
      const allResults = [...batchResults, ...singleResults];
      
      // Преобразуем в формат для аналитики
      const violationsData = allResults.flatMap(result => {
        if (result.violations && result.violations.length > 0) {
          return result.violations.map(violation => ({
            id: violation.id || Math.random().toString(36),
            category: violation.category || 'unknown',
            confidence: violation.confidence || 0,
            created_at: result.uploadTime || new Date().toISOString(),
            location: result.location,
            satellite_data: result.satellite_data,
            image_path: result.image || result.image_path,
            violation_id: result.violation_id
          }));
        }
        return [];
      });

      console.log('Loaded real violations data:', violationsData);
      setRealViolationsData(violationsData);
      
      // Также пытаемся загрузить данные через API
      try {
        const response = await api.get('/api/violations/list');
        if (response.data.success && response.data.data) {
          const apiViolations = response.data.data.map(v => ({
            ...v,
            created_at: v.created_at || v.timestamp || new Date().toISOString()
          }));
          
          // Объединяем с локальными данными
          const combinedData = [...violationsData, ...apiViolations];
          setRealViolationsData(combinedData);
          console.log('Combined with API data:', combinedData);
        }
      } catch (apiError) {
        console.log('API violations not available, using local data only');
      }
      
    } catch (error) {
      console.error('Error loading real violations data:', error);
    }
  };

  const loadSatelliteStats = async () => {
    try {
      const response = await api.get('/api/satellite/sources');
      if (response.data.success) {
        const sources = response.data.data;
        
        // Generate satellite usage statistics from real data
        const satelliteUsage = realViolationsData.filter(v => v.satellite_data).reduce((acc, v) => {
          const source = v.satellite_data?.source || 'unknown';
          acc[source] = (acc[source] || 0) + 1;
          return acc;
        }, {});

        setSatelliteStats({
          sources: sources,
          usage: satelliteUsage,
          totalWithSatellite: realViolationsData.filter(v => v.satellite_data).length,
          coverageRate: realViolationsData.length > 0 ? 
            (realViolationsData.filter(v => v.satellite_data).length / realViolationsData.length * 100).toFixed(1) : 0
        });
      }
    } catch (error) {
      console.error('Error loading satellite stats:', error);
      // Generate mock data for demo
      setSatelliteStats({
        sources: [
          { name: 'Роскосмос', status: 'active', satellites: ['Ресурс-П', 'Канопус-В'] },
          { name: 'Яндекс Спутник', status: 'active', satellites: ['Яндекс-1'] },
          { name: 'ScanEx', status: 'active', satellites: ['Архивные данные'] }
        ],
        usage: {
          'Роскосмос': Math.floor(violations.length * 0.4),
          'Яндекс Спутник': Math.floor(violations.length * 0.35),
          'ScanEx': Math.floor(violations.length * 0.25)
        },
        totalWithSatellite: Math.floor(violations.length * 0.8),
        coverageRate: 0.8
      });
    }
  };

  const generatePerformanceStats = () => {
    const dataToUse = realViolationsData.length > 0 ? realViolationsData : violations;
    
    if (dataToUse.length === 0) {
      setPerformanceStats(null);
      return;
    }

    // Category distribution
    const categoryStats = dataToUse.reduce((acc, violation) => {
      const category = violation.category || 'unknown';
      acc[category] = (acc[category] || 0) + 1;
      return acc;
    }, {});

    // Time-based analysis
    const now = new Date();
    const timeRangeMs = {
      '24h': 24 * 60 * 60 * 1000,
      '7d': 7 * 24 * 60 * 60 * 1000,
      '30d': 30 * 24 * 60 * 60 * 1000
    };

    const cutoffTime = new Date(now.getTime() - timeRangeMs[timeRange]);
    const recentViolations = dataToUse.filter(v => {
      const violationTime = new Date(v.created_at || v.timestamp || now);
      return violationTime >= cutoffTime;
    });

    // Confidence analysis
    const confidenceStats = dataToUse.reduce((acc, v) => {
      const confidence = v.confidence || 0;
      if (confidence >= 0.8) acc.high++;
      else if (confidence >= 0.6) acc.medium++;
      else acc.low++;
      return acc;
    }, { high: 0, medium: 0, low: 0 });

    // Location analysis
    const locationStats = dataToUse.reduce((acc, v) => {
      if (v.location && (v.location.coordinates || v.location.lat)) {
        acc.withLocation++;
      } else {
        acc.withoutLocation++;
      }
      return acc;
    }, { withLocation: 0, withoutLocation: 0 });

    setPerformanceStats({
      total: dataToUse.length,
      recent: recentViolations.length,
      categories: categoryStats,
      confidence: confidenceStats,
      location: locationStats,
      averageConfidence: dataToUse.length > 0 ? 
        (dataToUse.reduce((sum, v) => sum + (v.confidence || 0), 0) / dataToUse.length).toFixed(2) : 0
    });
  };

  const getCategoryData = () => {
    const dataToUse = realViolationsData.length > 0 ? realViolationsData : violations;
    const categoryCount = dataToUse.reduce((acc, violation) => {
      const category = violation.category || 'unknown';
      acc[category] = (acc[category] || 0) + 1;
      return acc;
    }, {});

    return Object.entries(categoryCount).map(([category, count]) => ({
      name: formatCategoryName(category),
      value: count,
      percentage: dataToUse.length > 0 ? ((count / dataToUse.length) * 100).toFixed(1) : 0
    }));
  };

  const getConfidenceData = () => {
    const dataToUse = realViolationsData.length > 0 ? realViolationsData : violations;
    const ranges = {
      'Высокая (>80%)': 0,
      'Средняя (60-80%)': 0,
      'Низкая (<60%)': 0
    };

    dataToUse.forEach(v => {
      const conf = v.confidence || 0;
      if (conf > 0.8) ranges['Высокая (>80%)']++;
      else if (conf >= 0.6) ranges['Средняя (60-80%)']++;
      else ranges['Низкая (<60%)']++;
    });

    return Object.entries(ranges).map(([range, count]) => ({
      name: range,
      value: count,
      percentage: dataToUse.length > 0 ? ((count / dataToUse.length) * 100).toFixed(1) : 0
    }));
  };

  const getTimeSeriesData = () => {
    const dataToUse = realViolationsData.length > 0 ? realViolationsData : violations;
    const dailyData = {};
    dataToUse.forEach(v => {
      const date = new Date(v.created_at || v.timestamp || new Date()).toLocaleDateString('ru-RU');
      dailyData[date] = (dailyData[date] || 0) + 1;
    });

    return Object.entries(dailyData)
      .sort(([a], [b]) => new Date(a) - new Date(b))
      .map(([date, count]) => ({ date, count }));
  };

  const getSatelliteUsageData = () => {
    if (!satelliteStats?.usage) return [];
    
    return Object.entries(satelliteStats.usage).map(([source, count]) => ({
      name: source,
      value: count,
      percentage: satelliteStats.totalWithSatellite > 0 ? 
        ((count / satelliteStats.totalWithSatellite) * 100).toFixed(1) : 0
    }));
  };

  const formatCategoryName = (category) => {
    const names = {
      illegal_construction: 'Незаконное строительство',
      unauthorized_signage: 'Несанкционированные вывески',
      blocked_entrance: 'Заблокированный вход',
      improper_waste_disposal: 'Неправильная утилизация',
      unauthorized_modification: 'Несанкционированные изменения',
      parking_violation: 'Нарушение парковки',
      structural_damage: 'Структурные повреждения',
      unsafe_conditions: 'Небезопасные условия'
    };
    return names[category] || category;
  };

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D', '#FFC658'];

  const categoryData = getCategoryData();
  const confidenceData = getConfidenceData();
  const timeSeriesData = getTimeSeriesData();
  const satelliteUsageData = getSatelliteUsageData();

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          Аналитическая панель
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Период</InputLabel>
            <Select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              label="Период"
            >
              <MenuItem value="1d">1 день</MenuItem>
              <MenuItem value="7d">7 дней</MenuItem>
              <MenuItem value="30d">30 дней</MenuItem>
              <MenuItem value="90d">90 дней</MenuItem>
            </Select>
          </FormControl>
          <Button
            startIcon={<RefreshIcon />}
            onClick={loadAnalyticsData}
            variant="outlined"
            disabled={loading}
          >
            Обновить
          </Button>
        </Box>
      </Box>

      {loading && <LinearProgress sx={{ mb: 3 }} />}

      {/* Key Metrics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <AssessmentIcon color="primary" sx={{ fontSize: 40 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Всего нарушений
                  </Typography>
                  <Typography variant="h4">
                    {violations.length}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <TrendingUpIcon color="success" sx={{ fontSize: 40 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Средняя точность
                  </Typography>
                  <Typography variant="h4">
                    {performanceStats ? `${(performanceStats.avgAccuracy * 100).toFixed(1)}%` : '—'}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <SpeedIcon color="warning" sx={{ fontSize: 40 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Успешность обработки
                  </Typography>
                  <Typography variant="h4">
                    {performanceStats ? `${(performanceStats.successRate * 100).toFixed(1)}%` : '—'}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <SatelliteIcon color="info" sx={{ fontSize: 40 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Покрытие спутниковыми данными
                  </Typography>
                  <Typography variant="h4">
                    {satelliteStats ? `${(satelliteStats.coverageRate * 100).toFixed(1)}%` : '—'}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={3}>
        {/* Category Distribution */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Распределение по категориям
              </Typography>
              {categoryData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={categoryData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percentage }) => `${name}: ${percentage}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {categoryData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <Alert severity="info">Нет данных для отображения</Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Satellite Usage Distribution */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Использование спутниковых сервисов
              </Typography>
              {satelliteUsageData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={satelliteUsageData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percentage }) => `${name}: ${percentage}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {satelliteUsageData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <Alert severity="info">Нет данных о спутниковых сервисах</Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Time Series */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Динамика обнаружения нарушений
              </Typography>
              {timeSeriesData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={timeSeriesData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Area type="monotone" dataKey="count" stroke="#8884d8" fill="#8884d8" />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <Alert severity="info">Нет данных для отображения</Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Satellite Services Status */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Статус спутниковых сервисов
              </Typography>
              {satelliteStats ? (
                <Box>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="textSecondary">
                      Активных источников
                    </Typography>
                    <Typography variant="h6">
                      {satelliteStats.sources?.length || 0}
                    </Typography>
                  </Box>
                  
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="textSecondary">
                      Нарушений со спутниковыми данными
                    </Typography>
                    <Typography variant="h6">
                      {satelliteStats.totalWithSatellite || 0}
                    </Typography>
                  </Box>
                  
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="textSecondary">
                      Покрытие территории
                    </Typography>
                    <Typography variant="h6">
                      {satelliteStats.coverageRate ? `${(satelliteStats.coverageRate * 100).toFixed(1)}%` : '0%'}
                    </Typography>
                  </Box>

                  {satelliteStats.sources && Array.isArray(satelliteStats.sources) && (
                    <Box>
                      <Typography variant="body2" color="textSecondary" gutterBottom>
                        Доступные сервисы:
                      </Typography>
                      {satelliteStats.sources.map((source, index) => (
                        <Chip
                          key={index}
                          icon={<SatelliteIcon />}
                          label={source.name}
                          size="small"
                          color={source.status === 'active' ? 'success' : 'default'}
                          sx={{ mr: 1, mb: 1 }}
                        />
                      ))}
                    </Box>
                  )}
                </Box>
              ) : (
                <Alert severity="info">Загрузка данных спутниковых сервисов...</Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Processing Time Trend */}
        {performanceStats?.processingTimes && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Тренд времени обработки
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={performanceStats.processingTimes}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line 
                      type="monotone" 
                      dataKey="avgProcessingTime" 
                      stroke="#8884d8" 
                      name="Среднее время (сек)"
                    />
                    <Line 
                      type="monotone" 
                      dataKey="violationsProcessed" 
                      stroke="#82ca9d" 
                      name="Обработано нарушений"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    </Box>
  );
};

export default AnalyticsDashboard;
