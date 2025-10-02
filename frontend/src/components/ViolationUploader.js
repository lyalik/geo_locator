import React, { useState, useCallback, useEffect, useRef } from 'react';
import { useDropzone } from 'react-dropzone';
import { Box, Button, Typography, Paper, CircularProgress, Grid, Card, CardContent, TextField, Switch, FormControlLabel, Chip, Dialog, DialogContent, IconButton, Divider, Table, TableBody, TableCell, TableHead, TableRow, TableContainer } from '@mui/material';
import { CloudUpload as UploadIcon, Image as ImageIcon, CheckCircle as CheckIcon, Error as ErrorIcon, LocationOn as LocationIcon, Assessment as AnalysisIcon, Close as CloseIcon, ZoomIn as ZoomInIcon, Download as DownloadIcon } from '@mui/icons-material';
import { api } from '../services/api';
import ValidationDisplay from './ValidationDisplay';
import * as XLSX from 'xlsx';

// ГЛОБАЛЬНОЕ хранилище результатов вне React компонента
let GLOBAL_SINGLE_RESULTS = [];

/**
 * ViolationUploader - Компонент для загрузки и анализа одиночных изображений нарушений
 * 
 * Функциональность:
 * - Drag & Drop загрузка изображений (JPEG, PNG, GIF, BMP, WebP)
 * - Автоматическая детекция нарушений через YOLO + Mistral AI
 * - Геолокационный анализ с подсказками местоположения
 * - Ручной ввод координат при необходимости
 * - Опциональный спутниковый и геоанализ
 * - Сохранение результатов в PostgreSQL
 * - Отображение результатов с детальной информацией
 */
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
  const [hardcodedResults, setHardcodedResults] = useState([]);
  const [imageModalOpen, setImageModalOpen] = useState(false);
  const [selectedImage, setSelectedImage] = useState(null);
  
  // Функции для работы с глобальным хранилищем
  const addToGlobalStorage = (result) => {
    GLOBAL_SINGLE_RESULTS.push(result);
    console.log('Added to GLOBAL_SINGLE_RESULTS:', result);
    console.log('Total global results:', GLOBAL_SINGLE_RESULTS.length);
  };
  
  const clearGlobalStorage = () => {
    GLOBAL_SINGLE_RESULTS = [];
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
  
  // Экспорт результатов в Excel
  const exportToExcel = () => {
    const globalResults = getGlobalResults();
    const sourceData = globalResults.length > 0 ? globalResults :
                     resultsRef.current.length > 0 ? resultsRef.current :
                     hardcodedResults.length > 0 ? hardcodedResults : 
                     displayResults.length > 0 ? displayResults : 
                     results;
    
    if (sourceData.length === 0) {
      alert('Нет данных для экспорта');
      return;
    }
    
    // Подготовка данных для Excel
    const excelData = [];
    
    sourceData.forEach((result, index) => {
      const fileName = result.fileName || `Изображение ${index + 1}`;
      const violationId = result.violation_id || 'N/A';
      const uploadTime = result.uploadTime ? new Date(result.uploadTime).toLocaleString('ru-RU') : 'N/A';
      const coordinates = result.location?.coordinates 
        ? `${result.location.coordinates.latitude}, ${result.location.coordinates.longitude}`
        : 'N/A';
      const address = result.location?.address?.formatted || result.location?.address || 'N/A';
      
      if (result.violations && result.violations.length > 0) {
        result.violations.forEach((violation, vIdx) => {
          const source = violation.source === 'mistral_ai' ? 'Mistral AI' : 
                        violation.source === 'yolo' ? 'YOLO' : 'Unknown';
          const customerType = violation.customer_type || violation.label || '';
          const customerTypeText = customerType === '18-001' ? 'Строительная площадка' : 
                                  customerType === '00-022' ? 'Нарушения недвижимости' : '';
          
          excelData.push({
            '№': index + 1,
            'Файл': fileName,
            'ID Нарушения': violationId,
            'Дата/Время': uploadTime,
            'Источник': source,
            'Категория': violation.category || violation.type || '',
            'Уверенность (%)': Math.round((violation.confidence || 0) * 100),
            'Тип заказчика': customerType,
            'Описание типа': customerTypeText,
            'Описание нарушения': violation.description || '',
            'Координаты': coordinates,
            'Адрес': address
          });
        });
      } else {
        excelData.push({
          '№': index + 1,
          'Файл': fileName,
          'ID Нарушения': violationId,
          'Дата/Время': uploadTime,
          'Источник': 'Нет нарушений',
          'Категория': '',
          'Уверенность (%)': '',
          'Тип заказчика': '',
          'Описание типа': '',
          'Описание нарушения': '',
          'Координаты': coordinates,
          'Адрес': address
        });
      }
    });
    
    // Создание Excel файла
    const ws = XLSX.utils.json_to_sheet(excelData);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Нарушения');
    
    // Автоматическая ширина колонок
    const maxWidth = 50;
    const wscols = [
      { wch: 5 },  // №
      { wch: 30 }, // Файл
      { wch: 38 }, // ID
      { wch: 20 }, // Дата
      { wch: 15 }, // Источник
      { wch: 20 }, // Категория
      { wch: 15 }, // Уверенность
      { wch: 10 }, // Тип заказчика
      { wch: 25 }, // Описание типа
      { wch: maxWidth }, // Описание
      { wch: 25 }, // Координаты
      { wch: maxWidth }  // Адрес
    ];
    ws['!cols'] = wscols;
    
    // Сохранение файла
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
    XLSX.writeFile(wb, `violations_export_${timestamp}.xlsx`);
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

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.gif', '.bmp', '.webp']
    },
    multiple: true
  });

  const handleSubmit = async () => {
    if (files.length === 0) {
      alert('Please select files to upload');
      return;
    }

    setIsUploading(true);
    
    // Process files one by one
    const allResults = [];
    
    for (const file of files) {
      // Create a proper File object if needed
      const actualFile = file instanceof File ? file : new File([file], file.name || 'image.jpg', { type: file.type || 'image/jpeg' });
      
      try {
        let data;
        
        // Violation detection mode only
        const formData = new FormData();
        formData.append('file', actualFile);
        formData.append('user_id', 'current_user_id');
        formData.append('location_notes', 'User notes');
        formData.append('location_hint', locationHint);
        
        if (manualCoordinates.lat && manualCoordinates.lon) {
          formData.append('manual_lat', manualCoordinates.lat);
          formData.append('manual_lon', manualCoordinates.lon);
        }

        const response = await fetch('http://192.168.1.67:5001/api/violations/detect', {
          method: 'POST',
          body: formData,
        });

        data = await response.json();
        console.log('API Response:', data);
        
        // КРИТИЧЕСКАЯ ДИАГНОСТИКА - проверяем весь ответ
        console.log('🔍 Full API response structure:');
        console.log('- success:', data.success);
        console.log('- data exists:', !!data.data);
        console.log('- data keys:', data.data ? Object.keys(data.data) : 'NO DATA');
        console.log('- violations in data:', data.data?.violations ? data.data.violations.length : 'NO VIOLATIONS');
        console.log('- raw violations:', data.data?.violations);
        
        // Debug: детальный анализ violations
        if (data.success && data.data && data.data.violations) {
          console.log('🔍 Raw violations from API:', data.data.violations);
          data.data.violations.forEach((v, index) => {
            console.log(`🔍 Violation ${index}:`, {
              category: v.category,
              source: v.source,
              confidence: v.confidence,
              description: v.description
            });
          });
        } else {
          console.log('❌ NO VIOLATIONS FOUND IN RESPONSE');
          console.log('❌ Response structure:', JSON.stringify(data, null, 2));
        }

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

        // Создаем объект результата для отображения
        // Формируем правильные URL для изображений
        const baseUrl = 'http://192.168.1.67:5001';
        const annotatedImagePath = data.data?.annotated_image_path 
          ? (data.data.annotated_image_path.startsWith('http') 
              ? data.data.annotated_image_path 
              : `${baseUrl}${data.data.annotated_image_path}`)
          : null;
        const originalImagePath = data.data?.image_path
          ? (data.data.image_path.startsWith('http')
              ? data.data.image_path
              : `${baseUrl}${data.data.image_path}`)
          : URL.createObjectURL(actualFile);
        
        const processedResult = {
          violation_id: data.data?.violation_id || `temp_${Date.now()}`,
          fileName: actualFile.name,
          image: originalImagePath,
          annotated_image_path: annotatedImagePath,
          violations: data.data?.violations || [],
          location: data.data?.location || (manualCoordinates.lat && manualCoordinates.lon ? {
            coordinates: {
              latitude: parseFloat(manualCoordinates.lat),
              longitude: parseFloat(manualCoordinates.lon)
            },
            address: locationHint || 'Координаты заданы вручную'
          } : null),
          satellite_data: data.data?.satellite_data || null,
          uploadTime: new Date().toISOString()
        };
        allResults.push(processedResult);
        
        // Сохраняем в глобальное хранилище СРАЗУ
        addToGlobalStorage(processedResult);
        
        console.log('Processed result for display:', processedResult);
        console.log('Current allResults array:', allResults);
        
        // Логируем результаты анализа нарушений
        if (data.data && data.data.violations) {
          console.log('🔧 Processing violations from data.data.violations');
          const allViolations = data.data.violations;
          const googleViolations = allViolations.filter(v => v.source === 'mistral_ai');
          const yoloViolations = allViolations.filter(v => v.source === 'yolo' || !v.source);
          
          console.log('🔧 All violations:', allViolations);
          console.log('🔧 Mistral AI violations after filter:', googleViolations);
          console.log('🔧 YOLO violations after filter:', yoloViolations);
          
          if (googleViolations.length > 0) {
            console.log('🤖 Mistral AI обнаружил нарушения:', googleViolations);
            googleViolations.forEach(violation => {
              console.log(`- ${violation.category}: ${violation.description} (${Math.round(violation.confidence * 100)}%)`);
            });
          } else {
            console.log('❌ Mistral AI нарушения не найдены после фильтрации');
          }
          
          if (yoloViolations.length > 0) {
            console.log('🎯 YOLO обнаружил нарушения:', yoloViolations);
            yoloViolations.forEach(violation => {
              console.log(`- ${violation.category}: ${Math.round(violation.confidence * 100)}%`);
            });
          }
          
          console.log(`📊 Итого: Mistral AI: ${googleViolations.length}, YOLO: ${yoloViolations.length}`);
        } else {
          console.log('❌ Нет violations в data.data');
        }
        
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
      console.log(`Loading satellite data for coordinates: ${lat}, ${lon}`);
      // Здесь можно добавить вызов API для получения спутниковых данных
      // Пока что просто логируем
    } catch (error) {
      console.error('Error loading satellite data:', error);
    }
  };

  // Функция для анализа координат изображений (аналогично видео анализу)
  const analyzeImageCoordinates = async (file) => {
    const formData = new FormData();
    formData.append('image', file);
    if (locationHint) {
      formData.append('location_hint', locationHint);
    }

    try {
      const response = await fetch('http://192.168.1.67:5001/api/coordinates/detect', {
        method: 'POST',
        body: formData,
      });

      // Проверяем статус ответа
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Получаем текст ответа для диагностики
      const responseText = await response.text();
      console.log('Raw response:', responseText);

      // Пытаемся распарсить JSON
      let data;
      try {
        data = JSON.parse(responseText);
      } catch (parseError) {
        console.error('JSON parse error:', parseError);
        console.error('Response text:', responseText);
        throw new Error(`Сервер вернул некорректный JSON: ${responseText.substring(0, 100)}...`);
      }
      
      if (data.success) {
        const resultData = data.data || {};
        return {
          fileName: file.name,
          image: URL.createObjectURL(file),
          success: true,
          coordinates: resultData.coordinates,
          objects: resultData.objects || [],
          total_objects: resultData.total_objects || 0,
          coordinate_sources: resultData.coordinate_sources || {},
          detection_status: resultData.detection_status || 'unknown'
        };
      } else {
        return {
          fileName: file.name,
          image: URL.createObjectURL(file),
          success: false,
          error: data.error || data.message || 'Ошибка анализа координат'
        };
      }
    } catch (error) {
      console.error('Error in analyzeImageCoordinates:', error);
      return {
        fileName: file.name,
        image: URL.createObjectURL(file),
        success: false,
        error: error.message
      };
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Анализ нарушений с ИИ
      </Typography>
      <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
        🤖 Mistral AI + 🎯 YOLO + 🛰️ Спутниковый анализ + 📍 Геолокация (до 50 фото)
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
                  Загруженные файлы ({files.length} из 50)
                </Typography>
                <Box sx={{ maxHeight: 200, overflowY: 'auto' }}>
                  <Grid container spacing={1}>
                    {files.map((file) => (
                      <Grid item xs={6} sm={4} md={3} key={file.id}>
                        <Box sx={{ position: 'relative' }}>
                          <img
                            src={file.preview}
                            alt={file.name}
                            style={{
                              width: '100%',
                              height: 60,
                              objectFit: 'cover',
                              borderRadius: 4,
                              border: '1px solid #ddd'
                            }}
                          />
                          <Typography variant="caption" sx={{ 
                            position: 'absolute', 
                            bottom: 0, 
                            left: 0, 
                            right: 0, 
                            bgcolor: 'rgba(0,0,0,0.7)', 
                            color: 'white', 
                            p: 0.5, 
                            fontSize: '0.6rem',
                            textAlign: 'center'
                          }}>
                            {file.name.length > 15 ? `${file.name.substring(0, 15)}...` : file.name}
                          </Typography>
                        </Box>
                      </Grid>
                    ))}
                  </Grid>
                </Box>
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
                      label="🎯 YOLO детекция объектов"
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
                      // Используем backend геокодинг через наш API
                      const response = await fetch(`http://192.168.1.67:5001/api/geo/geocode?address=${encodeURIComponent(locationHint)}`);
                      const data = await response.json();
                      
                      if (data.success && data.data?.coordinates) {
                        const { latitude, longitude } = data.data.coordinates;
                        
                        setManualCoordinates({ 
                          lat: latitude.toString(), 
                          lon: longitude.toString() 
                        });
                        setShowManualInput(true);
                        alert(`Координаты найдены: ${latitude}, ${longitude}\nИсточник: ${data.data.source || 'Geo API'}`);
                      } else {
                        // Fallback - простое определение координат для Москвы
                        if (locationHint.toLowerCase().includes('москва')) {
                          const mockCoords = {
                            lat: (55.7558 + (Math.random() - 0.5) * 0.1).toFixed(6),
                            lon: (37.6176 + (Math.random() - 0.5) * 0.1).toFixed(6)
                          };
                          setManualCoordinates(mockCoords);
                          setShowManualInput(true);
                          alert(`Приблизительные координаты для Москвы: ${mockCoords.lat}, ${mockCoords.lon}`);
                        } else {
                          alert('Адрес не найден. Введите координаты вручную.');
                          setShowManualInput(true);
                        }
                      }
                    } catch (error) {
                      console.error('Geocoding error:', error);
                      // Fallback для московских адресов
                      if (locationHint.toLowerCase().includes('москва')) {
                        const mockCoords = {
                          lat: (55.7558 + (Math.random() - 0.5) * 0.1).toFixed(6),
                          lon: (37.6176 + (Math.random() - 0.5) * 0.1).toFixed(6)
                        };
                        setManualCoordinates(mockCoords);
                        setShowManualInput(true);
                        alert(`Приблизительные координаты для Москвы: ${mockCoords.lat}, ${mockCoords.lon}`);
                      } else {
                        alert('Сервис геокодинга недоступен. Введите координаты вручную.');
                        setShowManualInput(true);
                      }
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
                sx={{ py: 1.5 }}
              >
                {isUploading ? `Обработка... (${files.length} файлов)` : `Начать анализ (${files.length} файлов)`}
              </Button>
            </Box>
          )}
        </Grid>
        
        <Grid item xs={12} key={`results-${forceUpdate}`}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">
              Результаты анализа
            </Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button 
                variant="contained" 
                color="success"
                size="small" 
                startIcon={<DownloadIcon />}
                onClick={exportToExcel}
                disabled={GLOBAL_SINGLE_RESULTS.length === 0}
              >
                Экспорт в Excel
              </Button>
              <Button 
                variant="outlined" 
                size="small" 
                onClick={clearGlobalStorage}
                disabled={GLOBAL_SINGLE_RESULTS.length === 0}
              >
                Очистить результаты
              </Button>
            </Box>
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
                          <Box 
                            sx={{ 
                              flexShrink: 0,
                              position: 'relative',
                              cursor: 'pointer',
                              '&:hover': {
                                opacity: 0.8
                              }
                            }}
                            onClick={() => {
                              // Приоритет: аннотированное изображение с bbox > оригинал
                              const imageUrl = result.annotated_image_path || result.image || result.image_path;
                              setSelectedImage(imageUrl);
                              setImageModalOpen(true);
                            }}
                          >
                            <img 
                              src={result.annotated_image_path || result.image || result.image_path}
                              alt={`Результат ${index + 1}`}
                              style={{
                                width: 150,
                                height: 150,
                                objectFit: 'cover',
                                borderRadius: 8,
                                border: result.annotated_image_path ? '3px solid #4caf50' : '2px solid #ddd'
                              }}
                              onError={(e) => {
                                console.log('Image load error:', e.target.src);
                                e.target.style.backgroundColor = '#f5f5f5';
                                e.target.alt = 'Изображение недоступно';
                              }}
                            />
                            {/* Индикатор аннотированного изображения */}
                            {result.annotated_image_path && (
                              <Chip
                                label="С разметкой"
                                size="small"
                                color="success"
                                sx={{
                                  position: 'absolute',
                                  bottom: 5,
                                  left: 5,
                                  fontSize: '0.65rem',
                                  height: 20
                                }}
                              />
                            )}
                            <Box
                              sx={{
                                position: 'absolute',
                                top: '50%',
                                left: '50%',
                                transform: 'translate(-50%, -50%)',
                                backgroundColor: 'rgba(0,0,0,0.5)',
                                borderRadius: '50%',
                                padding: '8px',
                                display: 'flex',
                                opacity: 0,
                                transition: 'opacity 0.2s',
                                '&:hover': {
                                  opacity: 1
                                }
                              }}
                            >
                              <ZoomInIcon sx={{ color: 'white' }} />
                            </Box>
                          </Box>
                          
                          {/* Информация */}
                          <Box sx={{ flex: 1 }}>
                            <Typography variant="h6" gutterBottom>
                              {result.fileName || `Изображение ${index + 1}`}
                            </Typography>
                            
                            {/* Нарушения и статистика ИИ */}
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
                              
                              {/* Показываем статистику по источникам ИИ */}
                              {result.violations && result.violations.length > 0 && (() => {
                                const googleCount = result.violations.filter(v => v.source === 'mistral_ai').length;
                                const yoloCount = result.violations.filter(v => v.source === 'yolo' || !v.source).length;
                                
                                return (
                                  <>
                                    {googleCount > 0 && (
                                      <Chip 
                                        label={`🤖 Mistral AI: ${googleCount}`}
                                        color="secondary"
                                        size="small"
                                        sx={{ mr: 1, fontSize: '0.75rem' }}
                                      />
                                    )}
                                    {yoloCount > 0 && (
                                      <Chip 
                                        label={`🎯 YOLO: ${yoloCount}`}
                                        color="primary"
                                        size="small"
                                        sx={{ mr: 1, fontSize: '0.75rem' }}
                                      />
                                    )}
                                  </>
                                );
                              })()}
                              
                              {hasLocation && (
                                <Chip 
                                  label="📍 Геолокация"
                                  color="info"
                                  size="small"
                                  sx={{ mr: 1 }}
                                />
                              )}
                            </Box>
                            
                            {/* Детали нарушений - сгруппированные по источникам */}
                            {result.violations && result.violations.length > 0 && (() => {
                              const mistralViolations = result.violations.filter(v => v.source === 'mistral_ai');
                              const yoloViolations = result.violations.filter(v => v.source === 'yolo' || !v.source);
                              
                              return (
                                <Box sx={{ mb: 2 }}>
                                  <Divider sx={{ my: 2 }} />
                                  <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 'bold' }}>
                                    Обнаруженные нарушения:
                                  </Typography>
                                  
                                  {/* YOLO Results */}
                                  {yoloViolations.length > 0 && (
                                    <Box sx={{ mb: 2, p: 1.5, bgcolor: '#e3f2fd', borderRadius: 2 }}>
                                      <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1, color: '#1976d2' }}>
                                        🎯 YOLO ({yoloViolations.length})
                                      </Typography>
                                      <TableContainer>
                                        <Table size="small">
                                          <TableHead>
                                            <TableRow>
                                              <TableCell><strong>Категория</strong></TableCell>
                                              <TableCell><strong>Уверенность</strong></TableCell>
                                              <TableCell><strong>Тип</strong></TableCell>
                                            </TableRow>
                                          </TableHead>
                                          <TableBody>
                                            {yoloViolations.map((violation, idx) => {
                                              const customerType = violation.customer_type || violation.label;
                                              const customerTypeText = customerType === '18-001' ? 'Строительная площадка' : 
                                                                      customerType === '00-022' ? 'Нарушения недвижимости' : '';
                                              return (
                                                <TableRow key={idx} sx={{ '&:hover': { bgcolor: '#bbdefb' } }}>
                                                  <TableCell>{violation.category || violation.type}</TableCell>
                                                  <TableCell>
                                                    <Chip 
                                                      label={`${Math.round(violation.confidence * 100)}%`}
                                                      size="small"
                                                      color={violation.confidence > 0.7 ? 'success' : 'warning'}
                                                      sx={{ fontSize: '0.75rem' }}
                                                    />
                                                  </TableCell>
                                                  <TableCell>
                                                    {customerType && (
                                                      <Chip 
                                                        label={`${customerType}: ${customerTypeText}`}
                                                        size="small" 
                                                        color={customerType === '18-001' ? 'warning' : 'info'}
                                                        sx={{ fontSize: '0.7rem' }}
                                                      />
                                                    )}
                                                  </TableCell>
                                                </TableRow>
                                              );
                                            })}
                                          </TableBody>
                                        </Table>
                                      </TableContainer>
                                    </Box>
                                  )}
                                  
                                  {/* Mistral AI Results */}
                                  {mistralViolations.length > 0 && (
                                    <Box sx={{ p: 1.5, bgcolor: '#f3e5f5', borderRadius: 2 }}>
                                      <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1, color: '#9c27b0' }}>
                                        🤖 Mistral AI ({mistralViolations.length})
                                      </Typography>
                                      {mistralViolations.map((violation, idx) => {
                                        const customerType = violation.customer_type || violation.label;
                                        const customerTypeText = customerType === '18-001' ? 'Строительная площадка' : 
                                                                customerType === '00-022' ? 'Нарушения недвижимости' : '';
                                        return (
                                          <Box key={idx} sx={{ mb: 1.5, p: 1, bgcolor: 'white', borderRadius: 1 }}>
                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                                              <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                                                {violation.category || violation.type}
                                              </Typography>
                                              <Chip 
                                                label={`${Math.round(violation.confidence * 100)}%`}
                                                size="small"
                                                color={violation.confidence > 0.7 ? 'success' : 'warning'}
                                                sx={{ fontSize: '0.7rem' }}
                                              />
                                              {customerType && (
                                                <Chip 
                                                  label={`${customerType}: ${customerTypeText}`}
                                                  size="small" 
                                                  color={customerType === '18-001' ? 'warning' : 'info'}
                                                  sx={{ fontSize: '0.7rem' }}
                                                />
                                              )}
                                            </Box>
                                            {violation.description && (
                                              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', fontStyle: 'italic' }}>
                                                {violation.description}
                                              </Typography>
                                            )}
                                          </Box>
                                        );
                                      })}
                                    </Box>
                                  )}
                                </Box>
                              );
                            })()}
                            
                            {/* Местоположение */}
                            {hasLocation && (
                              <Box sx={{ mt: 2, p: 1.5, bgcolor: 'grey.100', borderRadius: 1 }}>
                                <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1 }}>
                                  📍 Геолокация:
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                  {result.location.address?.formatted || result.location.address || 
                                      `${result.location.coordinates?.latitude}, ${result.location.coordinates?.longitude}`}
                                </Typography>
                                
                                {/* Детальная информация об источниках координат */}
                                {result.location.sources_details && result.location.sources_details.length > 0 && (
                                  <Box sx={{ mt: 2 }}>
                                    <Typography variant="caption" sx={{ fontWeight: 'bold', display: 'block', mb: 1 }}>
                                      📊 Источники координат:
                                    </Typography>
                                    {result.location.sources_details.map((source, idx) => (
                                      <Box key={idx} sx={{ 
                                        mt: 1, 
                                        p: 1, 
                                        borderLeft: '3px solid',
                                        borderColor: source.status === 'success' ? 'success.main' : 'grey.400',
                                        bgcolor: source.status === 'success' ? 'success.lighter' : 'white',
                                        borderRadius: 0.5
                                      }}>
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
                                          <Typography variant="caption" sx={{ fontWeight: 'bold' }}>
                                            {source.icon} {source.name}
                                          </Typography>
                                          <Chip 
                                            label={source.status === 'success' ? '✅' : '❌'} 
                                            size="small" 
                                            sx={{ height: 16, fontSize: '0.6rem' }}
                                          />
                                        </Box>
                                        
                                        {source.details && (
                                          <Typography variant="caption" display="block" color="text.secondary" sx={{ fontSize: '0.7rem' }}>
                                            🔍 {source.details}
                                          </Typography>
                                        )}
                                        
                                        {source.text && (
                                          <Typography variant="caption" display="block" sx={{ fontSize: '0.7rem', fontFamily: 'monospace', mt: 0.5 }}>
                                            📝 "{source.text}"
                                          </Typography>
                                        )}
                                        
                                        {source.service && (
                                          <Typography variant="caption" display="block" color="text.secondary" sx={{ fontSize: '0.7rem', mt: 0.5 }}>
                                            🔧 {source.service}
                                          </Typography>
                                        )}
                                        
                                        {source.confidence > 0 && (
                                          <Typography variant="caption" display="block" color="primary" sx={{ fontSize: '0.7rem', mt: 0.5 }}>
                                            📊 {Math.round(source.confidence * 100)}%
                                          </Typography>
                                        )}
                                        
                                        {source.coordinates && source.coordinates.lat && (
                                          <Typography variant="caption" display="block" color="success.main" sx={{ fontSize: '0.7rem', fontWeight: 'bold', mt: 0.5 }}>
                                            📍 {source.coordinates.lat.toFixed(6)}, {source.coordinates.lon.toFixed(6)}
                                          </Typography>
                                        )}
                                      </Box>
                                    ))}
                                  </Box>
                                )}
                              </Box>
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
                        
                        {/* Валидация по готовой базе заказчика */}
                        {(result.validation || result.reference_matches) && (
                          <ValidationDisplay 
                            validation={result.validation}
                            referenceMatches={result.reference_matches}
                          />
                        )}
                      </CardContent>
                    </Card>
                  );
                })}
              </Box>
            );
          })()}
          
        </Grid>
      </Grid>
      
      {/* Modal для увеличенного изображения */}
      <Dialog 
        open={imageModalOpen} 
        onClose={() => setImageModalOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <IconButton
          onClick={() => setImageModalOpen(false)}
          sx={{
            position: 'absolute',
            right: 8,
            top: 8,
            color: 'white',
            bgcolor: 'rgba(0,0,0,0.5)',
            '&:hover': {
              bgcolor: 'rgba(0,0,0,0.7)'
            }
          }}
        >
          <CloseIcon />
        </IconButton>
        <DialogContent sx={{ p: 0, bgcolor: 'black', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          {selectedImage && (
            <img 
              src={selectedImage}
              alt="Увеличенное изображение"
              style={{
                maxWidth: '100%',
                maxHeight: '90vh',
                objectFit: 'contain'
              }}
            />
          )}
        </DialogContent>
      </Dialog>
    </Box>
  );
};

export default ViolationUploader;
