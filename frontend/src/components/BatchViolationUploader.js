import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Box, Button, Typography, Paper, CircularProgress, Grid, Card, CardContent, 
  TextField, LinearProgress, IconButton, Chip, Alert,  Switch, FormControlLabel
} from '@mui/material';
import {
  CloudUpload as UploadIcon, Image as ImageIcon, Delete as DeleteIcon,
  CheckCircle as CheckIcon, Error as ErrorIcon, Schedule as ScheduleIcon,
  GetApp as DownloadIcon, Satellite as SatelliteIcon,
  Analytics as AnalyticsIcon
} from '@mui/icons-material';
import { api } from '../services/api';

const BatchViolationUploader = ({ onUploadComplete, maxFiles = 20 }) => {
  const [files, setFiles] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [completedUploads, setCompletedUploads] = useState([]);
  const [locationHint, setLocationHint] = useState('');
  const [globalProgress, setGlobalProgress] = useState(0);
  const [enableSatelliteAnalysis, setEnableSatelliteAnalysis] = useState(true);
  const [enableGeoAnalysis, setEnableGeoAnalysis] = useState(true);
  const [satelliteDataCache, setSatelliteDataCache] = useState({});

  const onDrop = useCallback(acceptedFiles => {
    const imageFiles = acceptedFiles.filter(file => file.type.startsWith('image/'));
    const newFiles = imageFiles
      .slice(0, maxFiles - files.length)
      .map(file => Object.assign(file, {
        id: Math.random().toString(36).substr(2, 9),
        preview: URL.createObjectURL(file),
        status: 'pending', // pending, processing, completed, error
        progress: 0,
        result: null,
        error: null
      }));

    setFiles(prevFiles => [...prevFiles, ...newFiles]);
  }, [files.length, maxFiles]);

  const removeFile = (fileId) => {
    setFiles(prevFiles => {
      const updatedFiles = prevFiles.filter(f => f.id !== fileId);
      // Clean up preview URLs
      const fileToRemove = prevFiles.find(f => f.id === fileId);
      if (fileToRemove?.preview) {
        URL.revokeObjectURL(fileToRemove.preview);
      }
      return updatedFiles;
    });
  };

  const processFiles = async () => {
    if (files.length === 0) return;

    setIsProcessing(true);
    setGlobalProgress(0);

    const results = [];
    
    for (let i = 0; i < files.length; i++) {
      const fileItem = files[i];
      
      // Update file status to processing
      setFiles(prevFiles => 
        prevFiles.map(f => 
          f.id === fileItem.id ? { ...f, status: 'processing', progress: 0 } : f
        )
      );

      try {
        const result = await uploadSingleFile(fileItem, (progress) => {
          setFiles(prevFiles => 
            prevFiles.map(f => 
              f.id === fileItem.id ? { ...f, progress } : f
            )
          );
        });

        // Update file status to completed
        setFiles(prevFiles => 
          prevFiles.map(f => 
            f.id === fileItem.id ? { 
              ...f, 
              status: 'completed', 
              progress: 100, 
              result 
            } : f
          )
        );

        results.push(result);
      } catch (error) {
        // Update file status to error
        setFiles(prevFiles => 
          prevFiles.map(f => 
            f.id === fileItem.id ? { 
              ...f, 
              status: 'error', 
              error: error.message 
            } : f
          )
        );
      }

      // Update global progress
      setGlobalProgress(((i + 1) / files.length) * 100);
    }

    setCompletedUploads(results);
    setIsProcessing(false);
    
    if (onUploadComplete) {
      onUploadComplete(results);
    }
  };

  const loadSatelliteData = async (lat, lon) => {
    const cacheKey = `${lat.toFixed(4)},${lon.toFixed(4)}`;
    if (satelliteDataCache[cacheKey]) {
      return satelliteDataCache[cacheKey];
    }

    try {
      const bbox = `${lon - 0.01},${lat - 0.01},${lon + 0.01},${lat + 0.01}`;
      const params = new URLSearchParams({
        bbox,
        date_from: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        date_to: new Date().toISOString().split('T')[0],
        resolution: 10,
        max_cloud_coverage: 20
      });
      
      const response = await api.get(`/api/satellite/image?${params}`);
      
      if (response.data.success) {
        setSatelliteDataCache(prev => ({
          ...prev,
          [cacheKey]: response.data.data
        }));
        return response.data.data;
      }
    } catch (error) {
      console.error('Error loading satellite data:', error);
    }
    return null;
  };

  const uploadSingleFile = async (fileItem, onProgress) => {
    // fileItem is now the actual File object with added properties
    const actualFile = fileItem;
    
    const formData = new FormData();
    formData.append('file', actualFile);
    formData.append('location_hint', locationHint);
    formData.append('user_id', 'current_user_id'); // Replace with actual user ID

    // Debug logging
    console.log('BatchUploader - Processing file:', actualFile.name, 'Size:', actualFile.size, 'Type:', actualFile.type);
    console.log('BatchUploader - FormData entries:', [...formData.entries()]);

    return new Promise(async (resolve, reject) => {
      const xhr = new XMLHttpRequest();

      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable) {
          const progress = (event.loaded / event.total) * 50; // Upload is 50% of total progress
          onProgress(progress);
        }
      });

      xhr.addEventListener('load', async () => {
        if (xhr.status === 200) {
          try {
            const response = JSON.parse(xhr.responseText);
            console.log('BatchUploader - API Response:', response);
            onProgress(75);
            
            // Добавляем спутниковые данные если включен анализ
            if (enableSatelliteAnalysis && response.success && response.data?.location?.coordinates) {
              const satelliteData = await loadSatelliteData(
                response.data.location.coordinates.latitude, 
                response.data.location.coordinates.longitude
              );
              if (satelliteData) {
                response.data.satellite_data = satelliteData;
              }
            }
            
            onProgress(100);
            
            // Return processed result with proper structure
            const processedResult = {
              ...response.data,
              image: response.data?.image_path || response.data?.annotated_image_path || fileItem.preview,
              violations: response.data?.violations || [],
              location: response.data?.location || {},
              metadata: response.data?.metadata || {}
            };
            
            console.log('BatchUploader - Processed result:', processedResult);
            resolve(processedResult);
          } catch (error) {
            console.error('BatchUploader - Response parsing error:', error);
            reject(new Error('Ошибка обработки ответа сервера'));
          }
        } else {
          console.error('BatchUploader - Server error:', xhr.status, xhr.responseText);
          reject(new Error(`Ошибка сервера: ${xhr.status}`));
        }
      });

      xhr.addEventListener('error', () => {
        reject(new Error('Ошибка сети'));
      });

      // Simulate processing progress (second 50%)
      xhr.addEventListener('loadend', () => {
        if (xhr.status === 200) {
          let processingProgress = 50;
          const processingInterval = setInterval(() => {
            processingProgress += 10;
            onProgress(processingProgress);
            if (processingProgress >= 100) {
              clearInterval(processingInterval);
            }
          }, 200);
        }
      });

      xhr.open('POST', 'http://localhost:5000/api/violations/detect');
      xhr.send(formData);
    });
  };

  const clearAll = () => {
    files.forEach(file => {
      if (file.preview) {
        URL.revokeObjectURL(file.preview);
      }
    });
    setFiles([]);
    setCompletedUploads([]);
    setGlobalProgress(0);
  };

  const exportResults = () => {
    const dataStr = JSON.stringify(completedUploads, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `batch_upload_results_${new Date().toISOString().split('T')[0]}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {'image/*': ['.jpeg', '.jpg', '.png', '.gif']},
    maxFiles: maxFiles - files.length,
    multiple: true,
    disabled: isProcessing
  });

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return <CheckIcon color="success" />;
      case 'error': return <ErrorIcon color="error" />;
      case 'processing': return <CircularProgress size={20} />;
      default: return <ScheduleIcon color="action" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'success';
      case 'error': return 'error';
      case 'processing': return 'primary';
      default: return 'default';
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Пакетная загрузка нарушений
      </Typography>

      {/* Upload Area */}
      <Paper 
        variant="outlined" 
        sx={{ 
          p: 3, 
          border: '2px dashed',
          borderColor: isDragActive ? 'primary.main' : 'divider',
          backgroundColor: isDragActive ? 'action.hover' : 'background.paper',
          cursor: isProcessing ? 'not-allowed' : 'pointer',
          opacity: isProcessing ? 0.6 : 1,
          mb: 3
        }}
        {...getRootProps()}
      >
        <input {...getInputProps()} />
        
        <Box textAlign="center">
          <UploadIcon sx={{ fontSize: 48, mb: 1, color: 'primary.main' }} />
          <Typography variant="h6" gutterBottom>
            {isDragActive ? 'Отпустите файлы здесь' : 'Перетащите изображения или нажмите для выбора'}
          </Typography>
          <Typography variant="body2" color="textSecondary" paragraph>
            Поддерживаются: JPG, PNG, GIF. Максимум {maxFiles} файлов
          </Typography>
          <Button variant="contained" startIcon={<ImageIcon />} disabled={isProcessing}>
            Выбрать файлы
          </Button>
        </Box>
      </Paper>

      {/* Analysis Settings */}
      {files.length > 0 && (
        <Paper sx={{ p: 2, mb: 3, bgcolor: 'grey.50' }}>
          <Typography variant="subtitle2" gutterBottom>
            Настройки анализа
          </Typography>
          <Box sx={{ display: 'flex', gap: 3 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={enableSatelliteAnalysis}
                  onChange={(e) => setEnableSatelliteAnalysis(e.target.checked)}
                  disabled={isProcessing}
                />
              }
              label={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <SatelliteIcon fontSize="small" />
                  Спутниковый анализ
                </Box>
              }
            />
            <FormControlLabel
              control={
                <Switch
                  checked={enableGeoAnalysis}
                  onChange={(e) => setEnableGeoAnalysis(e.target.checked)}
                  disabled={isProcessing}
                />
              }
              label={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <AnalyticsIcon fontSize="small" />
                  Геолокационный анализ
                </Box>
              }
            />
          </Box>
        </Paper>
      )}

      {/* Location Hint */}
      {files.length > 0 && (
        <TextField
          label="Подсказка местоположения (опционально)"
          placeholder="например: Москва, Красная площадь, рядом с Кремлем"
          fullWidth
          value={locationHint}
          onChange={(e) => setLocationHint(e.target.value)}
          disabled={isProcessing}
          sx={{ mb: 3 }}
        />
      )}

      {/* File List */}
      {files.length > 0 && (
        <Paper sx={{ p: 2, mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">
              Файлы для обработки ({files.length})
            </Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant="contained"
                onClick={processFiles}
                disabled={isProcessing || files.length === 0}
                startIcon={<UploadIcon />}
              >
                {isProcessing ? 'Обработка...' : 'Начать обработку'}
              </Button>
              <Button
                variant="outlined"
                onClick={clearAll}
                disabled={isProcessing}
                startIcon={<DeleteIcon />}
              >
                Очистить все
              </Button>
            </Box>
          </Box>

          {/* Global Progress */}
          {isProcessing && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" gutterBottom>
                Общий прогресс: {Math.round(globalProgress)}%
              </Typography>
              <LinearProgress variant="determinate" value={globalProgress} />
            </Box>
          )}

          {/* File Grid */}
          <Grid container spacing={2}>
            {files.map((fileItem) => (
              <Grid item xs={12} sm={6} md={4} key={fileItem.id}>
                <Card>
                  <Box sx={{ position: 'relative' }}>
                    <img
                      src={fileItem.preview}
                      alt={fileItem.name || 'Uploaded file'}
                      style={{
                        width: '100%',
                        height: 120,
                        objectFit: 'cover'
                      }}
                    />
                    {!isProcessing && (
                      <IconButton
                        sx={{
                          position: 'absolute',
                          top: 4,
                          right: 4,
                          bgcolor: 'rgba(0,0,0,0.5)',
                          color: 'white',
                          '&:hover': { bgcolor: 'rgba(0,0,0,0.7)' }
                        }}
                        size="small"
                        onClick={() => removeFile(fileItem.id)}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    )}
                  </Box>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      {getStatusIcon(fileItem.status)}
                      <Typography variant="body2" noWrap>
                        {fileItem.name || 'Uploaded file'}
                      </Typography>
                    </Box>
                    
                    <Chip 
                      label={fileItem.status === 'pending' ? 'Ожидание' : 
                            fileItem.status === 'processing' ? 'Обработка' :
                            fileItem.status === 'completed' ? 'Завершено' : 'Ошибка'}
                      color={getStatusColor(fileItem.status)}
                      size="small"
                      sx={{ mb: 1 }}
                    />

                    {fileItem.status === 'processing' && (
                      <LinearProgress 
                        variant="determinate" 
                        value={fileItem.progress} 
                        sx={{ mb: 1 }}
                      />
                    )}

                    {fileItem.error && (
                      <Typography variant="caption" color="error">
                        {fileItem.error}
                      </Typography>
                    )}

                    {fileItem.result && (
                      <Box sx={{ mt: 1 }}>
                        <Typography variant="caption" display="block">
                          Категория: {fileItem.result.category}
                        </Typography>
                        <Typography variant="caption" display="block">
                          Уверенность: {(fileItem.result.confidence * 100).toFixed(1)}%
                        </Typography>
                        {fileItem.result.satellite_data && (
                          <Chip 
                            icon={<SatelliteIcon />}
                            label="Спутниковые данные"
                            size="small"
                            sx={{ mt: 0.5 }}
                          />
                        )}
                      </Box>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Paper>
      )}

      {/* Results Summary */}
      {completedUploads.length > 0 && (
        <Paper sx={{ p: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">
              Результаты обработки ({completedUploads.length})
            </Typography>
            <Button
              startIcon={<DownloadIcon />}
              onClick={exportResults}
              variant="outlined"
            >
              Экспорт результатов
            </Button>
          </Box>

          <Alert severity="success" sx={{ mb: 2 }}>
            Успешно обработано {completedUploads.length} из {files.length} файлов
          </Alert>

          <Grid container spacing={2}>
            {completedUploads.map((result, index) => (
              <Grid item xs={12} sm={6} md={4} key={index}>
                <Card>
                  <CardContent>
                    <Typography variant="subtitle2" gutterBottom>
                      Нарушение #{index + 1}
                    </Typography>
                    <Typography variant="body2">
                      <strong>Категория:</strong> {result.category}
                    </Typography>
                    <Typography variant="body2">
                      <strong>Уверенность:</strong> {(result.confidence * 100).toFixed(1)}%
                    </Typography>
                    {result.location && (
                      <Typography variant="body2">
                        <strong>Координаты:</strong> {result.location.coordinates.join(', ')}
                      </Typography>
                    )}
                    {result.satellite_data && (
                      <Box sx={{ mt: 1 }}>
                        <Chip 
                          icon={<SatelliteIcon />}
                          label={`Источник: ${result.satellite_data.source}`}
                          size="small"
                          color="primary"
                        />
                      </Box>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Paper>
      )}
    </Box>
  );
};

export default BatchViolationUploader;
