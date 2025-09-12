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
import api from '../services/api';

const GoogleVisionAnalyzer = () => {
  const [files, setFiles] = useState([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResults, setAnalysisResults] = useState([]);
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

  const analyzeWithGoogleVision = async (endpoint, file, title) => {
    const formData = new FormData();
    formData.append('image', file);
    
    try {
      const response = await api.post(`/api/geo/google-vision/${endpoint}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      return {
        success: true,
        title,
        data: response.data,
        file: file.name
      };
    } catch (error) {
      console.error(`Google Vision ${title} error:`, error);
      return {
        success: false,
        title,
        error: error.response?.data?.error || error.message,
        file: file.name
      };
    }
  };

  const handleAnalyze = async () => {
    if (files.length === 0) {
      setError('Пожалуйста, загрузите изображения для анализа');
      return;
    }

    setIsAnalyzing(true);
    setError(null);
    const results = [];

    for (const file of files) {
      // Выполняем все типы анализа параллельно
      const analyses = await Promise.all([
        analyzeWithGoogleVision('analyze', file, 'Общий анализ'),
        analyzeWithGoogleVision('violations', file, 'Детекция нарушений'),
        analyzeWithGoogleVision('address', file, 'Извлечение адреса'),
        analyzeWithGoogleVision('property', file, 'Анализ недвижимости')
      ]);

      results.push({
        file: file.name,
        preview: file.preview,
        analyses
      });
    }

    setAnalysisResults(results);
    setIsAnalyzing(false);
  };

  const clearFiles = () => {
    files.forEach(file => URL.revokeObjectURL(file.preview));
    setFiles([]);
    setAnalysisResults([]);
    setError(null);
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.gif', '.bmp', '.webp']
    },
    multiple: true
  });

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'info';
      default: return 'default';
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <AIIcon color="primary" />
        Google Vision Анализатор
      </Typography>
      
      <Typography variant="body1" color="text.secondary" paragraph>
        Продвинутый анализ изображений с помощью Mistral AI
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper
            {...getRootProps()}
            sx={{
              p: 4,
              textAlign: 'center',
              cursor: 'pointer',
              border: '2px dashed',
              borderColor: isDragActive ? 'primary.main' : 'grey.300',
              bgcolor: isDragActive ? 'action.hover' : 'background.paper',
              transition: 'all 0.3s ease'
            }}
          >
            <input {...getInputProps()} />
            {isAnalyzing ? (
              <Box textAlign="center">
                <CircularProgress color="primary" />
                <Typography>Анализ с помощью Google Vision...</Typography>
              </Box>
            ) : (
              <Box textAlign="center">
                <UploadIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  {isDragActive ? 'Отпустите файлы здесь' : 'Перетащите изображения или нажмите для выбора'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Поддерживаются: JPEG, PNG, GIF, BMP, WebP
                </Typography>
              </Box>
            )}
          </Paper>

          {files.length > 0 && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle1" gutterBottom>
                Загружено файлов: {files.length}
              </Typography>
              <Grid container spacing={1}>
                {files.map((file) => (
                  <Grid item xs={4} key={file.id}>
                    <Card>
                      <Box sx={{ height: 100, overflow: 'hidden' }}>
                        <img
                          src={file.preview}
                          alt={file.name}
                          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                        />
                      </Box>
                      <CardContent sx={{ p: 1 }}>
                        <Typography variant="caption" noWrap>
                          {file.name}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>

              <Button
                variant="contained"
                onClick={handleAnalyze}
                disabled={isAnalyzing}
                startIcon={<AIIcon />}
                sx={{ mt: 2, width: '100%' }}
              >
                {isAnalyzing ? 'Анализируем...' : 'Анализировать с Google Vision'}
              </Button>
            </Box>
          )}

          {files.length > 0 && (
            <Button
              variant="outlined"
              onClick={clearFiles}
              sx={{ mt: 1, width: '100%' }}
            >
              Очистить
            </Button>
          )}
        </Grid>

        <Grid item xs={12} md={6}>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          {analysisResults.length > 0 && (
            <Box>
              <Typography variant="h6" gutterBottom>
                Результаты анализа Google Vision
              </Typography>
              
              {analysisResults.map((result, index) => (
                <Card key={index} sx={{ mb: 2 }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                      <Box sx={{ width: 60, height: 60, overflow: 'hidden', borderRadius: 1 }}>
                        <img
                          src={result.preview}
                          alt={result.file}
                          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                        />
                      </Box>
                      <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                        {result.file}
                      </Typography>
                    </Box>

                    {result.analyses.map((analysis, analysisIndex) => (
                      <Accordion key={analysisIndex} sx={{ mb: 1 }}>
                        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
                            {analysis.success ? (
                              <CheckIcon color="success" />
                            ) : (
                              <WarningIcon color="error" />
                            )}
                            <Typography variant="subtitle2">
                              {analysis.title}
                            </Typography>
                            <Box sx={{ flexGrow: 1 }} />
                            <Chip
                              size="small"
                              label={analysis.success ? 'Успешно' : 'Ошибка'}
                              color={analysis.success ? 'success' : 'error'}
                            />
                          </Box>
                        </AccordionSummary>
                        <AccordionDetails>
                          {analysis.success ? (
                            <Box>
                              {analysis.title === 'Детекция нарушений' && analysis.data.violations && (
                                <Box>
                                  <Typography variant="body2" gutterBottom>
                                    Обнаружено нарушений: {analysis.data.violations.length}
                                  </Typography>
                                  {analysis.data.violations.map((violation, vIndex) => (
                                    <Box key={vIndex} sx={{ mb: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                                      <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
                                        <Chip
                                          label={violation.type}
                                          size="small"
                                          color={getSeverityColor(violation.severity)}
                                        />
                                        <Chip
                                          label={`${Math.round(violation.confidence)}%`}
                                          size="small"
                                          variant="outlined"
                                        />
                                      </Box>
                                      <Typography variant="body2">
                                        {violation.description}
                                      </Typography>
                                    </Box>
                                  ))}
                                </Box>
                              )}
                              
                              {analysis.data.analysis && (
                                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                                  {analysis.data.analysis}
                                </Typography>
                              )}
                              
                              <Divider sx={{ my: 2 }} />
                              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                                <Chip 
                                  label={`Модель: ${analysis.data.model || 'Google Vision'}`}
                                  size="small"
                                  variant="outlined"
                                />
                                <Chip 
                                  label="Google Cloud"
                                  size="small"
                                  color="primary"
                                  variant="outlined"
                                />
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

export default GoogleVisionAnalyzer;
