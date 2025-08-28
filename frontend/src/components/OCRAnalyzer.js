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
  LocationOn as LocationIcon,
  Business as BusinessIcon,
  Phone as PhoneIcon
} from '@mui/icons-material';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api/v1';

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
  const [textInput, setTextInput] = useState('');
  const [addressResults, setAddressResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
    setError('');
    setAddressResults(null);
  };

  const handleTextAnalysis = async () => {
    if (!textInput.trim()) {
      setError('Пожалуйста, введите текст для анализа');
      return;
    }

    setLoading(true);
    setError('');
    setAddressResults(null);

    try {
      const response = await axios.post(`${API_URL}/ocr/analyze-address`, {
        text: textInput
      });
      
      setAddressResults(response.data.data);
    } catch (err) {
      setError(err.response?.data?.error || 'Ошибка анализа текста');
    } finally {
      setLoading(false);
    }
  };

  const handleImageUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setLoading(true);
    setError('');
    setAddressResults(null);

    const formData = new FormData();
    formData.append('image', file);

    try {
      const response = await axios.post(`${API_URL}/ocr/analyze-address-image`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      setAddressResults(response.data.data);
    } catch (err) {
      setError(err.response?.data?.error || 'Ошибка анализа изображения');
    } finally {
      setLoading(false);
    }
  };

  const renderAddressResults = () => {
    if (!addressResults) return null;

    return (
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                <LocationIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                Результаты анализа адресов
              </Typography>
              
              {addressResults.addresses && addressResults.addresses.length > 0 && (
                <Box mb={2}>
                  <Typography variant="subtitle2" gutterBottom>Адреса:</Typography>
                  {addressResults.addresses.map((address, index) => (
                    <Chip 
                      key={index} 
                      label={address} 
                      icon={<LocationIcon />}
                      sx={{ mr: 0.5, mb: 0.5 }} 
                    />
                  ))}
                </Box>
              )}

              {addressResults.building_names && addressResults.building_names.length > 0 && (
                <Box mb={2}>
                  <Typography variant="subtitle2" gutterBottom>Названия зданий:</Typography>
                  {addressResults.building_names.map((name, index) => (
                    <Chip 
                      key={index} 
                      label={name} 
                      icon={<BusinessIcon />}
                      sx={{ mr: 0.5, mb: 0.5 }} 
                    />
                  ))}
                </Box>
              )}

              {addressResults.street_numbers && addressResults.street_numbers.length > 0 && (
                <Box mb={2}>
                  <Typography variant="subtitle2" gutterBottom>Номера домов:</Typography>
                  {addressResults.street_numbers.map((number, index) => (
                    <Chip 
                      key={index} 
                      label={number} 
                      sx={{ mr: 0.5, mb: 0.5 }} 
                    />
                  ))}
                </Box>
              )}

              {addressResults.organizations && addressResults.organizations.length > 0 && (
                <Box mb={2}>
                  <Typography variant="subtitle2" gutterBottom>Организации:</Typography>
                  {addressResults.organizations.map((org, index) => (
                    <Chip 
                      key={index} 
                      label={org} 
                      icon={<BusinessIcon />}
                      sx={{ mr: 0.5, mb: 0.5 }} 
                    />
                  ))}
                </Box>
              )}

              {addressResults.phone_numbers && addressResults.phone_numbers.length > 0 && (
                <Box mb={2}>
                  <Typography variant="subtitle2" gutterBottom>Телефоны:</Typography>
                  {addressResults.phone_numbers.map((phone, index) => (
                    <Chip 
                      key={index} 
                      label={phone} 
                      icon={<PhoneIcon />}
                      sx={{ mr: 0.5, mb: 0.5 }} 
                    />
                  ))}
                </Box>
              )}

              {addressResults.confidence_score && (
                <Typography variant="body2" color="textSecondary">
                  Уверенность: {(addressResults.confidence_score * 100).toFixed(1)}%
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    );
  };

  return (
    <Paper sx={{ width: '100%', mt: 2 }}>
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="OCR анализ">
          <Tab 
            label="Анализ текста" 
            icon={<TextIcon />} 
            iconPosition="start"
          />
          <Tab 
            label="Анализ изображения" 
            icon={<UploadIcon />} 
            iconPosition="start"
          />
        </Tabs>
      </Box>

      <TabPanel value={tabValue} index={0}>
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <TextField
              fullWidth
              multiline
              rows={6}
              variant="outlined"
              label="Введите текст для анализа адресов"
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              placeholder="Вставьте текст, содержащий адреса, названия зданий или организаций..."
            />
          </Grid>
          
          <Grid item xs={12}>
            <Button
              variant="contained"
              onClick={handleTextAnalysis}
              disabled={loading || !textInput.trim()}
              startIcon={loading ? <CircularProgress size={20} /> : <TextIcon />}
            >
              {loading ? 'Анализ...' : 'Анализировать текст'}
            </Button>
          </Grid>

          {error && (
            <Grid item xs={12}>
              <Alert severity="error">{error}</Alert>
            </Grid>
          )}

          {addressResults && (
            <Grid item xs={12}>
              {renderAddressResults()}
            </Grid>
          )}
        </Grid>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Box
              sx={{
                border: '2px dashed #ccc',
                borderRadius: 2,
                p: 4,
                textAlign: 'center',
                cursor: 'pointer',
                '&:hover': {
                  borderColor: 'primary.main',
                  backgroundColor: 'action.hover'
                }
              }}
              onClick={() => fileInputRef.current?.click()}
            >
              <UploadIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                Загрузите изображение для анализа адресов
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Поддерживаются форматы: JPG, PNG, GIF, BMP
              </Typography>
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleImageUpload}
                accept="image/*"
                style={{ display: 'none' }}
              />
            </Box>
          </Grid>

          {loading && (
            <Grid item xs={12}>
              <Box display="flex" justifyContent="center" alignItems="center" p={3}>
                <CircularProgress />
                <Typography variant="body1" sx={{ ml: 2 }}>
                  Анализ изображения...
                </Typography>
              </Box>
            </Grid>
          )}

          {error && (
            <Grid item xs={12}>
              <Alert severity="error">{error}</Alert>
            </Grid>
          )}

          {addressResults && (
            <Grid item xs={12}>
              {renderAddressResults()}
            </Grid>
          )}
        </Grid>
      </TabPanel>
    </Paper>
  );
};

export default OCRAnalyzer;
