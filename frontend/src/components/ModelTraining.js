import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Button,
  LinearProgress,
  Alert,
  Chip,
  Grid,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress
} from '@mui/material';
import {
  Psychology as AIIcon,
  Visibility as YoloIcon,
  TrendingUp as ImprovementIcon,
  CheckCircle as CheckCircleIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Assessment as StatsIcon,
  DataUsage as DataIcon
} from '@mui/icons-material';
import { trainingApi, referenceDbApi } from '../services/api';

const ModelTraining = () => {
  const [trainingStatus, setTrainingStatus] = useState(null);
  const [referenceDbStats, setReferenceDbStats] = useState(null);
  const [isTraining, setIsTraining] = useState(false);
  const [trainingResults, setTrainingResults] = useState({});
  const [error, setError] = useState(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [currentTraining, setCurrentTraining] = useState(null);

  useEffect(() => {
    loadTrainingStatus();
    loadReferenceDbStats();
  }, []);

  const loadTrainingStatus = async () => {
    try {
      const response = await trainingApi.getTrainingStatus();
      if (response.data.success) {
        setTrainingStatus(response.data);
      }
    } catch (err) {
      console.error('Error loading training status:', err);
    }
  };

  const loadReferenceDbStats = async () => {
    try {
      const response = await referenceDbApi.getStats();
      if (response.data.success) {
        setReferenceDbStats(response.data.data);
      }
    } catch (err) {
      console.error('Error loading reference DB stats:', err);
    }
  };

  const handleTrainYolo = async () => {
    setIsTraining(true);
    setCurrentTraining('YOLO');
    setDialogOpen(true);
    setError(null);

    try {
      const response = await trainingApi.trainYolo();
      if (response.data.success) {
        setTrainingResults(prev => ({
          ...prev,
          yolo: response.data
        }));
        await loadTrainingStatus();
      } else {
        setError('Ошибка дообучения YOLO: ' + response.data.error);
      }
    } catch (err) {
      setError('Ошибка дообучения YOLO: ' + err.message);
    } finally {
      setIsTraining(false);
      setCurrentTraining(null);
    }
  };

  const handleTrainMistral = async () => {
    setIsTraining(true);
    setCurrentTraining('Mistral AI');
    setDialogOpen(true);
    setError(null);

    try {
      const response = await trainingApi.trainMistral();
      if (response.data.success) {
        setTrainingResults(prev => ({
          ...prev,
          mistral: response.data
        }));
        await loadTrainingStatus();
      } else {
        setError('Ошибка дообучения Mistral: ' + response.data.error);
      }
    } catch (err) {
      setError('Ошибка дообучения Mistral: ' + err.message);
    } finally {
      setIsTraining(false);
      setCurrentTraining(null);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'success';
      case 'training': return 'warning';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return <CheckCircleIcon color="success" />;
      case 'training': return <CircularProgress size={20} />;
      case 'failed': return <StopIcon color="error" />;
      default: return <PlayIcon />;
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        🤖 Обучение и улучшение моделей
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Статистика готовой базы данных */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <DataIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">
                  Готовая база данных заказчика
                </Typography>
              </Box>
              
              {referenceDbStats ? (
                <Grid container spacing={2}>
                  <Grid item xs={12} md={4}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="h4" color="primary">
                        {referenceDbStats.total_records?.toLocaleString() || '0'}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Всего записей
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="h4" color="success.main">
                        {Object.keys(referenceDbStats.violation_types || {}).length}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Типов нарушений
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Paper sx={{ p: 2, textAlign: 'center' }}>
                      <Typography variant="h4" color="warning.main">
                        {((referenceDbStats.confidence_stats?.avg || 0) * 100).toFixed(1)}%
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Средняя уверенность
                      </Typography>
                    </Paper>
                  </Grid>
                </Grid>
              ) : (
                <LinearProgress />
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* YOLO Training */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <YoloIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">
                  YOLOv8 Дообучение
                </Typography>
                {trainingStatus?.yolo_status && (
                  <Chip 
                    label={trainingStatus.yolo_status.status}
                    color={getStatusColor(trainingStatus.yolo_status.status)}
                    size="small"
                    sx={{ ml: 2 }}
                  />
                )}
              </Box>

              {trainingStatus?.yolo_status && (
                <List dense>
                  <ListItem>
                    <ListItemIcon>
                      {getStatusIcon(trainingStatus.yolo_status.status)}
                    </ListItemIcon>
                    <ListItemText
                      primary="Статус обучения"
                      secondary={trainingStatus.yolo_status.status === 'ready' ? 'Готов к обучению' : 
                                trainingStatus.yolo_status.status === 'completed' ? 'Обучение завершено' : 
                                'В процессе обучения'}
                    />
                  </ListItem>
                  
                  {trainingStatus.yolo_status.epochs > 0 && (
                    <ListItem>
                      <ListItemIcon>
                        <ImprovementIcon color="success" />
                      </ListItemIcon>
                      <ListItemText
                        primary="Улучшение точности"
                        secondary={`+${(trainingStatus.yolo_status.accuracy_improvement * 100).toFixed(1)}% (${trainingStatus.yolo_status.epochs} эпох)`}
                      />
                    </ListItem>
                  )}
                </List>
              )}

              <Button
                variant="contained"
                onClick={handleTrainYolo}
                disabled={isTraining}
                startIcon={<PlayIcon />}
                fullWidth
                sx={{ mt: 2 }}
              >
                {isTraining && currentTraining === 'YOLO' ? 'Обучаем YOLO...' : 'Дообучить YOLO'}
              </Button>

              {trainingResults.yolo && (
                <Alert severity="success" sx={{ mt: 2 }}>
                  ✅ YOLO дообучен! Точность улучшена на {trainingResults.yolo.training?.accuracy_improvement}
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Mistral AI Training */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <AIIcon color="secondary" sx={{ mr: 1 }} />
                <Typography variant="h6">
                  Mistral AI Дообучение
                </Typography>
                {trainingStatus?.mistral_status && (
                  <Chip 
                    label={trainingStatus.mistral_status.status}
                    color={getStatusColor(trainingStatus.mistral_status.status)}
                    size="small"
                    sx={{ ml: 2 }}
                  />
                )}
              </Box>

              {trainingStatus?.mistral_status && (
                <List dense>
                  <ListItem>
                    <ListItemIcon>
                      {getStatusIcon(trainingStatus.mistral_status.status)}
                    </ListItemIcon>
                    <ListItemText
                      primary="Статус обучения"
                      secondary={trainingStatus.mistral_status.status === 'ready' ? 'Готов к обучению' : 
                                trainingStatus.mistral_status.status === 'completed' ? 'Обучение завершено' : 
                                'В процессе обучения'}
                    />
                  </ListItem>
                  
                  {trainingStatus.mistral_status.fine_tuning_steps > 0 && (
                    <ListItem>
                      <ListItemIcon>
                        <ImprovementIcon color="success" />
                      </ListItemIcon>
                      <ListItemText
                        primary="Улучшение точности"
                        secondary={`+${(trainingStatus.mistral_status.accuracy_improvement * 100).toFixed(1)}% (${trainingStatus.mistral_status.fine_tuning_steps} шагов)`}
                      />
                    </ListItem>
                  )}
                </List>
              )}

              <Button
                variant="contained"
                color="secondary"
                onClick={handleTrainMistral}
                disabled={isTraining}
                startIcon={<PlayIcon />}
                fullWidth
                sx={{ mt: 2 }}
              >
                {isTraining && currentTraining === 'Mistral AI' ? 'Обучаем Mistral...' : 'Дообучить Mistral AI'}
              </Button>

              {trainingResults.mistral && (
                <Alert severity="success" sx={{ mt: 2 }}>
                  ✅ Mistral AI дообучен! Точность улучшена на {trainingResults.mistral.training?.accuracy_improvement}
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Общая статистика обучения */}
        {trainingStatus?.dataset_info && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <StatsIcon color="info" sx={{ mr: 1 }} />
                  <Typography variant="h6">
                    Статистика датасета для обучения
                  </Typography>
                </Box>
                
                <Grid container spacing={2}>
                  <Grid item xs={12} md={4}>
                    <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'primary.light', color: 'white' }}>
                      <Typography variant="h5">
                        {trainingStatus.dataset_info.buildings_count?.toLocaleString()}
                      </Typography>
                      <Typography variant="body2">
                        Изображений зданий
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'warning.light', color: 'white' }}>
                      <Typography variant="h5">
                        {trainingStatus.dataset_info.garbage_count?.toLocaleString()}
                      </Typography>
                      <Typography variant="body2">
                        Изображений мусора
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'success.light', color: 'white' }}>
                      <Typography variant="h5">
                        {trainingStatus.dataset_info.total_images?.toLocaleString()}
                      </Typography>
                      <Typography variant="body2">
                        Всего для обучения
                      </Typography>
                    </Paper>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>

      {/* Диалог процесса обучения */}
      <Dialog open={dialogOpen} maxWidth="sm" fullWidth>
        <DialogTitle>
          Дообучение {currentTraining}
        </DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" alignItems="center" py={3}>
            <CircularProgress size={60} sx={{ mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              Выполняется дообучение модели
            </Typography>
            <Typography variant="body2" color="text.secondary" textAlign="center">
              Используем готовую базу данных заказчика с {referenceDbStats?.total_records?.toLocaleString()} записями
              для улучшения точности детекции нарушений
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)} disabled={isTraining}>
            Скрыть
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ModelTraining;
