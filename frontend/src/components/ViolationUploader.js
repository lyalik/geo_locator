import React, { useState, useCallback, useEffect, useRef } from 'react';
import { useDropzone } from 'react-dropzone';
import { Box, Button, Typography, Paper, CircularProgress, Grid, Card, CardContent, TextField, Switch, FormControlLabel, Chip } from '@mui/material';
import { CloudUpload as UploadIcon, Image as ImageIcon, CheckCircle as CheckIcon, Error as ErrorIcon } from '@mui/icons-material';
import { api } from '../services/api';

// ГЛОБАЛЬНОЕ хранилище результатов вне React компонента
let GLOBAL_SINGLE_RESULTS = [];
let GLOBAL_SINGLE_COUNTER = 0;

const ViolationUploader = ({ onUploadComplete }) => {
  const [files, setFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [results, setResults] = useState([]);
  const [displayResults, setDisplayResults] = useState([]);
  const [forceUpdate, setForceUpdate] = useState(0);
  const resultsRef = useRef([]);
  const [locationHint, setLocationHint] = useState('');
  const [manualCoordinates, setManualCoordinates] = useState({ lat: '', lon: '' });
  const [showManualInput, setShowManualInput] = useState(false);
  const [enableSatelliteAnalysis, setEnableSatelliteAnalysis] = useState(true);
  const [enableGeoAnalysis, setEnableGeoAnalysis] = useState(true);
  const [tempResults, setTempResults] = useState([]);
  const [hardcodedResults, setHardcodedResults] = useState([]);
  
  // Функции для работы с глобальным хранилищем
  const addToGlobalStorage = (result) => {
    GLOBAL_SINGLE_RESULTS.push(result);
    GLOBAL_SINGLE_COUNTER++;
    console.log('Added to GLOBAL_SINGLE_RESULTS:', result);
    console.log('Total global results:', GLOBAL_SINGLE_RESULTS.length);
  };
  
  const clearGlobalStorage = () => {
    GLOBAL_SINGLE_RESULTS = [];
    GLOBAL_SINGLE_COUNTER = 0;
    console.log('Global storage cleared');
    
    // Принудительно обновляем компонент
    setForceUpdate(Date.now());
    
    // Очищаем все React состояния
    setResults([]);
    setDisplayResults([]);
    setHardcodedResults([]);
    resultsRef.current = [];
  };
  
  const getGlobalResults = () => {
    return [...GLOBAL_SINGLE_RESULTS];
  };
  
  // Debug effect to monitor results changes
  useEffect(() => {
    console.log('Results state changed:', results);
    console.log('DisplayResults state changed:', displayResults);
  }, [results, displayResults]);
  
  const onDrop = useCallback(acceptedFiles => {
    const imageFiles = acceptedFiles.filter(file => file.type.startsWith('image/'));
    const filesWithPreview = imageFiles.map(file => Object.assign(file, {
      preview: URL.createObjectURL(file),
      id: Math.random().toString(36).substr(2, 9)
    }));
    setFiles(prevFiles => [...prevFiles, ...filesWithPreview]);
  }, []);

  const handleSubmit = async () => {
    if (files.length === 0) {
      alert('Please select files to upload');
      return;
    }

    setIsUploading(true);
    
    // Process files one by one since /detect endpoint expects single file
    const allResults = [];
    
    for (const file of files) {
      // Create a proper File object if needed
      const actualFile = file instanceof File ? file : new File([file], file.name || 'image.jpg', { type: file.type || 'image/jpeg' });
      
      const formData = new FormData();
      
      // Add single file
      formData.append('file', actualFile);
      
      // Add metadata
      formData.append('user_id', 'current_user_id'); // Replace with actual user ID
      formData.append('location_notes', 'User notes');
      formData.append('location_hint', locationHint);
      
      // Add manual coordinates if provided
      if (manualCoordinates.lat && manualCoordinates.lon) {
        formData.append('manual_lat', manualCoordinates.lat);
        formData.append('manual_lon', manualCoordinates.lon);
      }

      // Debug logging
      console.log('Original file object:', file);
      console.log('Actual file for upload:', actualFile);
      console.log('File instanceof File:', actualFile instanceof File);
      console.log('Uploading file:', actualFile.name, 'Size:', actualFile.size, 'Type:', actualFile.type);
      console.log('FormData entries:', [...formData.entries()]);

      try {
        const response = await fetch('http://localhost:5000/api/violations/detect', {
          method: 'POST',
          body: formData,
        });

        const data = await response.json();
        console.log('API Response:', data);

        if (data.success && enableSatelliteAnalysis && data.data?.location?.coordinates) {
          // Получаем спутниковые данные для обнаруженного местоположения
          await loadSatelliteData(data.data.location.coordinates.latitude, data.data.location.coordinates.longitude);
        }

        if (!data.success) {
          if (data.error === 'UNABLE_TO_DETERMINE_LOCATION' || data.suggest_manual_input) {
            setShowManualInput(true);
            alert('Unable to determine location automatically. Please enter coordinates manually.');
          } else {
            alert(`Error: ${data.message}`);
          }
          continue; // Skip to next file
        }

        console.log('Processing successful response for file:', file.name);

        // Add successful result with proper structure
        const processedResult = {
          ...data.data,
          image: data.data.image_path || data.data.annotated_image_path || file.preview,
          violations: data.data.violations || [],
          location: data.data.location || {},
          metadata: data.data.metadata || {},
          fileName: file.name,
          uploadTime: new Date().toISOString()
        };
        allResults.push(processedResult);
        
        // Сохраняем в глобальное хранилище СРАЗУ
        addToGlobalStorage(processedResult);
        
        console.log('Processed result for display:', processedResult);
        console.log('Current allResults array:', allResults);
        
      } catch (error) {
        console.error('Upload error:', error);
        alert(`Error processing file ${file.name}: ${error.message}`);
      }
    }

    // Process all results - IMMEDIATE UPDATE
    console.log('Setting results state with:', allResults);
    console.log('allResults before setting:', JSON.stringify(allResults, null, 2));
    
    // DIRECT STATE UPDATE - bypass all React issues
    const newResults = [...allResults];
    
    console.log('DIRECT UPDATE - Setting hardcodedResults:', newResults);
    setHardcodedResults(newResults);
    setDisplayResults([...newResults]);
    setResults([...newResults]);
    
    // Also update ref as backup
    resultsRef.current = [...newResults];
    
    console.log('States updated FIRST. New results length:', newResults.length);
    console.log('Ref updated with:', resultsRef.current);
    console.log('Global storage has:', GLOBAL_SINGLE_RESULTS.length, 'results');
    
    // Force component re-render multiple times
    const timestamp = Date.now();
    setForceUpdate(timestamp);
    
    // Дополнительные принудительные обновления
    setTimeout(() => setForceUpdate(timestamp + 1), 100);
    setTimeout(() => setForceUpdate(timestamp + 2), 300);
    
    console.log('Force update timestamp:', timestamp);
    
    // Now set uploading to false
    setIsUploading(false);
    
    // Don't clear files immediately to avoid state conflicts
    setTimeout(() => {
      setFiles([]);
    }, 200);
    
    if (onUploadComplete && allResults.length > 0) {
      onUploadComplete(allResults);
    }
    
    console.log('Upload process completed. Results should now be visible.');
    console.log('Final allResults before setState:', allResults);
    console.log('allResults.length:', allResults.length);
  };

  const loadSatelliteData = async (lat, lon) => {
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
        // Satellite data loaded successfully
        console.log('Satellite data loaded:', response.data.data);
      }
    } catch (error) {
      console.error('Error loading satellite data:', error);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {'image/*': ['.jpeg', '.jpg', '.png', '.gif']},
    maxFiles: 10,
    multiple: true
  });

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Анализ нарушений с ИИ
      </Typography>
      <Typography variant="body2" color="textSecondary" sx={{ mb: 3 }}>
        🤖 Mistral AI + 🎯 YOLO + 🛰️ Спутниковый анализ + 📍 Геолокация
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper 
            variant="outlined" 
            sx={{ 
              p: 3, 
              border: '2px dashed',
              borderColor: 'divider',
              height: 300,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              '&:hover': { borderColor: 'primary.main' },
              ...(isDragActive && { borderColor: 'primary.main' })
            }}
            {...getRootProps()}
          >
            <input {...getInputProps()} />
            
            {isUploading ? (
              <Box textAlign="center">
                <CircularProgress />
                <Typography>Processing...</Typography>
              </Box>
            ) : (
              <Box textAlign="center">
                <UploadIcon sx={{ fontSize: 48, mb: 1 }} />
                <Typography variant="h6" gutterBottom>
                  {isDragActive ? 'Drop images here' : 'Drag & drop images here'}
                </Typography>
                <Typography variant="body2" color="textSecondary" paragraph>
                  or click to select files
                </Typography>
                <Button variant="contained" startIcon={<ImageIcon />}>
                  Select Images
                </Button>
              </Box>
            )}
          </Paper>
          
          {files.length > 0 && (
            <Box mt={2}>
              {/* Превью загруженных файлов */}
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Загруженные файлы ({files.length})
                </Typography>
                <Grid container spacing={1}>
                  {files.map((file) => (
                    <Grid item xs={6} sm={4} key={file.id}>
                      <Box sx={{ position: 'relative' }}>
                        <img
                          src={file.preview}
                          alt={file.name}
                          style={{
                            width: '100%',
                            height: 80,
                            objectFit: 'cover',
                            borderRadius: 4,
                            border: '1px solid #ddd'
                          }}
                        />
                      </Box>
                    </Grid>
                  ))}
                </Grid>
              </Box>
              
              {/* Настройки анализа */}
              <Box sx={{ mb: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Настройки анализа
                </Typography>
                <Grid container spacing={1}>
                  <Grid item xs={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={enableSatelliteAnalysis}
                          onChange={(e) => setEnableSatelliteAnalysis(e.target.checked)}
                        />
                      }
                      label="Спутниковый анализ"
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={enableGeoAnalysis}
                          onChange={(e) => setEnableGeoAnalysis(e.target.checked)}
                        />
                      }
                      label="Геолокационный анализ"
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={true}
                          disabled
                        />
                      }
                      label="🤖 Mistral AI анализ"
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={true}
                          disabled
                        />
                      }
                      label="🎯 YOLO детекция"
                    />
                  </Grid>
                </Grid>
              </Box>
              
              <Box sx={{ mb: 2 }}>
                <TextField
                  label="Адрес для анализа (optional)"
                  placeholder="Например: Москва, Красная площадь, 1"
                  fullWidth
                  value={locationHint}
                  onChange={(e) => setLocationHint(e.target.value)}
                  sx={{ mb: 1 }}
                />
                <Button
                  variant="outlined"
                  size="small"
                  onClick={async () => {
                    if (!locationHint.trim()) {
                      alert('Введите адрес для поиска');
                      return;
                    }
                    
                    try {
                      // Яндекс Геокодер API
                      const response = await fetch(
                        `https://geocode-maps.yandex.ru/1.x/?apikey=YOUR_YANDEX_API_KEY&geocode=${encodeURIComponent(locationHint)}&format=json&results=1`
                      );
                      const data = await response.json();
                      
                      if (data.response?.GeoObjectCollection?.featureMember?.length > 0) {
                        const coords = data.response.GeoObjectCollection.featureMember[0].GeoObject.Point.pos.split(' ');
                        const lon = parseFloat(coords[0]);
                        const lat = parseFloat(coords[1]);
                        
                        setManualCoordinates({ lat: lat.toString(), lon: lon.toString() });
                        setShowManualInput(true);
                        alert(`Координаты найдены: ${lat}, ${lon}`);
                      } else {
                        alert('Адрес не найден. Попробуйте более точный адрес.');
                      }
                    } catch (error) {
                      console.error('Geocoding error:', error);
                      // Fallback к простому парсингу если API недоступен
                      alert('Сервис геокодинга недоступен. Введите координаты вручную.');
                      setShowManualInput(true);
                    }
                  }}
                  sx={{ mt: 1 }}
                >
                  🗺️ Найти координаты
                </Button>
              </Box>

              {showManualInput && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Manual Coordinates (if automatic detection fails)
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <TextField
                        label="Latitude"
                        type="number"
                        fullWidth
                        value={manualCoordinates.lat}
                        onChange={(e) => setManualCoordinates({...manualCoordinates, lat: e.target.value})}
                      />
                    </Grid>
                    <Grid item xs={6}>
                      <TextField
                        label="Longitude"
                        type="number"
                        fullWidth
                        value={manualCoordinates.lon}
                        onChange={(e) => setManualCoordinates({...manualCoordinates, lon: e.target.value})}
                      />
                    </Grid>
                  </Grid>
                </Box>
              )}

              <Button
                variant="contained"
                color="primary"
                fullWidth
                onClick={handleSubmit}
                disabled={isUploading}
              >
                {isUploading ? 'Обработка...' : 'Начать анализ'}
              </Button>
            </Box>
          )}
        </Grid>
        
        <Grid item xs={12} key={`results-${forceUpdate}`}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">
              Результаты анализа
            </Typography>
            <Button 
              variant="outlined" 
              size="small" 
              onClick={clearGlobalStorage}
              disabled={GLOBAL_SINGLE_RESULTS.length === 0}
            >
              Очистить результаты
            </Button>
          </Box>
          
          {/* Диагностическая информация */}
          <Box sx={{ p: 2, bgcolor: 'info.light', mb: 2, borderRadius: 1 }}>
            <Typography variant="body2" color="info.contrastText">
              🔍 Диагностика: Global={GLOBAL_SINGLE_RESULTS.length} | Ref={resultsRef.current.length} | 
              Display={displayResults.length} | Hard={hardcodedResults.length} | Results={results.length}
            </Typography>
            <Typography variant="body2" color="info.contrastText">
              📊 Источник данных: {GLOBAL_SINGLE_RESULTS.length > 0 ? 'GLOBAL_STORAGE' : 
                                   resultsRef.current.length > 0 ? 'RESULTS_REF' :
                                   hardcodedResults.length > 0 ? 'HARDCODED_STATE' :
                                   displayResults.length > 0 ? 'DISPLAY_STATE' : 'EMPTY'}
            </Typography>
          </Box>
          
          {(() => {
            // Приоритетная система отображения
            const globalResults = getGlobalResults();
            const sourceData = globalResults.length > 0 ? globalResults :
                             resultsRef.current.length > 0 ? resultsRef.current :
                             hardcodedResults.length > 0 ? hardcodedResults : 
                             displayResults.length > 0 ? displayResults : 
                             results;
            
            console.log('🎯 Rendering with source data:', sourceData);
            console.log('🎯 Source data length:', sourceData.length);
            
            if (sourceData.length === 0) {
              return (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <Typography variant="body1" color="text.secondary">
                    Результаты анализа появятся здесь после загрузки изображений
                  </Typography>
                </Box>
              );
            }
            
            return (
              <Box sx={{ maxHeight: 600, overflowY: 'auto' }}>
                {sourceData.map((result, index) => {
                  const violationCount = result.violations ? result.violations.length : 0;
                  const hasLocation = result.location && (result.location.coordinates || result.location.address);
                  
                  return (
                    <Card key={`result-${index}-${result.violation_id || index}`} sx={{ mb: 2 }}>
                      <CardContent>
                        <Box sx={{ display: 'flex', gap: 2 }}>
                          {/* Изображение */}
                          <Box sx={{ flexShrink: 0 }}>
                            <img 
                              src={result.image || result.annotated_image_path || result.image_path}
                              alt={`Результат ${index + 1}`}
                              style={{
                                width: 120,
                                height: 90,
                                objectFit: 'cover',
                                borderRadius: 4,
                                border: '1px solid #ddd'
                              }}
                              onError={(e) => {
                                console.log('Image load error:', e.target.src);
                                e.target.style.backgroundColor = '#f5f5f5';
                                e.target.alt = 'Изображение недоступно';
                              }}
                            />
                          </Box>
                          
                          {/* Информация */}
                          <Box sx={{ flex: 1 }}>
                            <Typography variant="h6" gutterBottom>
                              {result.fileName || `Изображение ${index + 1}`}
                            </Typography>
                            
                            {/* Нарушения */}
                            <Box sx={{ mb: 1 }}>
                              {violationCount > 0 ? (
                                <Chip 
                                  icon={<ErrorIcon />}
                                  label={`${violationCount} нарушений`}
                                  color="error"
                                  size="small"
                                  sx={{ mr: 1 }}
                                />
                              ) : (
                                <Chip 
                                  icon={<CheckIcon />}
                                  label="Нарушений не найдено"
                                  color="success"
                                  size="small"
                                  sx={{ mr: 1 }}
                                />
                              )}
                              
                              {hasLocation && (
                                <Chip 
                                  label="Геолокация определена"
                                  color="info"
                                  size="small"
                                  sx={{ mr: 1 }}
                                />
                              )}
                            </Box>
                            
                            {/* Детали нарушений */}
                            {result.violations && result.violations.length > 0 && (
                              <Box sx={{ mb: 1 }}>
                                <Typography variant="body2" color="text.secondary" gutterBottom>
                                  Обнаруженные нарушения:
                                </Typography>
                                {result.violations.map((violation, vIndex) => {
                                  // Определяем источник детекции
                                  const isMistralAI = violation.source === 'mistral_ai';
                                  const isYOLO = violation.source === 'yolo' || !violation.source;
                                  
                                  return (
                                    <Box key={vIndex} sx={{ ml: 1, mb: 0.5 }}>
                                      <Typography variant="body2" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                        • {violation.category || violation.type} ({Math.round(violation.confidence * 100)}%)
                                        {isMistralAI && (
                                          <Chip 
                                            label="Mistral AI" 
                                            size="small" 
                                            color="secondary"
                                            sx={{ fontSize: '0.7rem', height: 18 }}
                                          />
                                        )}
                                        {isYOLO && (
                                          <Chip 
                                            label="YOLO" 
                                            size="small" 
                                            color="primary"
                                            sx={{ fontSize: '0.7rem', height: 18 }}
                                          />
                                        )}
                                      </Typography>
                                      {violation.description && (
                                        <Typography variant="caption" color="text.secondary" sx={{ ml: 2, display: 'block' }}>
                                          {violation.description}
                                        </Typography>
                                      )}
                                    </Box>
                                  );
                                })}
                              </Box>
                            )}
                            
                            {/* Местоположение */}
                            {hasLocation && (
                              <Typography variant="body2" color="text.secondary">
                                📍 {result.location.address || 
                                    `${result.location.coordinates?.latitude}, ${result.location.coordinates?.longitude}`}
                              </Typography>
                            )}
                            
                            {/* Метаданные */}
                            <Typography variant="body2" color="text.secondary">
                              🆔 {result.violation_id || 'N/A'}
                            </Typography>
                            
                            {result.uploadTime && (
                              <Typography variant="body2" color="text.secondary">
                                ⏰ {new Date(result.uploadTime).toLocaleString('ru-RU')}
                              </Typography>
                            )}
                          </Box>
                        </Box>
                      </CardContent>
                    </Card>
                  );
                })}
              </Box>
            );
          })()}
          
        </Grid>
      </Grid>
    </Box>
  );
};

export default ViolationUploader;
