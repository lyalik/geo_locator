import React, { useState, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  Tabs,
  Tab,
  Button,
  TextField,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  Chip,
  List,
  ListItem,
  ListItemText
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  TextFields as TextIcon,
  Search as SearchIcon,
  Description as DocumentIcon,
  Warning as WarningIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import api from '../config/api';

function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`ocr-tabpanel-${index}`}
      aria-labelledby={`ocr-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const OCRAnalyzer = () => {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [textInput, setTextInput] = useState('');
  
  const fileInputRef = useRef(null);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
    setError(null);
    setResults(null);
  };

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    setSelectedFile(file);
    setError(null);
  };

  const analyzeDocument = async () => {
    if (!selectedFile) {
      setError('Пожалуйста, выберите файл');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await api.post('/ocr/analyze-document', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setResults(response.data.data);
    } catch (err) {
      setError(err.response?.data?.error || 'Ошибка анализа документа');
    } finally {
      setLoading(false);
    }
  };

  const extractText = async () => {
    if (!selectedFile) {
      setError('Пожалуйста, выберите файл');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await api.post('/ocr/extract-text', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setResults(response.data.data);
    } catch (err) {
      setError(err.response?.data?.error || 'Ошибка извлечения текста');
    } finally {
      setLoading(false);
    }
  };

  const analyzeViolationText = async () => {
    if (!textInput.trim()) {
      setError('Пожалуйста, введите текст для анализа');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await api.post('/ocr/analyze-violation', {
        text: textInput
      });

      setResults(response.data.data);
    } catch (err) {
      setError(err.response?.data?.error || 'Ошибка анализа нарушений');
    } finally {
      setLoading(false);
    }
  };

  const analyzeViolationImage = async () => {
    if (!selectedFile) {
      setError('Пожалуйста, выберите файл');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await api.post('/ocr/analyze-violation-image', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setResults(response.data.data);
    } catch (err) {
      setError(err.response?.data?.error || 'Ошибка анализа изображения на нарушения');
    } finally {
      setLoading(false);
    }
  };

  const renderDocumentAnalysis = () => {
    if (!results) return null;

    return (
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <DocumentIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Анализ документа
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    Тип документа: <strong>{results.document_type}</strong>
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    Языки: {results.detected_languages.map(lang => (
                      <Chip key={lang} label={lang} size="small" sx={{ ml: 0.5 }} />
                    ))}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    Текстовых областей: <strong>{results.metadata.total_regions}</strong>
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    Средняя точность: <strong>{(results.metadata.avg_confidence * 100).toFixed(1)}%</strong>
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <TextIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Извлеченный текст
              </Typography>
              <TextField
                multiline
                rows={10}
                fullWidth
                value={results.full_text}
                variant="outlined"
                InputProps={{ readOnly: true }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <InfoIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Ключевая информация
              </Typography>
              {results.key_information.dates && results.key_information.dates.length > 0 && (
                <Box mb={2}>
                  <Typography variant="subtitle2">Даты:</Typography>
                  {results.key_information.dates.map((date, index) => (
                    <Chip key={index} label={date} size="small" sx={{ mr: 0.5, mb: 0.5 }} />
                  ))}
                </Box>
              )}
              {results.key_information.addresses && results.key_information.addresses.length > 0 && (
                <Box mb={2}>
                  <Typography variant="subtitle2">Адреса:</Typography>
                  {results.key_information.addresses.map((address, index) => (
                    <Chip key={index} label={address} size="small" sx={{ mr: 0.5, mb: 0.5 }} />
                  ))}
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    );
  };

  const renderViolationAnalysis = () => {
    if (!results) return null;

    const isViolationRelated = results.is_violation_related;

    return (
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Alert 
            severity={isViolationRelated ? "warning" : "info"}
            icon={isViolationRelated ? <WarningIcon /> : <InfoIcon />}
          >
            {isViolationRelated 
              ? `Обнаружены признаки нарушения (уверенность: ${(results.confidence_score * 100).toFixed(1)}%)`
              : `Признаки нарушения не обнаружены (уверенность: ${(results.confidence_score * 100).toFixed(1)}%)`
            }
          </Alert>
        </Grid>

        {results.violation_keywords && results.violation_keywords.length > 0 && (
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom color="warning.main">
                  <WarningIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Ключевые слова нарушений
                </Typography>
                <Box>
                  {results.violation_keywords.map((keyword, index) => (
                    <Chip 
                      key={index} 
                      label={keyword} 
                      color="warning" 
                      size="small" 
                      sx={{ mr: 0.5, mb: 0.5 }} 
                    />
                  ))}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        )}

        {results.addresses && results.addresses.length > 0 && (
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <InfoIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Адреса
                </Typography>
                <List dense>
                  {results.addresses.map((address, index) => (
                    <ListItem key={index}>
                      <ListItemText primary={address} />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    );
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        OCR Анализ
      </Typography>
      
      <Paper sx={{ width: '100%' }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab label="Анализ документа" />
          <Tab label="Извлечение текста" />
          <Tab label="Анализ нарушений (текст)" />
          <Tab label="Анализ нарушений (изображение)" />
        </Tabs>

        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Загрузка документа для анализа
                  </Typography>
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileSelect}
                    accept="image/*"
                    style={{ display: 'none' }}
                  />
                  <Button
                    variant="outlined"
                    startIcon={<UploadIcon />}
                    onClick={() => fileInputRef.current?.click()}
                    sx={{ mr: 2 }}
                  >
                    Выбрать файл
                  </Button>
                  {selectedFile && (
                    <Typography variant="body2" sx={{ mt: 1 }}>
                      Выбран файл: {selectedFile.name}
                    </Typography>
                  )}
                  <Button
                    variant="contained"
                    onClick={analyzeDocument}
                    disabled={!selectedFile || loading}
                    sx={{ ml: 2 }}
                  >
                    {loading ? <CircularProgress size={24} /> : 'Анализировать документ'}
                  </Button>
                </CardContent>
              </Card>
            </Grid>
            {error && (
              <Grid item xs={12}>
                <Alert severity="error">{error}</Alert>
              </Grid>
            )}
            {results && renderDocumentAnalysis()}
          </Grid>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Извлечение текста из изображения
                  </Typography>
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileSelect}
                    accept="image/*"
                    style={{ display: 'none' }}
                  />
                  <Button
                    variant="outlined"
                    startIcon={<UploadIcon />}
                    onClick={() => fileInputRef.current?.click()}
                    sx={{ mr: 2 }}
                  >
                    Выбрать файл
                  </Button>
                  {selectedFile && (
                    <Typography variant="body2" sx={{ mt: 1 }}>
                      Выбран файл: {selectedFile.name}
                    </Typography>
                  )}
                  <Button
                    variant="contained"
                    onClick={extractText}
                    disabled={!selectedFile || loading}
                    sx={{ ml: 2 }}
                  >
                    {loading ? <CircularProgress size={24} /> : 'Извлечь текст'}
                  </Button>
                </CardContent>
              </Card>
            </Grid>
            {error && (
              <Grid item xs={12}>
                <Alert severity="error">{error}</Alert>
              </Grid>
            )}
            {results && (
              <Grid item xs={12}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      <TextIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                      Результат извлечения текста
                    </Typography>
                    <TextField
                      multiline
                      rows={15}
                      fullWidth
                      value={results.text}
                      variant="outlined"
                      InputProps={{ readOnly: true }}
                    />
                  </CardContent>
                </Card>
              </Grid>
            )}
          </Grid>
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Анализ текста на наличие нарушений
                  </Typography>
                  <TextField
                    multiline
                    rows={6}
                    fullWidth
                    value={textInput}
                    onChange={(e) => setTextInput(e.target.value)}
                    placeholder="Введите текст для анализа на наличие нарушений..."
                    variant="outlined"
                    sx={{ mb: 2 }}
                  />
                  <Button
                    variant="contained"
                    onClick={analyzeViolationText}
                    disabled={!textInput.trim() || loading}
                    startIcon={<SearchIcon />}
                  >
                    {loading ? <CircularProgress size={24} /> : 'Анализировать текст'}
                  </Button>
                </CardContent>
              </Card>
            </Grid>
            {error && (
              <Grid item xs={12}>
                <Alert severity="error">{error}</Alert>
              </Grid>
            )}
            {results && renderViolationAnalysis()}
          </Grid>
        </TabPanel>

        <TabPanel value={tabValue} index={3}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Анализ изображения на наличие нарушений
                  </Typography>
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileSelect}
                    accept="image/*"
                    style={{ display: 'none' }}
                  />
                  <Button
                    variant="outlined"
                    startIcon={<UploadIcon />}
                    onClick={() => fileInputRef.current?.click()}
                    sx={{ mr: 2 }}
                  >
                    Выбрать файл
                  </Button>
                  {selectedFile && (
                    <Typography variant="body2" sx={{ mt: 1 }}>
                      Выбран файл: {selectedFile.name}
                    </Typography>
                  )}
                  <Button
                    variant="contained"
                    onClick={analyzeViolationImage}
                    disabled={!selectedFile || loading}
                    sx={{ ml: 2 }}
                  >
                    {loading ? <CircularProgress size={24} /> : 'Анализировать изображение'}
                  </Button>
                </CardContent>
              </Card>
            </Grid>
            {error && (
              <Grid item xs={12}>
                <Alert severity="error">{error}</Alert>
              </Grid>
            )}
            {results && results.violation_analysis && (
              <Grid item xs={12}>
                <Alert 
                  severity={results.violation_analysis.is_violation_related ? "warning" : "info"}
                  icon={results.violation_analysis.is_violation_related ? <WarningIcon /> : <InfoIcon />}
                >
                  {results.violation_analysis.is_violation_related 
                    ? `Обнаружены признаки нарушения в документе (уверенность: ${(results.violation_analysis.confidence_score * 100).toFixed(1)}%)`
                    : `Признаки нарушения в документе не обнаружены (уверенность: ${(results.violation_analysis.confidence_score * 100).toFixed(1)}%)`
                  }
                </Alert>
              </Grid>
            )}
          </Grid>
        </TabPanel>
      </Paper>
    </Box>
  );
};

export default OCRAnalyzer;
