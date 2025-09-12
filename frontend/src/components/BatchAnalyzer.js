import React, { useState, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  LinearProgress,
  Alert,
  Grid,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Tooltip,
  Divider,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  VideoFile as VideoIcon,
  Image as ImageIcon,
  Delete as DeleteIcon,
  PlayArrow as PlayIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Analytics as AnalyticsIcon,
  ExpandMore as ExpandMoreIcon,
  Download as DownloadIcon,
  Map as MapIcon
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import { useSnackbar } from 'notistack';
import { videoAnalysis, imageAnalysis } from '../services/api';
import InteractiveResultsMap from './InteractiveResultsMap';

const BatchAnalyzer = () => {
  const { enqueueSnackbar } = useSnackbar();
  const [files, setFiles] = useState([]);
  const [locationHint, setLocationHint] = useState('');
  const [frameInterval, setFrameInterval] = useState(30);
  const [maxFrames, setMaxFrames] = useState(10);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResults, setAnalysisResults] = useState([]);
  const [currentAnalyzing, setCurrentAnalyzing] = useState(null);
  const [overallProgress, setOverallProgress] = useState(0);

  // Обработка загрузки файлов
  const onDrop = useCallback((acceptedFiles) => {
    const newFiles = acceptedFiles.map((file, index) => ({
      id: Date.now() + index,
      file,
      name: file.name,
      size: file.size,
      type: file.type.startsWith('video/') ? 'video' : 'image',
      status: 'pending', // pending, analyzing, completed, error
      progress: 0,
      result: null,
      error: null
    }));
    
    setFiles(prev => [...prev, ...newFiles]);
    enqueueSnackbar(`Добавлено ${newFiles.length} файлов для анализа`, { variant: 'success' });
  }, [enqueueSnackbar]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'video/*': ['.mp4', '.avi', '.mov', '.mkv'],
      'image/*': ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
    },
    multiple: true
  });

  // Удаление файла из списка
  const removeFile = (fileId) => {
    setFiles(prev => prev.filter(f => f.id !== fileId));
  };

  // Очистка всех файлов
  const clearAllFiles = () => {
    setFiles([]);
    setAnalysisResults([]);
    setOverallProgress(0);
  };

  // Анализ одного файла
  const analyzeFile = async (fileData) => {
    try {
      setCurrentAnalyzing(fileData.id);
      
      // Обновляем статус файла
      setFiles(prev => prev.map(f => 
        f.id === fileData.id 
          ? { ...f, status: 'analyzing', progress: 0 }
          : f
      ));

      const formData = new FormData();
      formData.append('file', fileData.file);
      if (locationHint) formData.append('location_hint', locationHint);
      
      let result;
      if (fileData.type === 'video') {
        formData.append('frame_interval', frameInterval.toString());
        formData.append('max_frames', maxFrames.toString());
        result = await videoAnalysis(formData);
      } else {
        result = await imageAnalysis(formData);
      }

      // Обновляем результат
      setFiles(prev => prev.map(f => 
        f.id === fileData.id 
          ? { ...f, status: 'completed', progress: 100, result }
          : f
      ));

      return { fileId: fileData.id, success: true, result };
    } catch (error) {
      console.error(`Ошибка анализа файла ${fileData.name}:`, error);
      
      setFiles(prev => prev.map(f => 
        f.id === fileData.id 
          ? { ...f, status: 'error', error: error.message }
          : f
      ));

      return { fileId: fileData.id, success: false, error: error.message };
    }
  };

  // Пакетный анализ всех файлов
  const startBatchAnalysis = async () => {
    if (files.length === 0) {
      enqueueSnackbar('Добавьте файлы для анализа', { variant: 'warning' });
      return;
    }

    setIsAnalyzing(true);
    setAnalysisResults([]);
    setOverallProgress(0);

    const pendingFiles = files.filter(f => f.status === 'pending');
    const results = [];

    for (let i = 0; i < pendingFiles.length; i++) {
      const fileData = pendingFiles[i];
      const result = await analyzeFile(fileData);
      results.push(result);
      
      // Обновляем общий прогресс
      const progress = ((i + 1) / pendingFiles.length) * 100;
      setOverallProgress(progress);
    }

    setAnalysisResults(results);
    setIsAnalyzing(false);
    setCurrentAnalyzing(null);

    const successful = results.filter(r => r.success).length;
    const failed = results.filter(r => !r.success).length;

    enqueueSnackbar(
      `Анализ завершен: ${successful} успешно, ${failed} ошибок`, 
      { variant: successful > 0 ? 'success' : 'error' }
    );
  };

  // Экспорт результатов в JSON
  const exportResults = () => {
    const successfulResults = files
      .filter(f => f.status === 'completed' && f.result)
      .map(f => ({
        filename: f.name,
        type: f.type,
        coordinates: f.result.coordinates,
        confidence: f.result.confidence,
        processing_time: f.result.processing_time,
        timestamp: new Date().toISOString()
      }));

    const dataStr = JSON.stringify(successfulResults, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `batch_analysis_results_${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    
    URL.revokeObjectURL(url);
  };

  // Получение статистики
  const getStatistics = () => {
    const total = files.length;
    const completed = files.filter(f => f.status === 'completed').length;
    const errors = files.filter(f => f.status === 'error').length;
    const pending = files.filter(f => f.status === 'pending').length;
    const withCoordinates = files.filter(f => f.result?.coordinates).length;
    
    return { total, completed, errors, pending, withCoordinates };
  };

  const stats = getStatistics();
  const hasResults = files.some(f => f.status === 'completed');

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        📁 Пакетный анализ файлов
      </Typography>
      
      <Typography variant="body1" color="textSecondary" sx={{ mb: 3 }}>
        Загрузите несколько изображений или видео для одновременного анализа координат
      </Typography>

      {/* Настройки анализа */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>Настройки анализа</Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Подсказка местоположения"
                value={locationHint}
                onChange={(e) => setLocationHint(e.target.value)}
                placeholder="Например: Краснодар, Россия"
                helperText="Поможет улучшить точность определения координат"
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel>Интервал кадров</InputLabel>
                <Select
                  value={frameInterval}
                  onChange={(e) => setFrameInterval(e.target.value)}
                  label="Интервал кадров"
                >
                  <MenuItem value={15}>Каждый 15-й кадр</MenuItem>
                  <MenuItem value={30}>Каждый 30-й кадр</MenuItem>
                  <MenuItem value={60}>Каждый 60-й кадр</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel>Макс. кадров</InputLabel>
                <Select
                  value={maxFrames}
                  onChange={(e) => setMaxFrames(e.target.value)}
                  label="Макс. кадров"
                >
                  <MenuItem value={5}>5 кадров</MenuItem>
                  <MenuItem value={10}>10 кадров</MenuItem>
                  <MenuItem value={20}>20 кадров</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Зона загрузки файлов */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box
            {...getRootProps()}
            sx={{
              border: '2px dashed',
              borderColor: isDragActive ? 'primary.main' : 'grey.300',
              borderRadius: 2,
              p: 4,
              textAlign: 'center',
              cursor: 'pointer',
              backgroundColor: isDragActive ? 'action.hover' : 'transparent',
              transition: 'all 0.2s ease'
            }}
          >
            <input {...getInputProps()} />
            <UploadIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              {isDragActive ? 'Отпустите файлы здесь' : 'Перетащите файлы сюда или нажмите для выбора'}
            </Typography>
            <Typography variant="body2" color="textSecondary">
              Поддерживаются видео (MP4, AVI, MOV) и изображения (JPG, PNG, BMP, TIFF)
            </Typography>
          </Box>
        </CardContent>
      </Card>

      {/* Статистика и управление */}
      {files.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">Файлы для анализа ({files.length})</Typography>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  variant="contained"
                  startIcon={<PlayIcon />}
                  onClick={startBatchAnalysis}
                  disabled={isAnalyzing || stats.pending === 0}
                >
                  {isAnalyzing ? 'Анализ...' : 'Начать анализ'}
                </Button>
                {hasResults && (
                  <Button
                    variant="outlined"
                    startIcon={<DownloadIcon />}
                    onClick={exportResults}
                  >
                    Экспорт результатов
                  </Button>
                )}
                <Button
                  variant="outlined"
                  color="error"
                  onClick={clearAllFiles}
                  disabled={isAnalyzing}
                >
                  Очистить все
                </Button>
              </Box>
            </Box>

            {/* Общий прогресс */}
            {isAnalyzing && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" gutterBottom>
                  Общий прогресс: {Math.round(overallProgress)}%
                </Typography>
                <LinearProgress variant="determinate" value={overallProgress} />
              </Box>
            )}

            {/* Статистика */}
            <Grid container spacing={2} sx={{ mb: 2 }}>
              <Grid item>
                <Chip label={`Всего: ${stats.total}`} />
              </Grid>
              <Grid item>
                <Chip label={`Ожидают: ${stats.pending}`} color="default" />
              </Grid>
              <Grid item>
                <Chip label={`Завершено: ${stats.completed}`} color="success" />
              </Grid>
              <Grid item>
                <Chip label={`Ошибки: ${stats.errors}`} color="error" />
              </Grid>
              <Grid item>
                <Chip label={`С координатами: ${stats.withCoordinates}`} color="primary" />
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Список файлов */}
      {files.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <List>
              {files.map((fileData, index) => (
                <React.Fragment key={fileData.id}>
                  <ListItem>
                    <ListItemIcon>
                      {fileData.type === 'video' ? <VideoIcon /> : <ImageIcon />}
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="body1">{fileData.name}</Typography>
                          {fileData.status === 'completed' && <CheckIcon color="success" />}
                          {fileData.status === 'error' && <ErrorIcon color="error" />}
                          {currentAnalyzing === fileData.id && (
                            <Chip size="small" label="Анализируется..." color="primary" />
                          )}
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="body2" color="textSecondary">
                            {(fileData.size / 1024 / 1024).toFixed(1)} MB • {fileData.type}
                          </Typography>
                          {fileData.status === 'analyzing' && (
                            <LinearProgress sx={{ mt: 1 }} />
                          )}
                          {fileData.status === 'error' && (
                            <Alert severity="error" sx={{ mt: 1 }}>
                              {fileData.error}
                            </Alert>
                          )}
                          {fileData.result?.coordinates && (
                            <Typography variant="body2" color="success.main" sx={{ mt: 1 }}>
                              📍 Координаты найдены: {fileData.result.coordinates.latitude.toFixed(4)}, {fileData.result.coordinates.longitude.toFixed(4)}
                            </Typography>
                          )}
                        </Box>
                      }
                    />
                    <IconButton
                      onClick={() => removeFile(fileData.id)}
                      disabled={isAnalyzing}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </ListItem>
                  {index < files.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          </CardContent>
        </Card>
      )}

      {/* Результаты на карте */}
      {hasResults && (
        <Accordion sx={{ mb: 3 }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="h6">
              <MapIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
              Результаты на карте
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            {files
              .filter(f => f.result?.coordinates)
              .map(fileData => (
                <Box key={fileData.id} sx={{ mb: 3 }}>
                  <Typography variant="subtitle1" gutterBottom>
                    {fileData.name}
                  </Typography>
                  <InteractiveResultsMap
                    coordinates={fileData.result.coordinates}
                    satelliteData={fileData.result.satellite_data}
                    locationInfo={fileData.result.location_info}
                    height={300}
                  />
                </Box>
              ))
            }
          </AccordionDetails>
        </Accordion>
      )}

      {/* Детальные результаты */}
      {hasResults && (
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="h6">
              <AnalyticsIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
              Детальные результаты
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Файл</TableCell>
                    <TableCell>Статус</TableCell>
                    <TableCell>Координаты</TableCell>
                    <TableCell>Точность</TableCell>
                    <TableCell>Время анализа</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {files.map(fileData => (
                    <TableRow key={fileData.id}>
                      <TableCell>{fileData.name}</TableCell>
                      <TableCell>
                        {fileData.status === 'completed' && <Chip label="Завершено" color="success" size="small" />}
                        {fileData.status === 'error' && <Chip label="Ошибка" color="error" size="small" />}
                        {fileData.status === 'pending' && <Chip label="Ожидает" color="default" size="small" />}
                        {fileData.status === 'analyzing' && <Chip label="Анализ" color="primary" size="small" />}
                      </TableCell>
                      <TableCell>
                        {fileData.result?.coordinates ? (
                          `${fileData.result.coordinates.latitude.toFixed(4)}, ${fileData.result.coordinates.longitude.toFixed(4)}`
                        ) : (
                          '—'
                        )}
                      </TableCell>
                      <TableCell>
                        {fileData.result?.coordinates ? 
                          `${Math.round(fileData.result.coordinates.confidence * 100)}%` : 
                          '—'
                        }
                      </TableCell>
                      <TableCell>
                        {fileData.result?.processing_time ? 
                          `${fileData.result.processing_time.toFixed(1)}с` : 
                          '—'
                        }
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </AccordionDetails>
        </Accordion>
      )}
    </Box>
  );
};

export default BatchAnalyzer;
