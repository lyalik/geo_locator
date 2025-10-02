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
  Paper,
  CircularProgress
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
  Map as MapIcon,
  FolderZip as ZipIcon
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import { useSnackbar } from 'notistack';
import JSZip from 'jszip';
import { videoAnalysis, imageAnalysis } from '../services/api';
import InteractiveResultsMap from './InteractiveResultsMap';
import ValidationDisplay from './ValidationDisplay';

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
  const [isExtractingZip, setIsExtractingZip] = useState(false);

  // Распаковка ZIP архива
  const extractZipFile = async (zipFile) => {
    try {
      setIsExtractingZip(true);
      enqueueSnackbar(`Распаковка архива ${zipFile.name}...`, { variant: 'info' });
      
      const zip = new JSZip();
      const zipData = await zip.loadAsync(zipFile);
      
      const imageFiles = [];
      const supportedExtensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif', '.webp'];
      
      // Извлекаем все изображения из архива
      for (const [filename, file] of Object.entries(zipData.files)) {
        if (!file.dir) {
          const ext = filename.toLowerCase().substring(filename.lastIndexOf('.'));
          if (supportedExtensions.includes(ext)) {
            try {
              const blob = await file.async('blob');
              const imageFile = new File([blob], filename, { type: `image/${ext.substring(1)}` });
              imageFiles.push(imageFile);
            } catch (err) {
              console.error(`Error extracting ${filename}:`, err);
            }
          }
        }
      }
      
      setIsExtractingZip(false);
      
      if (imageFiles.length === 0) {
        enqueueSnackbar('В архиве не найдено изображений', { variant: 'warning' });
        return [];
      }
      
      enqueueSnackbar(`Извлечено ${imageFiles.length} изображений из архива`, { variant: 'success' });
      return imageFiles;
      
    } catch (error) {
      setIsExtractingZip(false);
      enqueueSnackbar(`Ошибка распаковки архива: ${error.message}`, { variant: 'error' });
      console.error('ZIP extraction error:', error);
      return [];
    }
  };

  // Обработка загрузки файлов
  const onDrop = useCallback(async (acceptedFiles) => {
    let allFiles = [];
    
    // Обрабатываем каждый файл
    for (const file of acceptedFiles) {
      if (file.name.toLowerCase().endsWith('.zip')) {
        // Распаковываем ZIP архив
        const extractedFiles = await extractZipFile(file);
        allFiles = [...allFiles, ...extractedFiles];
      } else {
        allFiles.push(file);
      }
    }
    
    const newFiles = allFiles.map((file, index) => ({
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
      'image/*': ['.jpg', '.jpeg', '.png', '.bmp', '.tiff'],
      'application/zip': ['.zip'],
      'application/x-zip-compressed': ['.zip']
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
    const startTime = Date.now();
    const file = fileData.file || fileData; // Извлекаем сырой File объект
    console.log(`🔍 Starting analysis of ${file.name} (${(file.size / 1024 / 1024).toFixed(1)} MB)`);
    
    try {
      // Определяем тип файла по расширению, если MIME-type недоступен
      const fileName = file.name.toLowerCase();
      const isImage = file.type.startsWith('image/') || 
                     fileName.endsWith('.jpg') || fileName.endsWith('.jpeg') || 
                     fileName.endsWith('.png') || fileName.endsWith('.gif') || 
                     fileName.endsWith('.bmp') || fileName.endsWith('.webp');
      const isVideo = file.type.startsWith('video/') || 
                     fileName.endsWith('.mp4') || fileName.endsWith('.avi') || 
                     fileName.endsWith('.mov') || fileName.endsWith('.mkv') || 
                     fileName.endsWith('.webm') || fileName.endsWith('.flv');
      
      // Увеличиваем timeout для видео до 5 минут, для изображений оставляем 2 минуты
      const timeoutDuration = isVideo ? 300000 : 120000; // 5 мин для видео, 2 мин для фото
      const timeoutMessage = isVideo ? 'Превышено время ожидания анализа видео (5 мин)' : 'Превышено время ожидания анализа изображения (2 мин)';
      
      const timeoutPromise = new Promise((_, reject) =>
        setTimeout(() => reject(new Error(timeoutMessage)), timeoutDuration)
      );
      
      let result;
      
      if (isImage) {
        const analysisPromise = imageAnalysis.detectFromPhoto(file, locationHint || '');
        result = await Promise.race([analysisPromise, timeoutPromise]);
      } else if (isVideo) {
        // Используем настройки пользователя для видео
        console.log(`🎥 Video analysis with frameInterval=${frameInterval}, maxFrames=${maxFrames}`);
        const analysisPromise = videoAnalysis.analyzeVideo(file, locationHint || '', frameInterval, maxFrames);
        result = await Promise.race([analysisPromise, timeoutPromise]);
      } else {
        throw new Error(`Неподдерживаемый тип файла: ${fileName}. Поддерживаются изображения (jpg, png, gif, bmp, webp) и видео (mp4, avi, mov, mkv, webm, flv)`);
      }
      
      const duration = ((Date.now() - startTime) / 1000).toFixed(1);
      console.log(`✅ Analysis completed in ${duration}s:`, result);
      
      return {
        success: true,
        data: result,
        duration: parseFloat(duration)
      };
    } catch (error) {
      const duration = ((Date.now() - startTime) / 1000).toFixed(1);
      console.error(`❌ Analysis failed after ${duration}s:`, error);
      return {
        success: false,
        error: error.message,
        duration: parseFloat(duration)
      };
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
      console.log(`📊 Processing file ${i + 1}/${pendingFiles.length}: ${fileData.file?.name || fileData.name}`);
      
      // Обновляем статус файла на "analyzing"
      setFiles(prev => prev.map(f => 
        f.id === fileData.id ? { ...f, status: 'analyzing' } : f
      ));
      
      try {
        const result = await analyzeFile(fileData);
        results.push(result);
        
        // Логируем структуру результата для отладки
        console.log(`🔍 Result structure for ${fileData.file?.name || fileData.name}:`, {
          success: result.success,
          data: result.data,
          hasCoordinates: result.data?.data?.data?.coordinates ? 'YES' : 'NO',
          coordinates: result.data?.data?.data?.coordinates,
          fullData: result.data?.data
        });

        // Обновляем файл с результатом
        setFiles(prev => prev.map(f => 
          f.id === fileData.id ? { 
            ...f, 
            status: result.success ? 'completed' : 'error',
            result: result.success ? result.data?.data : null,
            error: result.success ? null : result.error,
            progress: 100
          } : f
        ));
        
        console.log(`✅ File ${i + 1} processed successfully`);
      } catch (error) {
        console.error(`❌ Error processing file ${i + 1}:`, error);
        const errorResult = {
          success: false,
          error: error.message,
          duration: 0
        };
        results.push(errorResult);
        
        // Обновляем файл с ошибкой
        setFiles(prev => prev.map(f => 
          f.id === fileData.id ? { 
            ...f, 
            status: 'error',
            error: error.message,
            progress: 100
          } : f
        ));
      }
      
      // Обновляем общий прогресс
      const progress = ((i + 1) / pendingFiles.length) * 100;
      setOverallProgress(progress);
      console.log(`📊 Progress: ${progress.toFixed(1)}% (${i + 1}/${pendingFiles.length})`);
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
    const withCoordinates = files.filter(f => f.result?.data?.coordinates).length;
    
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
          <Typography variant="h6" gutterBottom>
            Настройки анализа
          </Typography>
          
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Подсказка местоположения"
                value={locationHint}
                onChange={(e) => setLocationHint(e.target.value)}
                placeholder="Например: Москва, Россия"
                helperText="Поможет улучшить точность определения координат"
              />
            </Grid>
            
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel>Интервал кадров (видео)</InputLabel>
                <Select
                  value={frameInterval}
                  onChange={(e) => setFrameInterval(e.target.value)}
                  label="Интервал кадров (видео)"
                >
                  <MenuItem value={15}>Каждый 15-й кадр (быстро)</MenuItem>
                  <MenuItem value={30}>Каждый 30-й кадр (оптимально)</MenuItem>
                  <MenuItem value={60}>Каждый 60-й кадр (экономно)</MenuItem>
                  <MenuItem value={90}>Каждый 90-й кадр (очень быстро)</MenuItem>
                </Select>
              </FormControl>
              <Typography variant="caption" color="textSecondary" sx={{ mt: 0.5, display: 'block' }}>
                Меньше интервал = больше кадров = точнее, но дольше
              </Typography>
            </Grid>
            
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel>Макс. кадров (видео)</InputLabel>
                <Select
                  value={maxFrames}
                  onChange={(e) => setMaxFrames(e.target.value)}
                  label="Макс. кадров (видео)"
                >
                  <MenuItem value={5}>5 кадров (~10-15 сек)</MenuItem>
                  <MenuItem value={10}>10 кадров (~20-30 сек)</MenuItem>
                  <MenuItem value={20}>20 кадров (~40-60 сек)</MenuItem>
                  <MenuItem value={30}>30 кадров (~1-1.5 мин)</MenuItem>
                </Select>
              </FormControl>
              <Typography variant="caption" color="textSecondary" sx={{ mt: 0.5, display: 'block' }}>
                Примерное время обработки видео
              </Typography>
            </Grid>
          </Grid>
          
          {/* Информация о настройках видео */}
          <Alert severity="warning" sx={{ mt: 2 }}>
            <Typography variant="body2">
              <strong>⚠️ Важно: Ограничение длительности видео</strong>
            </Typography>
            <Typography variant="caption" component="div" sx={{ mt: 0.5 }}>
              • Максимальная длительность видео: <strong>10 секунд</strong>
            </Typography>
            <Typography variant="caption" component="div">
              • Этого достаточно для качественного анализа объекта
            </Typography>
            <Typography variant="caption" component="div">
              • Для длинных видео используйте обрезку или несколько коротких фрагментов
            </Typography>
          </Alert>
          
          <Alert severity="info" sx={{ mt: 1 }}>
            <Typography variant="body2">
              <strong>💡 Рекомендации для видео:</strong>
            </Typography>
            <Typography variant="caption" component="div">
              • Для быстрого анализа: интервал 60, макс. 5 кадров
            </Typography>
            <Typography variant="caption" component="div">
              • Для точного анализа: интервал 30, макс. 10 кадров
            </Typography>
            <Typography variant="caption" component="div">
              • Изображения обрабатываются сразу, настройки не влияют
            </Typography>
          </Alert>
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
            {isExtractingZip ? (
              <>
                <CircularProgress sx={{ mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  Распаковка ZIP архива...
                </Typography>
              </>
            ) : (
              <>
                <UploadIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  {isDragActive ? 'Отпустите файлы здесь' : 'Перетащите файлы сюда или нажмите для выбора'}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Поддерживаются видео (MP4, AVI, MOV), изображения (JPG, PNG, BMP, TIFF) и ZIP архивы
                </Typography>
                <Box sx={{ mt: 2, display: 'flex', gap: 1, justifyContent: 'center', flexWrap: 'wrap' }}>
                  <Chip icon={<ImageIcon />} label="Изображения" size="small" />
                  <Chip icon={<VideoIcon />} label="Видео" size="small" />
                  <Chip icon={<ZipIcon />} label="ZIP архивы" size="small" color="primary" />
                </Box>
              </>
            )}
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
                    <Box sx={{ flex: 1, minWidth: 0 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                        <Typography variant="body1" sx={{ fontWeight: 500 }}>{fileData.name}</Typography>
                        {fileData.status === 'completed' && <CheckIcon color="success" />}
                        {fileData.status === 'error' && <ErrorIcon color="error" />}
                        {currentAnalyzing === fileData.id && (
                          <Chip size="small" label="Анализируется..." color="primary" />
                        )}
                      </Box>
                      <Box sx={{ color: 'text.secondary', fontSize: '0.875rem', mb: 1 }}>
                        {(fileData.size / 1024 / 1024).toFixed(1)} MB • {fileData.type}
                        {fileData.type === 'video' && (
                          <Chip 
                            label={`${frameInterval} кадр, макс ${maxFrames}`} 
                            size="small" 
                            sx={{ ml: 1 }} 
                          />
                        )}
                      </Box>
                      {fileData.status === 'analyzing' && (
                        <Box>
                          <LinearProgress sx={{ mb: 1 }} />
                          {fileData.type === 'video' && (
                            <Typography variant="caption" color="primary">
                              🎥 Обработка видео... Извлечение и анализ кадров
                            </Typography>
                          )}
                        </Box>
                      )}
                      {fileData.status === 'error' && (
                        <Alert severity="error" sx={{ mb: 1 }}>
                          {fileData.error}
                        </Alert>
                      )}
                      {fileData.result?.data?.coordinates && (
                        <Box sx={{ color: 'success.main', fontSize: '0.875rem' }}>
                          📍 Координаты найдены: {fileData.result.data.coordinates.latitude.toFixed(4)}, {fileData.result.data.coordinates.longitude.toFixed(4)}
                          {fileData.type === 'video' && fileData.result?.data?.total_frames_processed && (
                            <Typography variant="caption" display="block" sx={{ color: 'text.secondary', mt: 0.5 }}>
                              🎬 Обработано кадров: {fileData.result.data.total_frames_processed} • 
                              Точность: {Math.round(fileData.result.data.coordinates.confidence * 100)}%
                            </Typography>
                          )}
                        </Box>
                      )}
                      {/* Отображение нарушений с типами заказчика */}
                      {fileData.result?.violations && fileData.result.violations.length > 0 && (
                        <Box sx={{ mt: 1 }}>
                          <Typography variant="caption" color="text.secondary" display="block">
                            Нарушения:
                          </Typography>
                          {fileData.result.violations.slice(0, 3).map((violation, idx) => {
                            const customerType = violation.customer_type || violation.label;
                            const customerTypeText = customerType === '18-001' ? 'Строительная площадка' : 
                                                     customerType === '00-022' ? 'Нарушения недвижимости' : '';
                            return (
                              <Box key={idx} sx={{ display: 'flex', alignItems: 'center', gap: 0.5, ml: 1, mt: 0.5 }}>
                                <Typography variant="caption">
                                  • {violation.category} ({Math.round(violation.confidence * 100)}%)
                                </Typography>
                                {customerType && (
                                  <Chip
                                    label={customerType}
                                    size="small"
                                    color={customerType === '18-001' ? 'warning' : 'info'}
                                    sx={{ height: 16, fontSize: '0.6rem' }}
                                  />
                                )}
                              </Box>
                            );
                          })}
                          {fileData.result.violations.length > 3 && (
                            <Typography variant="caption" color="text.secondary" sx={{ ml: 1, display: 'block', mt: 0.5 }}>
                              ... и ещё {fileData.result.violations.length - 3}
                            </Typography>
                          )}
                        </Box>
                      )}
                      {/* Краткая информация о валидации */}
                      {fileData.result?.validation && (
                        <Box sx={{ mt: 1, ml: 1 }}>
                          <Chip
                            label={fileData.result.validation.validated ? '✅ Валидировано' : '⚠️ Не валидировано'}
                            size="small"
                            color={fileData.result.validation.validated ? 'success' : 'warning'}
                            sx={{ height: 18, fontSize: '0.65rem' }}
                          />
                          {fileData.result.reference_matches && fileData.result.reference_matches.length > 0 && (
                            <Chip
                              label={`📋 ${fileData.result.reference_matches.length} совпадений`}
                              size="small"
                              color="info"
                              sx={{ height: 18, fontSize: '0.65rem', ml: 0.5 }}
                            />
                          )}
                        </Box>
                      )}
                      
                      {/* Детальная информация (для изображений И видео с результатами) */}
                      {fileData.status === 'completed' && fileData.result?.data && (
                        <Accordion sx={{ mt: 2 }}>
                          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                            <Typography variant="body2">
                              📊 Детальные результаты анализа
                              {fileData.type === 'video' && fileData.result?.data?.total_frames_processed && (
                                <Chip 
                                  label={`${fileData.result.data.total_frames_processed} кадров`} 
                                  size="small" 
                                  sx={{ ml: 1 }} 
                                />
                              )}
                            </Typography>
                          </AccordionSummary>
                          <AccordionDetails>
                            {/* Информация о видео кадрах */}
                            {fileData.type === 'video' && fileData.result?.data?.frames_analyzed && (
                              <Box sx={{ mb: 2, p: 1.5, bgcolor: 'info.light', borderRadius: 1 }}>
                                <Typography variant="subtitle2" gutterBottom>
                                  🎬 Анализ видео по кадрам:
                                </Typography>
                                <Typography variant="caption" display="block">
                                  • Всего кадров обработано: {fileData.result.data.total_frames_processed || fileData.result.data.frames_analyzed.length}
                                </Typography>
                                <Typography variant="caption" display="block">
                                  • Кадров с координатами: {fileData.result.data.frames_with_coordinates || 0}
                                </Typography>
                                <Typography variant="caption" display="block">
                                  • Итоговая точность: {Math.round((fileData.result.data.coordinates?.confidence || 0) * 100)}%
                                </Typography>
                              </Box>
                            )}
                            
                            {/* Источники координат */}
                            {fileData.result.data.sources_details && fileData.result.data.sources_details.length > 0 && (
                              <Box sx={{ mb: 2 }}>
                                <Typography variant="subtitle2" gutterBottom>
                                  📍 Источники координат:
                                </Typography>
                                {fileData.result.data.sources_details.map((source, idx) => (
                                  <Box key={idx} sx={{ 
                                    mt: 1, 
                                    p: 1.5, 
                                    borderLeft: '4px solid',
                                    borderColor: source.status === 'success' ? 'success.main' : 'grey.400',
                                    bgcolor: source.status === 'success' ? 'success.lighter' : 'grey.50',
                                    borderRadius: 1
                                  }}>
                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                                      <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                                        {source.icon} {source.name}
                                      </Typography>
                                      <Chip 
                                        label={source.status === 'success' ? '✅ Успешно' : '❌ Не найдено'} 
                                        size="small" 
                                        color={source.status === 'success' ? 'success' : 'default'}
                                        sx={{ height: 18, fontSize: '0.6rem' }}
                                      />
                                    </Box>
                                    
                                    {/* Что нашли */}
                                    {source.details && (
                                      <Box sx={{ mt: 1, p: 1, bgcolor: 'background.paper', borderRadius: 0.5 }}>
                                        <Typography variant="caption" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                                          🔍 Что нашли:
                                        </Typography>
                                        <Typography variant="caption" display="block" color="text.secondary" sx={{ mt: 0.5 }}>
                                          {source.details}
                                        </Typography>
                                      </Box>
                                    )}
                                    
                                    {/* Найденный текст/данные */}
                                    {source.text && (
                                      <Box sx={{ mt: 1, p: 1, bgcolor: 'background.paper', borderRadius: 0.5 }}>
                                        <Typography variant="caption" sx={{ fontWeight: 'bold', color: 'info.main' }}>
                                          📝 Распознанный текст:
                                        </Typography>
                                        <Typography variant="caption" display="block" sx={{ mt: 0.5, fontFamily: 'monospace' }}>
                                          "{source.text}"
                                        </Typography>
                                      </Box>
                                    )}
                                    
                                    {/* Через какой сервис */}
                                    {source.service && (
                                      <Typography variant="caption" display="block" sx={{ mt: 1, color: 'text.secondary' }}>
                                        🔧 Сервис: <strong>{source.service}</strong>
                                      </Typography>
                                    )}
                                    
                                    {/* Точность */}
                                    {source.confidence > 0 && (
                                      <Typography variant="caption" display="block" color="primary" sx={{ mt: 0.5 }}>
                                        📊 Точность: <strong>{Math.round(source.confidence * 100)}%</strong>
                                      </Typography>
                                    )}
                                    
                                    {/* Координаты */}
                                    {source.coordinates && source.coordinates.lat && (
                                      <Typography variant="caption" display="block" color="success.main" sx={{ mt: 0.5, fontWeight: 'bold' }}>
                                        📍 Координаты: {source.coordinates.lat.toFixed(6)}, {source.coordinates.lon.toFixed(6)}
                                      </Typography>
                                    )}
                                    
                                    {/* Дополнительная информация */}
                                    {source.message && (
                                      <Typography variant="caption" display="block" sx={{ mt: 1, fontStyle: 'italic', color: 'text.secondary' }}>
                                        💬 {source.message}
                                      </Typography>
                                    )}
                                  </Box>
                                ))}
                              </Box>
                            )}
                            
                            {/* Обнаруженные объекты */}
                            {fileData.result.data.objects && fileData.result.data.objects.length > 0 && (
                              <Box sx={{ mb: 2 }}>
                                <Typography variant="subtitle2" gutterBottom>
                                  🎯 Обнаруженные объекты ({fileData.result.data.objects.length}):
                                </Typography>
                                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 1 }}>
                                  {fileData.result.data.objects.slice(0, 10).map((obj, idx) => (
                                    <Chip
                                      key={idx}
                                      label={`${obj.category || obj.label} (${Math.round((obj.confidence || 0) * 100)}%)`}
                                      size="small"
                                      variant="outlined"
                                    />
                                  ))}
                                  {fileData.result.data.objects.length > 10 && (
                                    <Chip label={`+${fileData.result.data.objects.length - 10} еще`} size="small" />
                                  )}
                                </Box>
                              </Box>
                            )}
                            
                            {/* Спутниковые снимки */}
                            {fileData.result.data.satellite_data && (
                              <Box sx={{ mb: 2 }}>
                                <Typography variant="subtitle2" gutterBottom>
                                  🛰️ Спутниковые снимки:
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  Источник: {fileData.result.data.satellite_data.source || 'Неизвестно'}
                                </Typography>
                              </Box>
                            )}
                          </AccordionDetails>
                        </Accordion>
                      )}
                    </Box>
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
              .filter(f => f.result?.data?.coordinates)
              .map(fileData => (
                <Box key={fileData.id} sx={{ mb: 3 }}>
                  <Typography variant="subtitle1" gutterBottom>
                    {fileData.name}
                  </Typography>
                  <InteractiveResultsMap
                    coordinates={fileData.result.data.coordinates}
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
                        {fileData.result?.data?.coordinates ? (
                          `${fileData.result.data.coordinates.latitude.toFixed(4)}, ${fileData.result.data.coordinates.longitude.toFixed(4)}`
                        ) : (
                          '—'
                        )}
                      </TableCell>
                      <TableCell>
                        {fileData.result?.data?.confidence ? 
                          `${Math.round(fileData.result.data.confidence * 100)}%` : 
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
            
            {/* Детальная валидация для каждого файла */}
            {files.filter(f => f.result?.validation || f.result?.reference_matches).length > 0 && (
              <Box sx={{ mt: 3 }}>
                <Typography variant="h6" gutterBottom>
                  🔍 Валидация по готовой базе заказчика
                </Typography>
                {files
                  .filter(f => f.result?.validation || f.result?.reference_matches)
                  .map((fileData, idx) => (
                    <Box key={fileData.id} sx={{ mb: 3 }}>
                      <Typography variant="subtitle1" gutterBottom fontWeight="bold">
                        📄 {fileData.name}
                      </Typography>
                      <ValidationDisplay
                        validation={fileData.result.validation}
                        referenceMatches={fileData.result.reference_matches}
                      />
                    </Box>
                  ))
                }
              </Box>
            )}
          </AccordionDetails>
        </Accordion>
      )}
    </Box>
  );
};

export default BatchAnalyzer;
