import React, { useState, useEffect } from 'react';
import {
  Box, Card, CardContent, Typography, TextField, Button, Grid,
  List, ListItem, ListItemText, ListItemIcon, Chip, Alert,
  Dialog, DialogTitle, DialogContent, DialogActions, Divider,
  CircularProgress, Accordion, AccordionSummary, AccordionDetails,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, IconButton, Tooltip
} from '@mui/material';
import {
  Search as SearchIcon, Home as HomeIcon, Business as BusinessIcon,
  Warning as WarningIcon, CheckCircle as CheckIcon, Info as InfoIcon,
  ExpandMore as ExpandMoreIcon, LocationOn as LocationIcon,
  Description as DescriptionIcon, Assessment as AssessmentIcon,
  GetApp as ExportIcon, Refresh as RefreshIcon
} from '@mui/icons-material';
import { api } from '../services/api';

const PropertyAnalyzer = ({ coordinates, onPropertySelect }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchType, setSearchType] = useState('address'); // 'address', 'cadastral', 'coordinates'
  const [properties, setProperties] = useState([]);
  const [selectedProperty, setSelectedProperty] = useState(null);
  const [analysisResults, setAnalysisResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showPropertyDialog, setShowPropertyDialog] = useState(false);
  const [validationResult, setValidationResult] = useState(null);

  // Auto-search when coordinates are provided
  useEffect(() => {
    if (coordinates && coordinates.lat && coordinates.lon) {
      searchByCoordinates(coordinates.lat, coordinates.lon);
    }
  }, [coordinates]);

  const searchByAddress = async () => {
    if (!searchQuery.trim()) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.get('/rosreestr/search/address', {
        params: { address: searchQuery }
      });
      
      if (response.data.success) {
        setProperties(response.data.properties);
      } else {
        setError('Не удалось найти объекты недвижимости');
      }
    } catch (err) {
      setError('Ошибка при поиске объектов недвижимости');
      console.error('Property search error:', err);
    } finally {
      setLoading(false);
    }
  };

  const searchByCadastralNumber = async () => {
    if (!searchQuery.trim()) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.get(`/rosreestr/property/${searchQuery}`);
      
      if (response.data.success) {
        setProperties([response.data.property]);
      } else {
        setError('Объект недвижимости не найден');
      }
    } catch (err) {
      setError('Ошибка при получении информации об объекте');
      console.error('Property info error:', err);
    } finally {
      setLoading(false);
    }
  };

  const searchByCoordinates = async (lat, lon, radius = 100) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.get('/rosreestr/search/coordinates', {
        params: { lat, lon, radius }
      });
      
      if (response.data.success) {
        setProperties(response.data.properties);
      } else {
        setError('Не удалось найти объекты в указанной области');
      }
    } catch (err) {
      setError('Ошибка при поиске объектов по координатам');
      console.error('Coordinate search error:', err);
    } finally {
      setLoading(false);
    }
  };

  const analyzeLocation = async (lat, lon) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.post('/rosreestr/analyze/location', {
        lat,
        lon,
        violation_types: ['unauthorized_construction', 'usage_violation', 'boundary_violation']
      });
      
      if (response.data.success) {
        setAnalysisResults(response.data);
      } else {
        setError('Не удалось провести анализ местоположения');
      }
    } catch (err) {
      setError('Ошибка при анализе местоположения');
      console.error('Location analysis error:', err);
    } finally {
      setLoading(false);
    }
  };

  const validatePropertyUsage = async (cadastralNumber, currentUsage) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.post('/rosreestr/validate/usage', {
        cadastral_number: cadastralNumber,
        current_usage: currentUsage
      });
      
      if (response.data.success) {
        setValidationResult(response.data.validation);
      } else {
        setError('Не удалось проверить соответствие использования');
      }
    } catch (err) {
      setError('Ошибка при проверке использования объекта');
      console.error('Usage validation error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    switch (searchType) {
      case 'address':
        searchByAddress();
        break;
      case 'cadastral':
        searchByCadastralNumber();
        break;
      case 'coordinates':
        if (coordinates) {
          searchByCoordinates(coordinates.lat, coordinates.lon);
        }
        break;
      default:
        break;
    }
  };

  const handlePropertyClick = (property) => {
    setSelectedProperty(property);
    setShowPropertyDialog(true);
    if (onPropertySelect) {
      onPropertySelect(property);
    }
  };

  const getPropertyIcon = (category) => {
    if (category.includes('жилая') || category.includes('дом')) {
      return <HomeIcon color="primary" />;
    } else if (category.includes('коммерческая') || category.includes('офис')) {
      return <BusinessIcon color="secondary" />;
    }
    return <DescriptionIcon color="action" />;
  };

  const getComplianceColor = (status) => {
    switch (status) {
      case 'compliant': return 'success';
      case 'needs_review': return 'warning';
      case 'high_risk': return 'error';
      default: return 'default';
    }
  };

  const getComplianceText = (status) => {
    switch (status) {
      case 'compliant': return 'Соответствует';
      case 'needs_review': return 'Требует проверки';
      case 'high_risk': return 'Высокий риск';
      default: return 'Неизвестно';
    }
  };

  const exportResults = () => {
    const dataToExport = {
      search_query: searchQuery,
      search_type: searchType,
      properties: properties,
      analysis_results: analysisResults,
      timestamp: new Date().toISOString()
    };
    
    const blob = new Blob([JSON.stringify(dataToExport, null, 2)], {
      type: 'application/json'
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `property_analysis_${new Date().getTime()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <Box>
      {/* Search Controls */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Анализ объектов недвижимости
          </Typography>
          
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label={
                  searchType === 'address' ? 'Адрес объекта' :
                  searchType === 'cadastral' ? 'Кадастровый номер' :
                  'Поиск по координатам'
                }
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                disabled={loading || searchType === 'coordinates'}
                placeholder={
                  searchType === 'address' ? 'Введите адрес...' :
                  searchType === 'cadastral' ? '77:01:0001001:1234' :
                  coordinates ? `${coordinates.lat.toFixed(6)}, ${coordinates.lon.toFixed(6)}` : 'Координаты не заданы'
                }
              />
            </Grid>
            
            <Grid item xs={12} md={4}>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  variant={searchType === 'address' ? 'contained' : 'outlined'}
                  size="small"
                  onClick={() => setSearchType('address')}
                >
                  Адрес
                </Button>
                <Button
                  variant={searchType === 'cadastral' ? 'contained' : 'outlined'}
                  size="small"
                  onClick={() => setSearchType('cadastral')}
                >
                  Кадастр
                </Button>
                <Button
                  variant={searchType === 'coordinates' ? 'contained' : 'outlined'}
                  size="small"
                  onClick={() => setSearchType('coordinates')}
                  disabled={!coordinates}
                >
                  Координаты
                </Button>
              </Box>
            </Grid>
            
            <Grid item xs={12} md={2}>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  variant="contained"
                  startIcon={<SearchIcon />}
                  onClick={handleSearch}
                  disabled={loading || (searchType !== 'coordinates' && !searchQuery.trim())}
                  fullWidth
                >
                  Поиск
                </Button>
                {coordinates && (
                  <Tooltip title="Анализ местоположения">
                    <IconButton
                      onClick={() => analyzeLocation(coordinates.lat, coordinates.lon)}
                      disabled={loading}
                    >
                      <AssessmentIcon />
                    </IconButton>
                  </Tooltip>
                )}
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Loading */}
      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 3 }}>
          <CircularProgress />
        </Box>
      )}

      {/* Analysis Results Summary */}
      {analysisResults && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                Результаты анализа местоположения
              </Typography>
              <Button
                startIcon={<ExportIcon />}
                onClick={exportResults}
                size="small"
              >
                Экспорт
              </Button>
            </Box>
            
            <Grid container spacing={2}>
              <Grid item xs={6} md={3}>
                <Typography variant="body2" color="textSecondary">
                  Всего объектов
                </Typography>
                <Typography variant="h4">
                  {analysisResults.summary.total_properties}
                </Typography>
              </Grid>
              <Grid item xs={6} md={3}>
                <Typography variant="body2" color="textSecondary">
                  Соответствуют
                </Typography>
                <Typography variant="h4" color="success.main">
                  {analysisResults.summary.compliant}
                </Typography>
              </Grid>
              <Grid item xs={6} md={3}>
                <Typography variant="body2" color="textSecondary">
                  Требуют проверки
                </Typography>
                <Typography variant="h4" color="warning.main">
                  {analysisResults.summary.needs_review}
                </Typography>
              </Grid>
              <Grid item xs={6} md={3}>
                <Typography variant="body2" color="textSecondary">
                  Высокий риск
                </Typography>
                <Typography variant="h4" color="error.main">
                  {analysisResults.summary.high_risk}
                </Typography>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Properties List */}
      {properties.length > 0 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Найденные объекты недвижимости ({properties.length})
            </Typography>
            
            <List>
              {properties.map((property, index) => (
                <React.Fragment key={property.cadastral_number || index}>
                  <ListItem
                    button
                    onClick={() => handlePropertyClick(property)}
                    sx={{ borderRadius: 1, mb: 1, bgcolor: 'background.paper' }}
                  >
                    <ListItemIcon>
                      {getPropertyIcon(property.category)}
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="subtitle1">
                            {property.address || 'Адрес не указан'}
                          </Typography>
                          {analysisResults && analysisResults.analysis.find(a => 
                            a.property.cadastral_number === property.cadastral_number
                          ) && (
                            <Chip
                              size="small"
                              label={getComplianceText(
                                analysisResults.analysis.find(a => 
                                  a.property.cadastral_number === property.cadastral_number
                                ).compliance_status
                              )}
                              color={getComplianceColor(
                                analysisResults.analysis.find(a => 
                                  a.property.cadastral_number === property.cadastral_number
                                ).compliance_status
                              )}
                            />
                          )}
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="body2" color="textSecondary">
                            Кадастровый номер: {property.cadastral_number}
                          </Typography>
                          <Typography variant="body2" color="textSecondary">
                            Категория: {property.category} • Площадь: {property.area} м²
                          </Typography>
                          <Typography variant="body2" color="textSecondary">
                            Разрешенное использование: {property.permitted_use}
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItem>
                  {index < properties.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          </CardContent>
        </Card>
      )}

      {/* Property Detail Dialog */}
      <Dialog
        open={showPropertyDialog}
        onClose={() => setShowPropertyDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {selectedProperty && getPropertyIcon(selectedProperty.category)}
            Информация об объекте недвижимости
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedProperty && (
            <Box>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom>
                    Основная информация
                  </Typography>
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableBody>
                        <TableRow>
                          <TableCell><strong>Кадастровый номер</strong></TableCell>
                          <TableCell>{selectedProperty.cadastral_number}</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell><strong>Адрес</strong></TableCell>
                          <TableCell>{selectedProperty.address}</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell><strong>Категория</strong></TableCell>
                          <TableCell>{selectedProperty.category}</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell><strong>Площадь</strong></TableCell>
                          <TableCell>{selectedProperty.area} м²</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell><strong>Разрешенное использование</strong></TableCell>
                          <TableCell>{selectedProperty.permitted_use}</TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom>
                    Дополнительные данные
                  </Typography>
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableBody>
                        <TableRow>
                          <TableCell><strong>Форма собственности</strong></TableCell>
                          <TableCell>{selectedProperty.owner_type || 'Не указано'}</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell><strong>Дата регистрации</strong></TableCell>
                          <TableCell>{selectedProperty.registration_date || 'Не указано'}</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell><strong>Кадастровая стоимость</strong></TableCell>
                          <TableCell>
                            {selectedProperty.cost ? 
                              `${selectedProperty.cost.toLocaleString()} руб.` : 
                              'Не указано'
                            }
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell><strong>Координаты</strong></TableCell>
                          <TableCell>
                            {selectedProperty.coordinates ? 
                              `${selectedProperty.coordinates[0].toFixed(6)}, ${selectedProperty.coordinates[1].toFixed(6)}` : 
                              'Не указано'
                            }
                          </TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Grid>
              </Grid>

              {/* Risk Analysis */}
              {analysisResults && analysisResults.analysis.find(a => 
                a.property.cadastral_number === selectedProperty.cadastral_number
              ) && (
                <Box sx={{ mt: 3 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Анализ рисков
                  </Typography>
                  {(() => {
                    const analysis = analysisResults.analysis.find(a => 
                      a.property.cadastral_number === selectedProperty.cadastral_number
                    );
                    return (
                      <Alert 
                        severity={
                          analysis.compliance_status === 'compliant' ? 'success' :
                          analysis.compliance_status === 'needs_review' ? 'warning' : 'error'
                        }
                      >
                        <Typography variant="body2">
                          <strong>Статус соответствия:</strong> {getComplianceText(analysis.compliance_status)}
                        </Typography>
                        {analysis.risk_factors.length > 0 && (
                          <Box sx={{ mt: 1 }}>
                            <Typography variant="body2">
                              <strong>Факторы риска:</strong>
                            </Typography>
                            <ul style={{ margin: '4px 0', paddingLeft: '20px' }}>
                              {analysis.risk_factors.map((factor, idx) => (
                                <li key={idx}>
                                  <Typography variant="body2">
                                    {factor === 'missing_construction_date' && 'Отсутствует дата постройки'}
                                    {factor === 'large_area' && 'Необычно большая площадь'}
                                    {factor === 'potential_usage_violation' && 'Возможное нарушение использования'}
                                  </Typography>
                                </li>
                              ))}
                            </ul>
                          </Box>
                        )}
                      </Alert>
                    );
                  })()}
                </Box>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowPropertyDialog(false)}>
            Закрыть
          </Button>
          {selectedProperty && (
            <Button
              variant="contained"
              onClick={() => validatePropertyUsage(
                selectedProperty.cadastral_number,
                'current_usage_example'
              )}
              disabled={loading}
            >
              Проверить использование
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default PropertyAnalyzer;
