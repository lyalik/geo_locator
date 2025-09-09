import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useSnackbar } from 'notistack';
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Grid,
  Chip,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  CloudUpload as CloudUploadIcon,
  VideoFile as VideoFileIcon,
  PlayArrow as PlayArrowIcon,
  Assessment as AssessmentIcon,
  LocationOn as LocationOnIcon,
  Schedule as ScheduleIcon,
  ExpandMore as ExpandMoreIcon,
  Info as InfoIcon,
  Map as MapIcon
} from '@mui/icons-material';
import { videoAnalysis } from '../services/api';

const VideoAnalyzer = () => {
  const { enqueueSnackbar } = useSnackbar();
  const [selectedFile, setSelectedFile] = useState(null);
  const [locationHint, setLocationHint] = useState('');
  const [frameInterval, setFrameInterval] = useState(30);
  const [maxFrames, setMaxFrames] = useState(10);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isEstimating, setIsEstimating] = useState(false);
  const [analysisResults, setAnalysisResults] = useState(null);
  const [processingEstimate, setProcessingEstimate] = useState(null);
  const [progress, setProgress] = useState(0);
  const [fileType, setFileType] = useState(null); // 'image' or 'video'

  // Handle file drop
  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      setSelectedFile(file);
      setAnalysisResults(null);
      setProcessingEstimate(null);
      
      // Determine file type
      const isImage = file.type.startsWith('image/');
      const isVideo = file.type.startsWith('video/');
      
      if (isImage) {
        setFileType('image');
      } else if (isVideo) {
        setFileType('video');
      } else {
        setFileType(null);
      }
      
      enqueueSnackbar(`Выбран ${isImage ? 'изображение' : 'видео'}: ${file.name}`, { variant: 'info' });
    }
  }, [enqueueSnackbar]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'video/*': ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'],
      'image/*': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
    },
    multiple: false,
    maxSize: 500 * 1024 * 1024 // 500MB
  });

  // Analyze image coordinates
  const analyzeImageCoordinates = async (file) => {
    const formData = new FormData();
    formData.append('image', file);
    if (locationHint) {
      formData.append('location_hint', locationHint);
    }

    const response = await fetch('http://localhost:5001/api/coordinates/detect', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  };

  // Estimate processing time
  const handleEstimateProcessing = async () => {
    if (!selectedFile) {
      enqueueSnackbar('Сначала выберите файл', { variant: 'warning' });
      return;
    }

    if (fileType === 'image') {
      enqueueSnackbar('Для изображений оценка времени не требуется', { variant: 'info' });
      return;
    }

    setIsEstimating(true);
    try {
      const formData = new FormData();
      formData.append('video', selectedFile);
      formData.append('frame_interval', frameInterval.toString());
      formData.append('max_frames', maxFrames.toString());

      const response = await videoAnalysis.estimateProcessingTime(
        selectedFile, 
        frameInterval, 
        maxFrames
      );

      if (response.data.success) {
        setProcessingEstimate(response.data.data);
        enqueueSnackbar('Оценка времени обработки получена', { variant: 'success' });
      } else {
        throw new Error(response.data.message || 'Ошибка при оценке времени обработки');
      }
    } catch (error) {
      console.error('Estimation error:', error);
      enqueueSnackbar(`Ошибка оценки: ${error.message}`, { variant: 'error' });
    } finally {
      setIsEstimating(false);
    }
  };

  // Start analysis (video or image)
  const handleAnalyzeFile = async () => {
    if (!selectedFile) {
      enqueueSnackbar('Сначала выберите файл', { variant: 'warning' });
      return;
    }

    setIsAnalyzing(true);
    setProgress(0);
    setAnalysisResults(null);

    try {
      if (fileType === 'image') {
        // Image coordinate analysis
        setProgress(50);
        const data = await analyzeImageCoordinates(selectedFile);
        setProgress(100);

        if (data.success) {
          console.log('🔍 Полученные данные от API:', data);
          console.log('🗺️ Координаты:', data.data?.coordinates);
          console.log('📍 Объекты:', data.data?.objects);
          
          // Transform image coordinate results to match video analysis format
          const apiData = data.data || data;
          const transformedResults = {
            total_frames_processed: 1,
            successful_frames: 1,
            total_objects_detected: apiData.total_objects || 0,
            coordinates: apiData.coordinates ? {
              latitude: apiData.coordinates.latitude,
              longitude: apiData.coordinates.longitude,
              confidence: apiData.coordinates.confidence || 1,
              source: apiData.coordinates.source || 'EXIF',
              frame_count: 1
            } : null,
            object_statistics: apiData.objects ? {
              category_counts: apiData.objects.reduce((acc, obj) => {
                acc[obj.category] = (acc[obj.category] || 0) + 1;
                return acc;
              }, {}),
              category_avg_confidence: apiData.objects.reduce((acc, obj) => {
                acc[obj.category] = obj.confidence;
                return acc;
              }, {}),
              unique_categories: [...new Set(apiData.objects.map(obj => obj.category))].length,
              average_geolocation_utility: apiData.objects.reduce((sum, obj) => sum + (obj.geolocation_utility || 0), 0) / apiData.objects.length,
              high_utility_objects: apiData.objects.filter(obj => (obj.geolocation_utility || 0) > 0.7).length
            } : null,
            frame_results: [{
              frame_number: 1,
              timestamp: 0,
              success: true,
              objects: apiData.objects || [],
              coordinates: apiData.coordinates
            }]
          };
          setAnalysisResults(transformedResults);
          enqueueSnackbar('Анализ изображения завершен успешно!', { variant: 'success' });
        } else {
          throw new Error(data.message || 'Ошибка при анализе изображения');
        }
      } else {
        // Video analysis
        const progressInterval = setInterval(() => {
          setProgress((prev) => {
            if (prev >= 90) {
              clearInterval(progressInterval);
              return 90;
            }
            return prev + 5;
          });
        }, 1000);

        const response = await videoAnalysis.analyze(
          selectedFile,
          locationHint,
          frameInterval,
          maxFrames
        );

        clearInterval(progressInterval);
        setProgress(100);

        if (response.data.success) {
          setAnalysisResults(response.data.data);
          enqueueSnackbar('Анализ видео завершен успешно!', { variant: 'success' });
        } else {
          throw new Error(response.data.message || 'Ошибка при анализе видео');
        }
      }
    } catch (error) {
      console.error('Analysis error:', error);
      enqueueSnackbar(`Ошибка анализа: ${error.message}`, { variant: 'error' });
    } finally {
      setTimeout(() => {
        setIsAnalyzing(false);
        setProgress(0);
      }, 1000);
    }
  };

  // Format time duration
  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Format file size
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        <VideoFileIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
        Анализ медиафайлов
      </Typography>
      
      <Typography variant="body1" color="textSecondary" sx={{ mb: 3 }}>
        Загрузите фото или видео для анализа и определения координат объектов
      </Typography>

      {/* File Upload Section */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box
            {...getRootProps()}
            sx={{
              border: '2px dashed',
              borderColor: isDragActive ? 'primary.main' : 'divider',
              borderRadius: 2,
              p: 4,
              textAlign: 'center',
              cursor: 'pointer',
              backgroundColor: isDragActive ? 'action.hover' : 'background.paper',
              transition: 'all 0.2s ease-in-out',
              '&:hover': {
                backgroundColor: 'action.hover',
                borderColor: 'primary.main',
              },
            }}
          >
            <input {...getInputProps()} />
            <CloudUploadIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              {isDragActive 
                ? 'Отпустите файл здесь' 
                : 'Перетащите фото или видео сюда или нажмите для выбора'}
            </Typography>
            <Typography variant="body2" color="textSecondary">
              Видео: MP4, AVI, MOV, MKV, WMV, FLV, WEBM
            </Typography>
            <Typography variant="body2" color="textSecondary">
              Фото: JPG, JPEG, PNG, GIF, BMP, WEBP
            </Typography>
            <Typography variant="body2" color="textSecondary">
              Максимальный размер: 500 МБ
            </Typography>
          </Box>

          {selectedFile && (
            <Box sx={{ mt: 2, p: 2, backgroundColor: 'grey.50', borderRadius: 1 }}>
              <Grid container spacing={2} alignItems="center">
                <Grid item>
                  <VideoFileIcon color="primary" />
                </Grid>
                <Grid item xs>
                  <Typography variant="subtitle1">{selectedFile.name}</Typography>
                  <Typography variant="body2" color="textSecondary">
                    {formatFileSize(selectedFile.size)}
                  </Typography>
                </Grid>
              </Grid>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Analysis Parameters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Параметры анализа
          </Typography>
          
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Подсказка местоположения"
                placeholder="Например: Москва, Красная площадь"
                value={locationHint}
                onChange={(e) => setLocationHint(e.target.value)}
                helperText="Укажите примерное местоположение для повышения точности"
              />
            </Grid>
            
            {fileType === 'video' && (
              <>
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Интервал кадров</InputLabel>
                    <Select
                      value={frameInterval}
                      label="Интервал кадров"
                      onChange={(e) => setFrameInterval(e.target.value)}
                    >
                      <MenuItem value={15}>Каждые 15 кадров (высокое качество)</MenuItem>
                      <MenuItem value={30}>Каждые 30 кадров (рекомендуется)</MenuItem>
                      <MenuItem value={60}>Каждые 60 кадров (быстро)</MenuItem>
                      <MenuItem value={120}>Каждые 120 кадров (очень быстро)</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Максимум кадров</InputLabel>
                    <Select
                      value={maxFrames}
                      label="Максимум кадров"
                      onChange={(e) => setMaxFrames(e.target.value)}
                    >
                      <MenuItem value={5}>5 кадров (быстро)</MenuItem>
                      <MenuItem value={10}>10 кадров (рекомендуется)</MenuItem>
                      <MenuItem value={20}>20 кадров (детально)</MenuItem>
                      <MenuItem value={50}>50 кадров (максимально)</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
              </>
            )}
          </Grid>

          <Box sx={{ mt: 3, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            {fileType === 'video' && (
              <Button
                variant="outlined"
                startIcon={<ScheduleIcon />}
                onClick={handleEstimateProcessing}
                disabled={!selectedFile || isEstimating || isAnalyzing}
              >
                {isEstimating ? 'Оценка...' : 'Оценить время'}
              </Button>
            )}
            
            <Button
              variant="contained"
              size="large"
              startIcon={<PlayArrowIcon />}
              onClick={handleAnalyzeFile}
              disabled={!selectedFile || isAnalyzing}
              color="primary"
            >
              {isAnalyzing ? 'Анализ...' : 'НАЧАТЬ АНАЛИЗ МЕДИАФАЙЛА'}
            </Button>
          </Box>
        </CardContent>
      </Card>

      {/* Processing Estimate */}
      {processingEstimate && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              <ScheduleIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
              Оценка обработки
            </Typography>
            
            <Grid container spacing={2}>
              <Grid item xs={6} sm={3}>
                <Typography variant="body2" color="textSecondary">Длительность видео</Typography>
                <Typography variant="h6">{formatDuration(processingEstimate.video_duration)}</Typography>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography variant="body2" color="textSecondary">Всего кадров</Typography>
                <Typography variant="h6">{processingEstimate.total_frames}</Typography>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography variant="body2" color="textSecondary">К обработке</Typography>
                <Typography variant="h6">{processingEstimate.frames_to_process}</Typography>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography variant="body2" color="textSecondary">Время обработки</Typography>
                <Typography variant="h6" color="primary">
                  ~{Math.ceil(processingEstimate.estimated_processing_time / 60)} мин
                </Typography>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Progress Bar */}
      {isAnalyzing && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Обработка видео...
            </Typography>
            <LinearProgress 
              variant="determinate" 
              value={progress} 
              sx={{ height: 8, borderRadius: 4, mb: 1 }}
            />
            <Typography variant="body2" color="textSecondary">
              {progress < 90 ? `Обработка: ${progress}%` : 'Финализация результатов...'}
            </Typography>
          </CardContent>
        </Card>
      )}

      {/* Analysis Results */}
      {analysisResults && (
        <Box>
          <Typography variant="h5" gutterBottom>
            <AssessmentIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
            Результаты анализа
          </Typography>

          {/* Summary Card */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>Сводка</Typography>
              
              <Grid container spacing={3}>
                <Grid item xs={6} sm={3}>
                  <Typography variant="body2" color="textSecondary">Обработано кадров</Typography>
                  <Typography variant="h6">{analysisResults.total_frames_processed}</Typography>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Typography variant="body2" color="textSecondary">Успешных кадров</Typography>
                  <Typography variant="h6" color="success.main">
                    {analysisResults.successful_frames}
                  </Typography>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Typography variant="body2" color="textSecondary">Объектов найдено</Typography>
                  <Typography variant="h6">{analysisResults.total_objects_detected}</Typography>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Typography variant="body2" color="textSecondary">Точность координат</Typography>
                  <Typography variant="h6" color="primary">
                    {analysisResults.coordinates ? 
                      `${Math.round(analysisResults.coordinates.confidence * 100)}%` : 'N/A'}
                  </Typography>
                </Grid>
              </Grid>

              {analysisResults.coordinates && (
                <Box sx={{ mt: 2 }}>
                  <Chip
                    icon={<LocationOnIcon />}
                    label={`${analysisResults.coordinates.latitude.toFixed(6)}, ${analysisResults.coordinates.longitude.toFixed(6)}`}
                    color="primary"
                    sx={{ mr: 1 }}
                  />
                  <Chip
                    label={`Источник: ${analysisResults.coordinates.source}`}
                    variant="outlined"
                    sx={{ mr: 1 }}
                  />
                  <Chip
                    label={`Кадров: ${analysisResults.coordinates.frame_count}`}
                    variant="outlined"
                  />
                </Box>
              )}
            </CardContent>
          </Card>

          {/* Object Statistics */}
          {analysisResults.object_statistics && (
            <Accordion sx={{ mb: 3 }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="h6">Статистика объектов</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle1" gutterBottom>Категории объектов</Typography>
                    <TableContainer component={Paper} variant="outlined">
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Категория</TableCell>
                            <TableCell align="right">Количество</TableCell>
                            <TableCell align="right">Уверенность</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {Object.entries(analysisResults.object_statistics.category_counts || {}).map(([category, count]) => (
                            <TableRow key={category}>
                              <TableCell>{category}</TableCell>
                              <TableCell align="right">{count}</TableCell>
                              <TableCell align="right">
                                {Math.round((analysisResults.object_statistics.category_avg_confidence[category] || 0) * 100)}%
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle1" gutterBottom>Общая статистика</Typography>
                    <Box sx={{ p: 2, backgroundColor: 'grey.50', borderRadius: 1 }}>
                      <Typography variant="body2">
                        <strong>Уникальных категорий:</strong> {analysisResults.object_statistics.unique_categories}
                      </Typography>
                      <Typography variant="body2">
                        <strong>Средняя полезность для геолокации:</strong> {' '}
                        {Math.round((analysisResults.object_statistics.average_geolocation_utility || 0) * 100)}%
                      </Typography>
                      <Typography variant="body2">
                        <strong>Высокополезных объектов:</strong> {analysisResults.object_statistics.high_utility_objects}
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
              </AccordionDetails>
            </Accordion>
          )}

          {/* Frame Results */}
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">Покадровые результаты</Typography>
              <Tooltip title="Детальная информация по каждому обработанному кадру">
                <IconButton size="small" sx={{ ml: 1 }}>
                  <InfoIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            </AccordionSummary>
            <AccordionDetails>
              <TableContainer component={Paper} variant="outlined">
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Кадр</TableCell>
                      <TableCell>Время</TableCell>
                      <TableCell>Статус</TableCell>
                      <TableCell>Объекты</TableCell>
                      <TableCell>Координаты</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {analysisResults.frame_results?.map((frame, index) => (
                      <TableRow key={index}>
                        <TableCell>{frame.frame_number}</TableCell>
                        <TableCell>{formatDuration(frame.timestamp)}</TableCell>
                        <TableCell>
                          <Chip 
                            label={frame.success ? 'Успех' : 'Ошибка'} 
                            color={frame.success ? 'success' : 'error'}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>{frame.objects?.length || 0}</TableCell>
                        <TableCell>
                          {frame.coordinates ? (
                            <Chip 
                              label={`${frame.coordinates.confidence ? Math.round(frame.coordinates.confidence * 100) : 0}%`}
                              size="small"
                              color="primary"
                            />
                          ) : (
                            <Chip label="Нет" size="small" variant="outlined" />
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </AccordionDetails>
          </Accordion>

          {/* Map View Button */}
          {analysisResults.coordinates && (
            <Box sx={{ mt: 3, textAlign: 'center' }}>
              <Button
                variant="contained"
                startIcon={<MapIcon />}
                onClick={() => {
                  const { latitude, longitude } = analysisResults.coordinates;
                  window.open(`https://yandex.ru/maps/?ll=${longitude},${latitude}&z=15&pt=${longitude},${latitude}`, '_blank');
                }}
              >
                Показать на карте
              </Button>
            </Box>
          )}
        </Box>
      )}
    </Box>
  );
};

export default VideoAnalyzer;
