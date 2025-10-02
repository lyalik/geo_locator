import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useSnackbar } from 'notistack';
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Grid,
  LinearProgress,
  TextField,
  Typography,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
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
  IconButton,
  Tooltip,
  Divider,
  Dialog,
  DialogContent
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
  Map as MapIcon,
  LocationOff as LocationOffIcon,
  OpenInNew as OpenInNewIcon,
  Analytics as AnalyticsIcon
} from '@mui/icons-material';
import { videoAnalysis } from '../services/api';
import InteractiveResultsMap from './InteractiveResultsMap';

/**
 * VideoAnalyzer - Компонент для анализа координат из видео и изображений
 * 
 * Функциональность:
 * - Загрузка и анализ видеофайлов для извлечения координат
 * - Обработка отдельных изображений с геолокационным анализом
 * - Извлечение кадров из видео с заданным интервалом
 * - Интеграция с российскими спутниковыми сервисами (Роскосмос, Яндекс)
 * - Определение местоположения через Яндекс Карты и 2GIS
 * - Отображение результатов на интерактивной карте
 * - Экспорт координатных данных и метаданных
 * - Поддержка подсказок местоположения для улучшения точности
 */
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
  const [previewImage, setPreviewImage] = useState(null);
  const [imageModalOpen, setImageModalOpen] = useState(false);
  const [selectedModalImage, setSelectedModalImage] = useState(null);

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
        // Create preview for image
        const reader = new FileReader();
        reader.onloadend = () => {
          setPreviewImage(reader.result);
        };
        reader.readAsDataURL(file);
      } else if (isVideo) {
        setFileType('video');
        setPreviewImage(null);
      } else {
        setFileType(null);
        setPreviewImage(null);
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
  const analyzeImageCoordinates = async (file, locationHint) => {
    const { coordinateAnalysis } = await import('../services/api');
    const response = await coordinateAnalysis.detectFromPhoto(file, locationHint);
    return response.data; // Извлекаем данные из axios response
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
        const data = await analyzeImageCoordinates(selectedFile, locationHint);
        setProgress(100);

        if (data.success) {
          console.log('🔍 Полученные данные от API:', data);
          console.log('🗺️ Координаты:', data.data.coordinates);
          console.log('📍 Объекты:', data.data.objects);
          console.log('🛰️ Спутниковые данные:', data.data.satellite_data);
          console.log('📍 Информация о местоположении:', data.data.location_info);
          
          // Извлекаем данные из правильной структуры API ответа
          const apiData = data.data;
          const objectsArray = Array.isArray(apiData.objects) ? apiData.objects : [];
          
          const transformedResults = {
            total_frames_processed: 1,
            successful_frames: 1,
            total_objects_detected: objectsArray.length,
            coordinates: apiData.coordinates ? {
              latitude: apiData.coordinates.latitude || apiData.coordinates.lat,
              longitude: apiData.coordinates.longitude || apiData.coordinates.lon,
              confidence: apiData.coordinates.confidence || 1,
              source: apiData.coordinates.source || 'Coordinate Detection',
              frame_count: 1
            } : null,
            // Всегда показываем новый интерфейс, даже если координаты не найдены
            has_analysis_data: true,
            // Добавляем спутниковые данные
            satellite_data: apiData.satellite_data ? {
              source: apiData.satellite_data.primary_source,
              source_name: apiData.satellite_data.primary_source_name,
              image_data: apiData.satellite_data.image_data,
              coordinates: apiData.satellite_data.coordinates,
              available_sources: apiData.satellite_data.available_sources,
              all_sources: apiData.satellite_data.all_sources
            } : null,
            // Добавляем информацию о местоположении
            location_info: apiData.location_info ? {
              coordinates: apiData.location_info.coordinates,
              dgis_data: apiData.location_info.dgis_data,
              nearby_places: apiData.location_info.nearby_places || []
            } : null,
            object_statistics: objectsArray.length > 0 ? {
              category_counts: objectsArray.reduce((acc, obj) => {
                const category = obj.category || obj.class || 'unknown';
                acc[category] = (acc[category] || 0) + 1;
                return acc;
              }, {}),
              category_avg_confidence: objectsArray.reduce((acc, obj) => {
                const category = obj.category || obj.class || 'unknown';
                acc[category] = obj.confidence || 0;
                return acc;
              }, {}),
              unique_categories: [...new Set(objectsArray.map(obj => obj.category || obj.class || 'unknown'))].length,
              average_geolocation_utility: objectsArray.reduce((sum, obj) => sum + (obj.geolocation_utility || 0), 0) / objectsArray.length,
              high_utility_objects: objectsArray.filter(obj => (obj.geolocation_utility || 0) > 0.7).length
            } : null,
            frame_results: [{
              frame_number: 1,
              timestamp: 0,
              success: true,
              objects: objectsArray,
              coordinates: apiData.coordinates,
              satellite_data: apiData.satellite_data,
              location_info: apiData.location_info
            }],
            // Добавляем рекомендации
            recommendations: apiData.recommendations || [],
            // Добавляем источники данных
            sources_used: apiData.sources_used || [],
            // Добавляем источники координат
            coordinate_sources: apiData.coordinate_sources || {}
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

        const response = await videoAnalysis.analyzeVideo(
          selectedFile,
          locationHint,
          frameInterval,
          maxFrames
        );

        clearInterval(progressInterval);
        setProgress(100);

        if (response.data.success) {
          console.log('🎥 Полученные данные анализа видео:', response.data);
          
          // Извлекаем данные из правильной структуры API ответа для видео
          const videoData = response.data.data;
          const objectsArray = Array.isArray(videoData.objects) ? videoData.objects : [];
          
          const transformedVideoResults = {
            total_frames_processed: videoData.total_frames_processed || 0,
            successful_frames: videoData.frame_results ? videoData.frame_results.filter(f => f.success).length : 0,
            total_objects_detected: videoData.total_objects || objectsArray.length,
            processing_time: videoData.processing_time_seconds || 0,
            coordinates: videoData.coordinates ? {
              latitude: videoData.coordinates.latitude || videoData.coordinates.lat,
              longitude: videoData.coordinates.longitude || videoData.coordinates.lon,
              confidence: videoData.coordinates.confidence || 0,
              source: videoData.coordinates.source || 'Video Analysis',
              frame_count: videoData.total_frames_processed || 0
            } : null,
            has_analysis_data: true,
            satellite_data: videoData.satellite_data || null,
            location_info: videoData.location_info || null,
            object_stats: videoData.object_stats || null,
            frame_results: videoData.frame_results || [],
            recommendations: videoData.recommendations || [],
            sources_used: videoData.sources_used || [],
            coordinate_sources: videoData.coordinate_sources || {},
            quality_stats: videoData.quality_stats || null,
            video_info: videoData.video_info || null
          };
          
          setAnalysisResults(transformedVideoResults);
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

      {/* Image Preview */}
      {previewImage && fileType === 'image' && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              📸 Превью изображения
            </Typography>
            <Box 
              sx={{ 
                display: 'flex', 
                justifyContent: 'center',
                cursor: 'pointer',
                '&:hover': {
                  opacity: 0.8
                }
              }}
              onClick={() => {
                setSelectedModalImage(previewImage);
                setImageModalOpen(true);
              }}
            >
              <img 
                src={previewImage} 
                alt="Preview" 
                style={{ 
                  maxWidth: '100%', 
                  maxHeight: '400px',
                  borderRadius: '8px',
                  border: '2px solid #ddd'
                }} 
              />
            </Box>
            <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block', textAlign: 'center' }}>
              Кликните для увеличения
            </Typography>
          </CardContent>
        </Card>
      )}

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
              Обработка...
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

          {/* Uploaded Photo Display */}
          {selectedFile && (
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  📷 Загруженная фотография
                </Typography>
                <Box sx={{ 
                  display: 'flex', 
                  justifyContent: 'center',
                  mb: 2,
                  border: '1px solid #e0e0e0',
                  borderRadius: 1,
                  p: 1,
                  backgroundColor: '#fafafa'
                }}>
                  <img 
                    src={URL.createObjectURL(selectedFile)}
                    alt="Загруженная фотография"
                    style={{ 
                      maxWidth: '100%', 
                      maxHeight: '400px', 
                      objectFit: 'contain',
                      borderRadius: '4px'
                    }}
                  />
                </Box>
                <Typography variant="body2" color="textSecondary" align="center">
                  Файл: {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} МБ)
                </Typography>
              </CardContent>
            </Card>
          )}

          {/* Coordinates Results Card */}
          {analysisResults.coordinates && (
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  📍 Найденные координаты
                </Typography>
                
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Box sx={{ p: 2, bgcolor: 'success.light', borderRadius: 1, mb: 2 }}>
                      <Typography variant="h6" color="success.contrastText" gutterBottom>
                        {analysisResults.coordinates.latitude.toFixed(6)}, {analysisResults.coordinates.longitude.toFixed(6)}
                      </Typography>
                      <Typography variant="body2" color="success.contrastText">
                        Точность: {Math.round(analysisResults.coordinates.confidence * 100)}% • 
                        Источник: {analysisResults.coordinates.source} • 
                        Кадров: {analysisResults.coordinates.frame_count}
                      </Typography>
                    </Box>
                    
                    <Typography variant="subtitle2" gutterBottom>Открыть на картах:</Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                      <Chip 
                        label="Яндекс Карты"
                        clickable
                        color="primary"
                        onClick={() => {
                          const { latitude, longitude } = analysisResults.coordinates;
                          window.open(`https://yandex.ru/maps/?ll=${longitude},${latitude}&z=16&l=map`, '_blank');
                        }}
                      />
                      <Chip 
                        label="2ГИС"
                        clickable
                        variant="outlined"
                        onClick={() => {
                          const { latitude, longitude } = analysisResults.coordinates;
                          window.open(`https://2gis.ru/geo/${latitude},${longitude}/zoom/16`, '_blank');
                        }}
                      />
                      <Chip 
                        label="OpenStreetMap"
                        clickable
                        variant="outlined"
                        onClick={() => {
                          const { latitude, longitude } = analysisResults.coordinates;
                          window.open(`https://www.openstreetmap.org/#map=16/${latitude}/${longitude}`, '_blank');
                        }}
                      />
                      <Chip 
                        label="Google Maps"
                        clickable
                        variant="outlined"
                        onClick={() => {
                          const { latitude, longitude } = analysisResults.coordinates;
                          window.open(`https://www.google.com/maps/@${latitude},${longitude},16z`, '_blank');
                        }}
                      />
                    </Box>
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" gutterBottom>Статистика анализа:</Typography>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2">Обработано кадров:</Typography>
                        <Typography variant="body2" fontWeight="bold">{analysisResults.total_frames_processed}</Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2">Успешных кадров:</Typography>
                        <Typography variant="body2" fontWeight="bold" color="success.main">
                          {analysisResults.successful_frames}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2">Объектов найдено:</Typography>
                        <Typography variant="body2" fontWeight="bold">{analysisResults.total_objects_detected}</Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2">Время анализа:</Typography>
                        <Typography variant="body2" fontWeight="bold">
                          {analysisResults.processing_time ? `${analysisResults.processing_time.toFixed(1)}с` : 'N/A'}
                        </Typography>
                      </Box>
                    </Box>
                  </Grid>
                </Grid>

                {/* Interactive Map */}
                <Grid item xs={12}>
                  <InteractiveResultsMap 
                    coordinates={analysisResults.coordinates}
                    satelliteData={analysisResults.satellite_data}
                    locationInfo={analysisResults.location_info}
                    height={400}
                  />
                </Grid>
              </CardContent>
            </Card>
          )}

          {/* Координатная диагностика */}
          {analysisResults && analysisResults.detection_log && analysisResults.detection_log.length > 0 && (
            <Accordion sx={{ mb: 3 }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <InfoIcon color="primary" />
                  <Typography variant="h6">
                    🔍 Диагностика определения координат
                  </Typography>
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell><strong>Метод</strong></TableCell>
                        <TableCell><strong>Статус</strong></TableCell>
                        <TableCell><strong>Детали</strong></TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {analysisResults.detection_log.map((log, idx) => (
                        <TableRow 
                          key={idx}
                          sx={{ 
                            '&:hover': { bgcolor: 'action.hover' },
                            bgcolor: log.success ? 'success.light' : 'error.light',
                            opacity: log.success ? 1 : 0.7
                          }}
                        >
                          <TableCell>
                            <Typography variant="body2" fontWeight="bold">
                              {log.method}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip 
                              label={log.success ? 'Успешно' : 'Не удалось'}
                              color={log.success ? 'success' : 'error'}
                              size="small"
                              sx={{ fontWeight: 'bold' }}
                            />
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {log.error 
                                ? log.error 
                                : log.details 
                                  ? (typeof log.details === 'string' ? log.details : JSON.stringify(log.details))
                                  : log.objects_count !== undefined 
                                    ? `${log.objects_count} объектов` 
                                    : log.matches_count !== undefined
                                      ? `${log.matches_count} совпадений`
                                      : log.similar_count !== undefined
                                        ? `${log.similar_count} похожих`
                                        : '-'
                              }
                            </Typography>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
                
                {/* Объяснение fallback */}
                {analysisResults.fallback_reason && (
                  <Alert severity="warning" sx={{ mt: 2 }}>
                    <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                      ⚠️ Почему использованы координаты по умолчанию:
                    </Typography>
                    <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit' }}>
                      {analysisResults.fallback_reason}
                    </Typography>
                  </Alert>
                )}
                
                {/* Рекомендации */}
                {analysisResults.recommendations && analysisResults.recommendations.length > 0 && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                      💡 Рекомендации для улучшения точности:
                    </Typography>
                    {analysisResults.recommendations.map((rec, idx) => {
                      const severityMap = {
                        'critical': 'error',
                        'high': 'warning',
                        'medium': 'info',
                        'low': 'success'
                      };
                      return (
                        <Alert 
                          key={idx} 
                          severity={severityMap[rec.priority] || 'info'} 
                          sx={{ mb: 1 }}
                        >
                          <Typography variant="body2" fontWeight="bold">
                            {typeof rec.message === 'string' ? rec.message : JSON.stringify(rec.message)}
                          </Typography>
                          <Typography variant="caption" sx={{ display: 'block', mt: 0.5 }}>
                            {typeof rec.action === 'string' ? rec.action : JSON.stringify(rec.action)}
                          </Typography>
                        </Alert>
                      );
                    })}
                  </Box>
                )}
              </AccordionDetails>
            </Accordion>
          )}

          {/* No Coordinates Found */}
          {!analysisResults.coordinates && (
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Box sx={{ textAlign: 'center', py: 3 }}>
                  <LocationOffIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                  <Typography variant="h6" gutterBottom>
                    Координаты не найдены
                  </Typography>
                  <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                    Не удалось определить местоположение по видео. 
                    Попробуйте видео с более четкими ориентирами или добавьте подсказку о местоположении.
                  </Typography>
                  
                  <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, mt: 2 }}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="body2" color="textSecondary">Обработано кадров</Typography>
                      <Typography variant="h6">{analysisResults.total_frames_processed}</Typography>
                    </Box>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="body2" color="textSecondary">Объектов найдено</Typography>
                      <Typography variant="h6">{analysisResults.total_objects_detected}</Typography>
                    </Box>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          )}

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

          {/* Satellite Imagery Section */}
          {analysisResults.satellite_data && analysisResults.satellite_data.success && (
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  🛰️ Спутниковые снимки
                </Typography>
                
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="body2" color="textSecondary" gutterBottom>
                      Источник: {analysisResults.satellite_data.source_name || analysisResults.satellite_data.source}
                    </Typography>
                    
                    {analysisResults.satellite_data.image_data && (
                      <Box sx={{ 
                        border: '1px solid #ddd', 
                        borderRadius: 1, 
                        overflow: 'hidden',
                        maxWidth: '100%'
                      }}>
                        {analysisResults.satellite_data.image_data.image_url ? (
                          <img 
                            src={analysisResults.satellite_data.image_data.image_url}
                            alt="Спутниковый снимок"
                            style={{ width: '100%', height: 'auto', maxHeight: '300px', objectFit: 'cover' }}
                            onError={(e) => {
                              e.target.style.display = 'none';
                              e.target.nextSibling.style.display = 'block';
                            }}
                          />
                        ) : analysisResults.satellite_data.image_data.image_data ? (
                          <img 
                            src={`data:${analysisResults.satellite_data.image_data.content_type || 'image/jpeg'};base64,${analysisResults.satellite_data.image_data.image_data}`}
                            alt="Спутниковый снимок"
                            style={{ width: '100%', height: 'auto', maxHeight: '300px', objectFit: 'cover' }}
                          />
                        ) : (
                          <Typography variant="body2" color="textSecondary" sx={{ p: 2, textAlign: 'center' }}>
                            Спутниковый снимок недоступен
                          </Typography>
                        )}
                        <Typography 
                          variant="body2" 
                          color="error" 
                          sx={{ p: 2, textAlign: 'center', display: 'none' }}
                        >
                          Ошибка загрузки изображения
                        </Typography>
                      </Box>
                    )}
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" gutterBottom>Информация о снимке:</Typography>
                    <Typography variant="body2">
                      <strong>Координаты:</strong> {analysisResults.coordinates.latitude.toFixed(6)}, {analysisResults.coordinates.longitude.toFixed(6)}
                    </Typography>
                    <Typography variant="body2">
                      <strong>Доступных источников:</strong> {analysisResults.satellite_data.available_sources}
                    </Typography>
                    {analysisResults.satellite_data.image_data.satellite && (
                      <Typography variant="body2">
                        <strong>Спутник:</strong> {analysisResults.satellite_data.image_data.satellite}
                      </Typography>
                    )}
                    {analysisResults.satellite_data.image_data.acquisition_date && (
                      <Typography variant="body2">
                        <strong>Дата съемки:</strong> {new Date(analysisResults.satellite_data.image_data.acquisition_date).toLocaleDateString()}
                      </Typography>
                    )}
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          )}

          {/* Satellite Data Section */}
          {analysisResults.satellite_data && (
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  🛰️ Спутниковые снимки
                </Typography>
                
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" gutterBottom>Доступные источники:</Typography>
                    <Box sx={{ mb: 2 }}>
                      {analysisResults.satellite_data.all_sources ? 
                        analysisResults.satellite_data.all_sources.map((source, index) => (
                          <Chip 
                            key={index}
                            label={source}
                            color={index === 0 ? "primary" : "default"}
                            sx={{ mr: 1, mb: 1 }}
                          />
                        )) : (
                          <Chip 
                            label={analysisResults.satellite_data.source_name || analysisResults.satellite_data.source}
                            color="primary"
                            sx={{ mr: 1, mb: 1 }}
                          />
                        )}
                      <Chip 
                        label="Яндекс Карты"
                        variant="outlined"
                        sx={{ mr: 1, mb: 1 }}
                        onClick={() => {
                          const { latitude, longitude } = analysisResults.coordinates;
                          window.open(`https://yandex.ru/maps/?ll=${longitude},${latitude}&z=16&l=sat`, '_blank');
                        }}
                      />
                      <Chip 
                        label="2ГИС"
                        variant="outlined"
                        sx={{ mr: 1, mb: 1 }}
                        onClick={() => {
                          const { latitude, longitude } = analysisResults.coordinates;
                          window.open(`https://2gis.ru/geo/${latitude},${longitude}/zoom/16`, '_blank');
                        }}
                      />
                      <Chip 
                        label="OpenStreetMap"
                        variant="outlined"
                        sx={{ mr: 1, mb: 1 }}
                        onClick={() => {
                          const { latitude, longitude } = analysisResults.coordinates;
                          window.open(`https://www.openstreetmap.org/#map=16/${latitude}/${longitude}`, '_blank');
                        }}
                      />
                    </Box>
                    
                    <Typography variant="body2" sx={{ mb: 1 }}>
                      <strong>Координаты:</strong> {analysisResults.coordinates.latitude.toFixed(6)}, {analysisResults.coordinates.longitude.toFixed(6)}
                    </Typography>
                    <Typography variant="body2" sx={{ mb: 1 }}>
                      <strong>Доступных источников:</strong> {analysisResults.satellite_data.available_sources}
                    </Typography>
                    {analysisResults.satellite_data.image_data && analysisResults.satellite_data.image_data.satellite && (
                      <Typography variant="body2" sx={{ mb: 1 }}>
                        <strong>Спутник:</strong> {analysisResults.satellite_data.image_data.satellite}
                      </Typography>
                    )}
                  </Grid>
                  
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" gutterBottom>Спутниковый снимок:</Typography>
                    <Box sx={{ textAlign: 'center', p: 2 }}>
                      <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                        Спутниковые снимки доступны через внешние сервисы:
                      </Typography>
                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                        <Button
                          variant="outlined"
                          size="small"
                          onClick={() => {
                            const { latitude, longitude } = analysisResults.coordinates;
                            window.open(`https://yandex.ru/maps/?ll=${longitude},${latitude}&z=16&l=sat`, '_blank');
                          }}
                        >
                          Открыть в Яндекс Картах (спутник)
                        </Button>
                        <Button
                          variant="outlined"
                          size="small"
                          onClick={() => {
                            const { latitude, longitude } = analysisResults.coordinates;
                            window.open(`https://www.google.com/maps/@${latitude},${longitude},16z/data=!3m1!1e3`, '_blank');
                          }}
                        >
                          Открыть в Google Maps (спутник)
                        </Button>
                        <Button
                          variant="outlined"
                          size="small"
                          onClick={() => {
                            const { latitude, longitude } = analysisResults.coordinates;
                            window.open(`https://www.openstreetmap.org/#map=16/${latitude}/${longitude}`, '_blank');
                          }}
                        >
                          Открыть в OpenStreetMap
                        </Button>
                      </Box>
                    </Box>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          )}

          {/* Location Information Section */}
          {analysisResults.location_info && (
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  📍 Информация о местоположении
                </Typography>
                
                <Grid container spacing={3}>
                  {/* Coordinates and Source */}
                  <Grid item xs={12}>
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="subtitle2" gutterBottom>Координаты:</Typography>
                      <Typography variant="h6" color="primary" sx={{ mb: 1 }}>
                        {analysisResults.coordinates ? 
                          `${analysisResults.coordinates.latitude.toFixed(6)}, ${analysisResults.coordinates.longitude.toFixed(6)}` : 
                          'Координаты не определены'
                        }
                      </Typography>
                      {analysisResults.coordinates && (
                        <Chip 
                          label={`Источник: ${analysisResults.coordinates.source}`}
                          color="primary"
                          size="small"
                          sx={{ mr: 1 }}
                        />
                      )}
                      {analysisResults.coordinates && (
                        <Chip 
                          label={`Точность: ${Math.round(analysisResults.coordinates.confidence * 100)}%`}
                          variant="outlined"
                          size="small"
                        />
                      )}
                    </Box>
                  </Grid>

                  {/* Yandex Data */}
                  {analysisResults.location_info.yandex_data && analysisResults.location_info.yandex_data.places && analysisResults.location_info.yandex_data.places.length > 0 && (
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle2" gutterBottom>Данные Яндекс:</Typography>
                      {analysisResults.location_info.yandex_data.places.slice(0, 2).map((place, index) => (
                        <Box key={index} sx={{ mb: 2, p: 2, bgcolor: 'background.paper', borderRadius: 1, border: '1px solid', borderColor: 'divider' }}>
                          <Typography variant="body1" sx={{ fontWeight: 'bold', mb: 1 }}>
                            {place.name}
                          </Typography>
                          <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
                            {place.address}
                          </Typography>
                          {place.description && (
                            <Typography variant="caption" color="textSecondary" sx={{ mb: 1, display: 'block' }}>
                              {place.description}
                            </Typography>
                          )}
                          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                            <Chip 
                              label={place.type || 'Место'}
                              size="small"
                              color="primary"
                            />
                            <Chip 
                              label={place.precision || 'Точность не указана'}
                              size="small"
                              variant="outlined"
                            />
                          </Box>
                        </Box>
                      ))}
                    </Grid>
                  )}
                  
                  {/* 2GIS Data */}
                  {analysisResults.location_info.dgis_data && analysisResults.location_info.dgis_data.places && analysisResults.location_info.dgis_data.places.length > 0 && (
                    <Grid item xs={12} md={6}>
                      <Typography variant="subtitle2" gutterBottom>Данные 2ГИС:</Typography>
                      {analysisResults.location_info.dgis_data.places.slice(0, 2).map((place, index) => (
                        <Box key={index} sx={{ mb: 2, p: 2, bgcolor: 'background.paper', borderRadius: 1, border: '1px solid', borderColor: 'divider' }}>
                          <Typography variant="body1" sx={{ fontWeight: 'bold', mb: 1 }}>
                            {place.name}
                          </Typography>
                          <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
                            {place.address}
                          </Typography>
                          {place.category && (
                            <Chip 
                              label={Array.isArray(place.category) ? place.category.join(', ') : place.category}
                              size="small"
                              color="secondary"
                            />
                          )}
                        </Box>
                      ))}
                    </Grid>
                  )}

                  {/* Reverse Geocoding */}
                  {analysisResults.location_info.reverse_geocoding && analysisResults.location_info.reverse_geocoding.results && analysisResults.location_info.reverse_geocoding.results.length > 0 && (
                    <Grid item xs={12}>
                      <Typography variant="subtitle2" gutterBottom>Обратное геокодирование:</Typography>
                      {analysisResults.location_info.reverse_geocoding.results.slice(0, 1).map((result, index) => (
                        <Box key={index} sx={{ p: 2, bgcolor: 'action.hover', borderRadius: 1 }}>
                          <Typography variant="body1" sx={{ mb: 1 }}>
                            <strong>Адрес:</strong> {result.formatted_address}
                          </Typography>
                          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                            <Chip 
                              label={`Тип: ${result.type}`}
                              size="small"
                              variant="outlined"
                            />
                            <Chip 
                              label={`Точность: ${Math.round(result.confidence * 100)}%`}
                              size="small"
                              color="primary"
                            />
                            <Chip 
                              label={`Источник: ${analysisResults.location_info.reverse_geocoding.source}`}
                              size="small"
                              variant="outlined"
                            />
                          </Box>
                        </Box>
                      ))}
                    </Grid>
                  )}
                  
                  {/* OSM Data */}
                  {analysisResults.location_info.osm_data && (
                    <Grid item xs={12}>
                      <Typography variant="subtitle2" gutterBottom>Данные OpenStreetMap:</Typography>
                      <Typography variant="body2">
                        <strong>Тип местности:</strong> {analysisResults.location_info.osm_data.place_type || 'Не определено'}
                      </Typography>
                      {analysisResults.location_info.osm_data.buildings_count && (
                        <Typography variant="body2">
                          <strong>Зданий поблизости:</strong> {analysisResults.location_info.osm_data.buildings_count}
                        </Typography>
                      )}
                    </Grid>
                  )}
                </Grid>
              </CardContent>
            </Card>
          )}

          {/* Recommendations Section */}
          {analysisResults.recommendations && analysisResults.recommendations.length > 0 && (
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  💡 Рекомендации
                </Typography>
                {analysisResults.recommendations.map((recommendation, index) => (
                  <Box key={index} sx={{ mb: 1, display: 'flex', alignItems: 'flex-start' }}>
                    <InfoIcon sx={{ mr: 1, mt: 0.5, fontSize: 16, color: 'info.main' }} />
                    <Typography variant="body2">
                      {typeof recommendation === 'string' 
                        ? recommendation 
                        : typeof recommendation === 'object' && recommendation.message 
                          ? recommendation.message 
                          : JSON.stringify(recommendation)}
                    </Typography>
                  </Box>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Sources Used Section */}
          {analysisResults.sources_used && analysisResults.sources_used.length > 0 && (
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  📡 Использованные источники данных
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {analysisResults.sources_used.map((source, index) => (
                    <Chip 
                      key={index}
                      label={source}
                      variant="outlined"
                      color="primary"
                    />
                  ))}
                </Box>
              </CardContent>
            </Card>
          )}

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

      {/* Image Modal for Zoom */}
      <Dialog
        open={imageModalOpen}
        onClose={() => setImageModalOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <Box sx={{ bgcolor: 'black', position: 'relative' }}>
          <IconButton
            onClick={() => setImageModalOpen(false)}
            sx={{
              position: 'absolute',
              right: 8,
              top: 8,
              color: 'white',
              bgcolor: 'rgba(0,0,0,0.5)',
              '&:hover': {
                bgcolor: 'rgba(0,0,0,0.7)',
              },
              zIndex: 1
            }}
          >
            <InfoIcon />
          </IconButton>
          {selectedModalImage && (
            <img
              src={selectedModalImage}
              alt="Увеличенное изображение"
              style={{
                width: '100%',
                height: 'auto',
                display: 'block'
              }}
            />
          )}
        </Box>
      </Dialog>
    </Box>
  );
};

export default VideoAnalyzer;
