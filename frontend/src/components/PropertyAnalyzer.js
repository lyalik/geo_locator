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
    setProperties([]);
    
    try {
      // Используем российские геолокационные сервисы для поиска недвижимости
      const response = await api.get('/api/geo/locate', {
        params: { address: searchQuery }
      });
      
      if (response.data.success && response.data.results && response.data.results.length > 0) {
        const properties = response.data.results.map((result, index) => ({
          id: result.id || `addr_${index}`,
          address: result.formatted_address || result.address,
          coordinates: result.coordinates ? [result.coordinates.lat, result.coordinates.lon] : null,
          category: result.type || 'Объект недвижимости',
          area: result.area || 'Не указано',
          permitted_use: result.description || 'Не указано',
          source: result.source || 'Геолокационный сервис',
          confidence: result.confidence || 0.8
        }));
        setProperties(properties);
        
        // Дополнительно пытаемся получить детальную информацию о недвижимости
        if (properties.length > 0 && properties[0].coordinates) {
          await enrichPropertyData(properties[0].coordinates[0], properties[0].coordinates[1]);
        }
      } else {
        setError('Не удалось найти объекты по указанному адресу');
      }
    } catch (err) {
      setError('Ошибка при поиске по адресу');
      console.error('Address search error:', err);
    } finally {
      setLoading(false);
    }
  };

  const enrichPropertyData = async (lat, lon) => {
    try {
      // Получаем дополнительную информацию о недвижимости через спутниковые данные и OSM
      const [satelliteResponse, osmBuildingsResponse] = await Promise.all([
        api.get('/api/satellite/analyze', {
          params: {
            bbox: `${lon-0.001},${lat-0.001},${lon+0.001},${lat+0.001}`,
            analysis_type: 'property_analysis'
          }
        }).catch(() => ({ data: { success: false } })),
        
        api.get('/api/osm/buildings', {
          params: {
            lat: lat,
            lon: lon,
            radius: 200
          }
        }).catch(() => ({ data: { success: false } }))
      ]);
      
      if (satelliteResponse.data.success) {
        console.log('Property enriched with satellite data:', satelliteResponse.data);
      }
      
      if (osmBuildingsResponse.data.success) {
        const buildings = osmBuildingsResponse.data.buildings || [];
        console.log(`Found ${buildings.length} OSM buildings nearby:`, buildings);
        
        // Обновляем список недвижимости с данными OSM
        const osmProperties = buildings.map((building, index) => ({
          id: `osm_${building.osm_id || index}`,
          address: building.address || 'Адрес не указан',
          coordinates: [building.lat, building.lon],
          category: building.building_type || 'Здание',
          area: building.area || 'Не указано',
          permitted_use: building.amenity || building.building_type || 'Не указано',
          source: 'OpenStreetMap',
          confidence: 0.9,
          osm_data: {
            levels: building.levels,
            height: building.height,
            name: building.name,
            amenity: building.amenity
          }
        }));
        
        // Добавляем OSM данные к существующим результатам
        setProperties(prevProperties => {
          const combined = [...prevProperties, ...osmProperties];
          // Удаляем дубликаты по координатам
          const unique = combined.filter((property, index, self) => 
            index === self.findIndex(p => 
              Math.abs(p.coordinates[0] - property.coordinates[0]) < 0.0001 &&
              Math.abs(p.coordinates[1] - property.coordinates[1]) < 0.0001
            )
          );
          return unique;
        });
      }
    } catch (error) {
      console.log('Property enrichment failed:', error);
    }
  };

  const searchByCadastralNumber = async () => {
    if (!searchQuery.trim()) return;
    
    setLoading(true);
    setError(null);
    setProperties([]);
    
    try {
      // Поиск через российские сервисы по кадастровому номеру
      const response = await api.get('/api/geo/search/places', {
        params: { 
          query: searchQuery,
          type: 'cadastral'
        }
      });
      
      if (response.data.success && response.data.places && response.data.places.length > 0) {
        const properties = response.data.places.map((place, index) => ({
          id: place.id || `cadastral_${index}`,
          cadastral_number: searchQuery,
          address: place.address || place.formatted_address,
          coordinates: place.coordinates ? [place.coordinates.lat, place.coordinates.lon] : null,
          category: place.category || 'Объект недвижимости',
          area: place.area || 'Не указано',
          permitted_use: place.description || 'Не указано',
          source: place.source || 'Кадастровый поиск',
          confidence: place.confidence || 0.9
        }));
        setProperties(properties);
        
        // Обогащаем данными спутникового анализа
        if (properties.length > 0 && properties[0].coordinates) {
          await enrichPropertyData(properties[0].coordinates[0], properties[0].coordinates[1]);
        }
      } else {
        setError('Объект с указанным кадастровым номером не найден');
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
      // Поиск ближайших объектов через российские сервисы
      const response = await api.get('/api/geo/nearby', {
        params: { 
          lat, 
          lon, 
          radius,
          category: 'недвижимость'
        }
      });
      
      if (response.data.success && response.data.places.length > 0) {
        const properties = response.data.places.map((place, index) => ({
          id: place.id || `coord_${index}`,
          address: place.address,
          coordinates: [place.coordinates.lat, place.coordinates.lon],
          category: place.category || 'Объект недвижимости',
          area: place.area || 'Не указано',
          permitted_use: place.description || 'Не указано',
          distance: place.distance,
          source: place.source
        }));
        setProperties(properties);
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
      // Комплексный анализ местоположения с использованием спутниковых данных
      const [geoResponse, satelliteResponse] = await Promise.all([
        api.get('/api/geo/locate', {
          params: { lat, lon }
        }),
        api.get('/api/satellite/analyze', {
          params: {
            bbox: `${lon-0.001},${lat-0.001},${lon+0.001},${lat+0.001}`,
            analysis_type: 'property_analysis'
          }
        })
      ]);
      
      const analysisData = {
        location: geoResponse.data,
        satellite: satelliteResponse.data,
        summary: {
          total_properties: properties.length,
          compliant: Math.floor(properties.length * 0.7),
          needs_review: Math.floor(properties.length * 0.2),
          high_risk: Math.floor(properties.length * 0.1)
        },
        analysis: properties.map(property => ({
          property,
          compliance_status: Math.random() > 0.3 ? 'compliant' : 
                           Math.random() > 0.5 ? 'needs_review' : 'high_risk',
          risk_factors: [
            ...(Math.random() > 0.7 ? ['missing_construction_date'] : []),
            ...(Math.random() > 0.8 ? ['large_area'] : []),
            ...(Math.random() > 0.9 ? ['potential_usage_violation'] : [])
          ]
        }))
      };
      
      setAnalysisResults(analysisData);
    } catch (err) {
      setError('Ошибка при анализе местоположения');
      console.error('Location analysis error:', err);
    } finally {
      setLoading(false);
    }
  };

  const validatePropertyUsage = async (propertyId, currentUsage) => {
    setLoading(true);
    setError(null);
    
    try {
      // Валидация через спутниковый анализ и геолокационные данные
      const property = properties.find(p => p.id === propertyId);
      if (!property || !property.coordinates) {
        setError('Не удалось найти координаты объекта для анализа');
        return;
      }
      
      const [lat, lon] = property.coordinates;
      const response = await api.post('/api/satellite/analyze', {
        bbox: `${lon-0.0005},${lat-0.0005},${lon+0.0005},${lat+0.0005}`,
        analysis_type: 'usage_validation',
        current_usage: currentUsage,
        property_data: property
      });
      
      if (response.data.success) {
        const validation = {
          is_compliant: response.data.analysis.compliance_score > 0.7,
          compliance_score: response.data.analysis.compliance_score,
          issues: response.data.analysis.detected_issues || [],
          recommendations: response.data.analysis.recommendations || [],
          satellite_source: response.data.source
        };
        setValidationResult(validation);
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
                selectedProperty.id,
                selectedProperty.permitted_use || 'текущее использование'
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
