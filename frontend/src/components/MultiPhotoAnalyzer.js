import React, { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  TextField,
  Paper,
  Alert,
  CircularProgress,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Grid,
  Card,
  CardContent,
  CardMedia
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  PhotoCamera as PhotoCameraIcon,
  Analytics as AnalyticsIcon,
  Map as MapIcon,
  CheckCircle as CheckCircleIcon
} from '@mui/icons-material';
import { useSnackbar } from 'notistack';
import ObjectGrouper from './ObjectGrouper';
import InteractiveResultsMap from './InteractiveResultsMap';
import { objectGroupAnalysis } from '../services/api';

const MultiPhotoAnalyzer = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [objects, setObjects] = useState([]);
  const [locationHint, setLocationHint] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResults, setAnalysisResults] = useState(null);
  const [error, setError] = useState(null);
  const { enqueueSnackbar } = useSnackbar();

  const steps = [
    {
      label: 'Группировка фотографий',
      description: 'Создайте группы объектов и добавьте фотографии',
      icon: <PhotoCameraIcon />
    },
    {
      label: 'Анализ координат',
      description: 'Запустите анализ для определения координат',
      icon: <AnalyticsIcon />
    },
    {
      label: 'Результаты',
      description: 'Просмотрите результаты анализа на карте',
      icon: <MapIcon />
    }
  ];

  const handleObjectsChange = (newObjects) => {
    setObjects(newObjects);
    console.log('📊 Objects updated:', newObjects);
  };

  const handleNext = () => {
    if (activeStep === 0) {
      // Проверяем, что есть хотя бы один объект с фотографиями
      if (objects.length === 0) {
        enqueueSnackbar('Создайте хотя бы один объект', { variant: 'warning' });
        return;
      }
      
      const hasPhotos = objects.some(obj => obj.files.length > 0);
      if (!hasPhotos) {
        enqueueSnackbar('Добавьте фотографии к объектам', { variant: 'warning' });
        return;
      }
    }
    
    setActiveStep((prevStep) => prevStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevStep) => prevStep - 1);
  };

  const handleAnalyze = async () => {
    if (objects.length === 0) {
      enqueueSnackbar('Нет объектов для анализа', { variant: 'error' });
      return;
    }

    setIsAnalyzing(true);
    setError(null);

    try {
      console.log('🚀 Starting multi-photo analysis for objects:', objects);
      
      const response = await objectGroupAnalysis.analyzeGroups(objects, locationHint);
      console.log('✅ Analysis completed:', response);
      
      // Правильная структура данных из backend (batch_detect возвращает data.results)
      const results = {
        results: response.data.data?.results || response.data.results || [],
        summary: response.data.data?.summary || response.data.summary || {}
      };
      
      setAnalysisResults(results);
      enqueueSnackbar(`Анализ завершен! Обработано ${results.results.length} объектов`, { 
        variant: 'success' 
      });
      
      // Переходим к результатам
      setActiveStep(2);
      
    } catch (error) {
      console.error('❌ Analysis failed:', error);
      setError(error.message || 'Ошибка при анализе координат');
      enqueueSnackbar('Ошибка при анализе координат', { variant: 'error' });
    } finally {
      setIsAnalyzing(false);
    }
  };

  const renderStepContent = (step) => {
    switch (step) {
      case 0:
        return (
          <Box>
            <ObjectGrouper 
              onObjectsChange={handleObjectsChange}
              locationHint={locationHint}
              setLocationHint={setLocationHint}
              maxObjects={5}
              maxFilesPerObject={10}
            />
            <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="body2" color="text.secondary">
                Объектов: {objects.length} | 
                Всего фото: {objects.reduce((sum, obj) => sum + obj.files.length, 0)}
              </Typography>
              <Button
                variant="contained"
                onClick={handleNext}
                disabled={objects.length === 0 || !objects.some(obj => obj.files.length > 0)}
                endIcon={<AnalyticsIcon />}
              >
                Перейти к анализу
              </Button>
            </Box>
          </Box>
        );
      
      case 1:
        return (
          <Box>
            <Alert severity="info" sx={{ mb: 3 }}>
              Система проанализирует {objects.length} объектов с общим количеством {objects.reduce((sum, obj) => sum + obj.files.length, 0)} фотографий.
              Для каждого объекта будут агрегированы координаты из всех фотографий для повышения точности.
            </Alert>

            <TextField
              fullWidth
              label="Подсказка местоположения (необязательно)"
              placeholder="Например: Москва, Красная площадь"
              value={locationHint}
              onChange={(e) => setLocationHint(e.target.value)}
              sx={{ mb: 3 }}
              helperText="Укажите примерное местоположение для улучшения точности анализа"
            />

            {/* Превью объектов */}
            <Typography variant="h6" gutterBottom>
              Объекты для анализа:
            </Typography>
            <Grid container spacing={2} sx={{ mb: 3 }}>
              {objects.map((obj) => (
                <Grid item xs={12} sm={6} md={4} key={obj.id}>
                  <Card>
                    <CardContent>
                      <Typography variant="subtitle1" noWrap>
                        {obj.name}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {obj.files.length} фото
                      </Typography>
                      <Box sx={{ mt: 1, display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {obj.files.slice(0, 3).map((fileData, index) => (
                          <Chip 
                            key={index}
                            label={fileData.file.name.split('.')[0]}
                            size="small"
                            variant="outlined"
                          />
                        ))}
                        {obj.files.length > 3 && (
                          <Chip 
                            label={`+${obj.files.length - 3}`}
                            size="small"
                            color="primary"
                          />
                        )}
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>

            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Button onClick={handleBack}>
                Назад
              </Button>
              <Button
                variant="contained"
                onClick={handleAnalyze}
                disabled={isAnalyzing}
                startIcon={isAnalyzing ? <CircularProgress size={20} /> : <AnalyticsIcon />}
              >
                {isAnalyzing ? 'Анализ...' : 'Начать анализ'}
              </Button>
            </Box>

            {error && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {error}
              </Alert>
            )}
          </Box>
        );
      
      case 2:
        return (
          <Box>
            {analysisResults ? (
              <Box>
                <Alert severity="success" sx={{ mb: 3 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <CheckCircleIcon />
                    <Typography>
                      Анализ завершен! Обработано {analysisResults.results?.length || 0} объектов
                    </Typography>
                  </Box>
                </Alert>

                {/* Результаты по объектам */}
                <Typography variant="h6" gutterBottom>
                  Результаты анализа:
                </Typography>
                
                {analysisResults.results?.map((result, index) => (
                  <Accordion key={index} defaultExpanded={index === 0}>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
                        <Typography variant="subtitle1">
                          {result.object_name}
                        </Typography>
                        {result.coordinates ? (
                          <Chip 
                            label={`${Math.round(result.confidence * 100)}% точность`} 
                            color="success" 
                            size="small" 
                          />
                        ) : (
                          <Chip 
                            label="Координаты не найдены" 
                            color="error" 
                            size="small" 
                          />
                        )}
                        <Typography variant="body2" color="text.secondary" sx={{ ml: 'auto' }}>
                          {result.files_processed} фото
                        </Typography>
                      </Box>
                    </AccordionSummary>
                    <AccordionDetails>
                      <Grid container spacing={2}>
                        <Grid item xs={12} md={6}>
                          <Typography variant="body2" paragraph>
                            <strong>Описание:</strong> {result.object_description || 'Не указано'}
                          </Typography>
                          {result.coordinates && (
                            <Typography variant="body2" paragraph>
                              <strong>Координаты:</strong> {result.coordinates.latitude?.toFixed(6)}, {result.coordinates.longitude?.toFixed(6)}
                            </Typography>
                          )}
                          <Typography variant="body2" paragraph>
                            <strong>Источник:</strong> {result.source}
                          </Typography>
                          <Typography variant="body2" paragraph>
                            <strong>Сообщение:</strong> {result.message}
                          </Typography>
                          <Typography variant="body2">
                            <strong>Источники координат:</strong> {result.coordinate_sources?.length || 0}
                          </Typography>
                        </Grid>
                        <Grid item xs={12} md={6}>
                          {result.coordinate_sources && result.coordinate_sources.length > 0 && (
                            <Box>
                              <Typography variant="body2" gutterBottom>
                                <strong>Источники координат:</strong>
                              </Typography>
                              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                                {result.coordinate_sources.map((source, sourceIndex) => (
                                  <Chip 
                                    key={sourceIndex}
                                    label={`${source.source} (${Math.round(source.confidence * 100)}%)`}
                                    size="small"
                                    variant="outlined"
                                  />
                                ))}
                              </Box>
                            </Box>
                          )}
                          {result.objects && Object.keys(result.objects).length > 0 && (
                            <Box sx={{ mt: 2 }}>
                              <Typography variant="body2" gutterBottom>
                                <strong>Обнаруженные объекты:</strong>
                              </Typography>
                              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                {Object.entries(result.objects).map(([objName, objData], objIndex) => (
                                  <Chip 
                                    key={objIndex}
                                    label={`${objName} (${objData.count})`}
                                    size="small"
                                    variant="outlined"
                                  />
                                ))}
                              </Box>
                            </Box>
                          )}
                        </Grid>
                      </Grid>
                    </AccordionDetails>
                  </Accordion>
                ))}

                {/* Карта с результатами */}
                <Box sx={{ mt: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    Карта результатов:
                  </Typography>
                  <Paper sx={{ height: 400, overflow: 'hidden' }}>
                    <InteractiveResultsMap 
                      results={analysisResults.results?.filter(r => r.coordinates).map(r => ({
                        ...r,
                        lat: r.coordinates.latitude,
                        lon: r.coordinates.longitude,
                        category: r.object_name,
                        confidence: Math.round(r.confidence * 100)
                      })) || []}
                      mapId="multi-photo-results-map"
                    />
                  </Paper>
                </Box>

                <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between' }}>
                  <Button onClick={() => setActiveStep(0)}>
                    Новый анализ
                  </Button>
                  <Button variant="outlined" onClick={handleBack}>
                    Назад к анализу
                  </Button>
                </Box>
              </Box>
            ) : (
              <Alert severity="info">
                Результаты анализа будут отображены здесь
              </Alert>
            )}
          </Box>
        );
      
      default:
        return null;
    }
  };

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto', p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Анализ координат по нескольким фото
      </Typography>
      
      <Typography variant="body1" color="text.secondary" paragraph>
        Загрузите несколько фотографий одного объекта с разных ракурсов для повышения точности определения координат
      </Typography>

      <Paper sx={{ p: 3 }}>
        <Stepper activeStep={activeStep} orientation="vertical">
          {steps.map((step, index) => (
            <Step key={step.label}>
              <StepLabel
                optional={
                  index === 2 ? (
                    <Typography variant="caption">Последний шаг</Typography>
                  ) : null
                }
                StepIconComponent={() => (
                  <Box
                    sx={{
                      width: 40,
                      height: 40,
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      bgcolor: activeStep >= index ? 'primary.main' : 'grey.300',
                      color: activeStep >= index ? 'white' : 'grey.600'
                    }}
                  >
                    {step.icon}
                  </Box>
                )}
              >
                {step.label}
              </StepLabel>
              <StepContent>
                <Typography sx={{ mb: 2 }}>{step.description}</Typography>
                {renderStepContent(index)}
              </StepContent>
            </Step>
          ))}
        </Stepper>
      </Paper>
    </Box>
  );
};

export default MultiPhotoAnalyzer;
