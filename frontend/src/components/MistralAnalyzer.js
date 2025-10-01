import React, { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Paper,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  Chip,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  Divider
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Psychology as AIIcon,
  ExpandMore as ExpandMoreIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import { violationApi } from '../services/api';
import ReferenceValidation from './ReferenceValidation';

const AIAnalyzer = () => {
  const [files, setFiles] = useState([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResults, setAnalysisResults] = useState([]);
  const [referenceValidationResults, setReferenceValidationResults] = useState([]);
  const [error, setError] = useState(null);

  const onDrop = (acceptedFiles) => {
    const newFiles = acceptedFiles.map(file => ({
      ...file,
      id: Math.random().toString(36).substr(2, 9),
      preview: URL.createObjectURL(file)
    }));
    setFiles(prev => [...prev, ...newFiles]);
    setError(null);
  };

  const analyzeWithMistral = async (endpoint, file, title) => {
    const formData = new FormData();
    formData.append('image', file);
    
    try {
      const response = await api.post(`/api/geo/mistral/${endpoint}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      return {
        title,
        endpoint,
        success: response.data.success,
        data: response.data,
        fileName: file.name
      };
    } catch (error) {
      return {
        title,
        endpoint,
        success: false,
        error: error.response?.data?.error || error.message,
        fileName: file.name
      };
    }
  };

  const handleAnalyze = async () => {
    if (files.length === 0) {
      setError('Выберите изображения для анализа');
      return;
    }

    setIsAnalyzing(true);
    setError(null);
    const results = [];

    for (const file of files) {
      // Выполняем все типы анализа параллельно
      const analyses = await Promise.all([
        analyzeWithMistral('analyze', file, 'Общий анализ'),
        analyzeWithMistral('violations', file, 'Детекция нарушений'),
        analyzeWithMistral('address', file, 'Извлечение адреса'),
        analyzeWithMistral('property', file, 'Анализ недвижимости')
      ]);

      results.push({
        fileName: file.name,
        preview: file.preview,
        analyses
      });
    }

    setAnalysisResults(results);
    setIsAnalyzing(false);
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'info';
      default: return 'default';
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {'image/*': ['.jpeg', '.jpg', '.png', '.gif']},
    maxFiles: 5,
    multiple: true
  });

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <AIIcon color="secondary" />
         AI Анализатор
      </Typography>
      
      <Typography variant="body1" color="text.secondary" paragraph>
        Продвинутый анализ изображений с помощью AI технологий
      </Typography>

      <Grid container spacing={3}>
        {/* Загрузка файлов */}
        <Grid item xs={12} md={6}>
          <Paper 
            variant="outlined" 
            sx={{ 
              p: 3, 
              border: '2px dashed',
              borderColor: 'divider',
              height: 200,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              '&:hover': { borderColor: 'secondary.main' },
              ...(isDragActive && { borderColor: 'secondary.main' })
            }}
            {...getRootProps()}
          >
            <input {...getInputProps()} />
            
            {isAnalyzing ? (
              <Box textAlign="center">
                <CircularProgress color="secondary" />
                <Typography>Анализ с помощью AI...</Typography>
              </Box>
            ) : (
              <Box textAlign="center">
                <UploadIcon sx={{ fontSize: 48, mb: 1, color: 'secondary.main' }} />
                <Typography variant="h6" gutterBottom>
                  {isDragActive ? 'Отпустите изображения' : 'Загрузите изображения'}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Поддерживаются: JPG, PNG, GIF (до 5 файлов)
                </Typography>
              </Box>
            )}
          </Paper>

          {files.length > 0 && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Загружено файлов: {files.length}
              </Typography>
              <Grid container spacing={1}>
                {files.map((file) => (
                  <Grid item xs={6} key={file.id}>
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
                  </Grid>
                ))}
              </Grid>
              
              <Button
                variant="contained"
                color="secondary"
                onClick={handleAnalyze}
                disabled={isAnalyzing}
                startIcon={<AIIcon />}
                sx={{ mt: 2, width: '100%' }}
              >
                {isAnalyzing ? 'Анализируем...' : 'Анализировать с AI'}
              </Button>
            </Box>
          )}

          {error && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {error}
            </Alert>
          )}
        </Grid>

        {/* Результаты анализа */}
        <Grid item xs={12} md={6}>
          <Typography variant="h6" gutterBottom>
            Результаты анализа
          </Typography>
          
          {analysisResults.length === 0 ? (
            <Paper sx={{ p: 3, textAlign: 'center' }}>
              <Typography color="text.secondary">
                Результаты анализа появятся здесь
              </Typography>
            </Paper>
          ) : (
            <Box sx={{ maxHeight: 600, overflowY: 'auto' }}>
              {analysisResults.map((result, index) => (
                <Card key={index} sx={{ mb: 2 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      {result.fileName}
                    </Typography>
                    
                    {result.analyses.map((analysis, aIndex) => (
                      <Accordion key={aIndex} sx={{ mb: 1 }}>
                        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Typography variant="subtitle1">
                              {analysis.title}
                            </Typography>
                            <Chip 
                              label={analysis.success ? 'Успешно' : 'Ошибка'}
                              color={analysis.success ? 'success' : 'error'}
                              size="small"
                            />
                          </Box>
                        </AccordionSummary>
                        
                        <AccordionDetails>
                          {analysis.success ? (
                            <Box>
                              {/* Результаты детекции нарушений */}
                              {analysis.endpoint === 'violations' && analysis.data.analysis && (
                                <Box>
                                  {JSON.parse(analysis.data.analysis).violations?.map((violation, vIndex) => (
                                    <Box key={vIndex} sx={{ mb: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                                        <WarningIcon color={getSeverityColor(violation.severity)} />
                                        <Typography variant="subtitle2">
                                          {violation.type}
                                        </Typography>
                                        <Chip 
                                          label={`${Math.round(violation.confidence * 100)}%`}
                                          color={getSeverityColor(violation.severity)}
                                          size="small"
                                        />
                                      </Box>
                                      <Typography variant="body2" color="text.secondary">
                                        {violation.description}
                                      </Typography>
                                    </Box>
                                  ))}
                                  
                                  {JSON.parse(analysis.data.analysis).recommendations && (
                                    <Box sx={{ mt: 2 }}>
                                      <Typography variant="subtitle2" gutterBottom>
                                        Рекомендации:
                                      </Typography>
                                      <List dense>
                                        {JSON.parse(analysis.data.analysis).recommendations.map((rec, rIndex) => (
                                          <ListItem key={rIndex}>
                                            <ListItemText primary={rec} />
                                          </ListItem>
                                        ))}
                                      </List>
                                    </Box>
                                  )}
                                  
                                  {/* Валидация против готовой базы данных заказчика */}
                                  {analysis.endpoint === 'violations' && analysis.data.coordinates && (
                                    <ReferenceValidation
                                      coordinates={analysis.data.coordinates}
                                      violations={JSON.parse(analysis.data.analysis).violations || []}
                                      onValidationComplete={(validationResult) => {
                                        console.log('🎯 Валидация завершена:', validationResult);
                                      }}
                                    />
                                  )}
                                </Box>
                              )}
                              
                              {/* Общий анализ */}
                              {analysis.endpoint === 'analyze' && (
                                <Typography variant="body2">
                                  {analysis.data.analysis || 'Анализ завершен'}
                                </Typography>
                              )}
                              
                              {/* Извлечение адреса */}
                              {analysis.endpoint === 'address' && (
                                <Box>
                                  <Typography variant="body2">
                                    <strong>Адрес:</strong> {analysis.data.address || 'Не определен'}
                                  </Typography>
                                  {analysis.data.confidence && (
                                    <Typography variant="caption" color="text.secondary">
                                      Уверенность: {Math.round(analysis.data.confidence * 100)}%
                                    </Typography>
                                  )}
                                </Box>
                              )}
                              
                              {/* Анализ недвижимости */}
                              {analysis.endpoint === 'property' && (
                                <Box>
                                  <Typography variant="body2">
                                    <strong>Тип:</strong> {analysis.data.property_type || 'Не определен'}
                                  </Typography>
                                  <Typography variant="body2">
                                    <strong>Описание:</strong> {analysis.data.description || 'Нет описания'}
                                  </Typography>
                                </Box>
                              )}
                              
                              {/* Метаданные */}
                              <Divider sx={{ my: 2 }} />
                              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                                <Chip 
                                  label={`Модель: ${analysis.data.model || 'AI'}`}
                                  size="small"
                                  variant="outlined"
                                />
                                {analysis.data.tokens_used && (
                                  <Chip 
                                    label={`Токены: ${analysis.data.tokens_used}`}
                                    size="small"
                                    variant="outlined"
                                  />
                                )}
                              </Box>
                            </Box>
                          ) : (
                            <Alert severity="error">
                              <Typography variant="body2">
                                {analysis.error}
                              </Typography>
                            </Alert>
                          )}
                        </AccordionDetails>
                      </Accordion>
                    ))}
                  </CardContent>
                </Card>
              ))}
            </Box>
          )}
        </Grid>
      </Grid>
    </Box>
  );
};

export default AIAnalyzer;
