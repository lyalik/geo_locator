import React, { useState, useEffect } from 'react';
import {
  Box, Card, CardContent, Typography, TextField, Button, Grid,
  List, ListItem, ListItemText, ListItemIcon, Chip, Alert,
  Dialog, DialogTitle, DialogContent, DialogActions, Divider,
  CircularProgress, Accordion, AccordionSummary, AccordionDetails,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, IconButton, Tooltip, Tabs, Tab
} from '@mui/material';
import {
  Search as SearchIcon, LocationOn as LocationIcon, Business as BusinessIcon,
  Home as HomeIcon, School as SchoolIcon, LocalHospital as HospitalIcon,
  Restaurant as RestaurantIcon, Assessment as AssessmentIcon,
  ExpandMore as ExpandMoreIcon, Map as MapIcon, Compare as CompareIcon,
  GetApp as ExportIcon, Refresh as RefreshIcon, Info as InfoIcon
} from '@mui/icons-material';
import { api } from '../services/api';

const UrbanAnalyzer = ({ coordinates, onLocationSelect }) => {
  const [activeTab, setActiveTab] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [geocodeResults, setGeocodeResults] = useState([]);
  const [buildings, setBuildings] = useState([]);
  const [urbanAnalysis, setUrbanAnalysis] = useState(null);
  const [comparisonLocations, setComparisonLocations] = useState([]);
  const [comparisonResults, setComparisonResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedBuilding, setSelectedBuilding] = useState(null);
  const [showBuildingDialog, setShowBuildingDialog] = useState(false);

  // Auto-analyze when coordinates are provided
  useEffect(() => {
    if (coordinates && coordinates.lat && coordinates.lon) {
      analyzeUrbanContext(coordinates.lat, coordinates.lon);
    }
  }, [coordinates]);

  const geocodeAddress = async () => {
    if (!searchQuery.trim()) return;
    
    setLoading(true);
    setError(null);
    
    try {
      // Используем российские геолокационные сервисы
      const response = await api.get('/api/geo/locate', {
        params: { address: searchQuery }
      });
      
      console.log('Geocoding response:', response.data);
      
      // Обрабатываем ответ от разных источников (Yandex и 2GIS)
      let allResults = [];
      
      if (response.data.yandex && response.data.yandex.results) {
        const yandexResults = response.data.yandex.results.map(result => ({
          display_name: result.formatted_address,
          lat: result.latitude,
          lon: result.longitude,
          type: result.type,
          class: 'yandex',
          feature_type: result.type,
          confidence: result.confidence
        }));
        allResults = [...allResults, ...yandexResults];
      }
      
      if (response.data.dgis && response.data.dgis.results) {
        const dgisResults = response.data.dgis.results.map(result => ({
          display_name: result.formatted_address,
          lat: result.latitude,
          lon: result.longitude,
          type: result.type,
          class: '2gis',
          feature_type: result.type,
          confidence: result.confidence
        }));
        allResults = [...allResults, ...dgisResults];
      }
      
      if (allResults.length > 0) {
        setGeocodeResults(allResults);
      } else {
        setError('Не удалось найти адрес');
      }
    } catch (err) {
      setError('Ошибка при геокодировании адреса');
      console.error('Geocoding error:', err);
    } finally {
      setLoading(false);
    }
  };

  const reverseGeocode = async (lat, lon) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.get('/api/geo/locate', {
        params: { lat, lon }
      });
      
      if (response.data.success && response.data.results.length > 0) {
        return {
          display_name: response.data.results[0].formatted_address,
          type: response.data.results[0].type
        };
      }
      return null;
    } catch (err) {
      console.error('Reverse geocoding error:', err);
      return null;
    } finally {
      setLoading(false);
    }
  };

  const getBuildingsInArea = async (lat, lon, radius = 100) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.get('/api/geo/nearby', {
        params: { 
          lat, 
          lon, 
          radius,
          category: 'здания'
        }
      });
      
      if (response.data.success && response.data.places) {
        const buildings = response.data.places.map(place => ({
          osm_id: place.id,
          name: place.name,
          building_type: place.category || 'building',
          address: place.address,
          coordinates: [place.coordinates.lat, place.coordinates.lon],
          amenity: place.amenity,
          levels: place.levels,
          height: place.height
        }));
        setBuildings(buildings);
      } else {
        setError('Не удалось получить данные о зданиях');
      }
    } catch (err) {
      setError('Ошибка при получении данных о зданиях');
      console.error('Buildings error:', err);
    } finally {
      setLoading(false);
    }
  };

  const analyzeUrbanContext = async (lat, lon) => {
    setLoading(true);
    setError(null);
    
    try {
      // Получаем данные о зданиях и инфраструктуре включая OSM
      const [buildingsResponse, nearbyResponse, satelliteResponse, osmUrbanResponse] = await Promise.all([
        api.get('/api/geo/search/places', {
          params: { 
            query: 'здания', 
            lat: lat, 
            lon: lon,
            radius: 1000
          }
        }).catch(() => ({ data: { success: false } })),
        
        api.get('/api/geo/nearby', {
          params: {
            lat: lat,
            lon: lon,
            radius: 1000,
            category: 'all'
          }
        }).catch(() => ({ data: { success: false } })),
        
        api.get('/api/satellite/analyze', {
          params: {
            bbox: `${lon-0.01},${lat-0.01},${lon+0.01},${lat+0.01}`,
            analysis_type: 'urban_analysis'
          }
        }).catch(() => ({ data: { success: false } })),
        
        api.get('/api/osm/urban-context', {
          params: {
            lat: lat,
            lon: lon,
            radius: 1000
          }
        }).catch(() => ({ data: { success: false } }))
      ]);

      const buildings = nearbyResponse.data.places?.filter(place => 
        place.category?.includes('здание') || place.category?.includes('building')
      ).map(place => ({
        osm_id: place.id,
        name: place.name,
        building_type: place.category || 'building',
        address: place.address,
        coordinates: [place.coordinates.lat, place.coordinates.lon],
        amenity: place.amenity,
        levels: place.levels,
        height: place.height
      })) || [];
      
      const amenities = nearbyResponse.data.places?.filter(place => 
        !place.category?.includes('здание') && !place.category?.includes('building')
      ) || [];
      
      const amenityCategories = amenities.reduce((acc, amenity) => {
        const category = amenity.category || 'other';
        acc[category] = (acc[category] || 0) + 1;
        return acc;
      }, {});
      
      // Обработка OSM данных
      let osmBuildings = [];
      let osmAmenities = [];
      
      if (osmUrbanResponse.data.success && osmUrbanResponse.data.context) {
        const osmData = osmUrbanResponse.data.context;
        osmBuildings = osmData.buildings || [];
        osmAmenities = osmData.amenities || [];
        
        console.log(`OSM Urban Context: ${osmBuildings.length} buildings, ${osmAmenities.length} amenities`);
      }
      
      // Объединяем данные из всех источников
      const allBuildings = [...buildings, ...osmBuildings];
      const allAmenities = [...amenities, ...osmAmenities];
      
      const combinedAmenityCategories = allAmenities.reduce((acc, amenity) => {
        const category = amenity.category || amenity.amenity || 'other';
        acc[category] = (acc[category] || 0) + 1;
        return acc;
      }, {});

      const analysis = {
        address_info: null, // Will be filled by reverse geocoding if needed
        area_type: satelliteResponse.data.analysis?.area_classification || 'mixed_use',
        building_count: allBuildings.length,
        building_density: Math.round(allBuildings.length / 0.25), // buildings per km² (500m radius ≈ 0.25 km²)
        amenity_count: allAmenities.length,
        amenity_categories: combinedAmenityCategories,
        buildings: allBuildings,
        satellite_analysis: satelliteResponse.data.analysis || {},
        osm_analysis: osmUrbanResponse.data.context || {},
        infrastructure_score: calculateInfrastructureScore(combinedAmenityCategories),
        development_level: determineDevelopmentLevel(allBuildings.length, allAmenities.length),
        data_sources: {
          geo_api: nearbyResponse.data.success,
          satellite: satelliteResponse.data.success,
          osm: osmUrbanResponse.data.success
        },
        analysis_timestamp: new Date().toISOString()
      };

      console.log('Urban context analysis completed:', analysis);
      
      setUrbanAnalysis(analysis);
      setBuildings(buildings);
    } catch (err) {
      setError('Ошибка при анализе городского контекста');
      console.error('Urban analysis error:', err);
    } finally {
      setLoading(false);
    }
  };

  const calculateInfrastructureScore = (amenityCategories) => {
    const weights = {
      'транспорт': 3,
      'образование': 2,
      'медицина': 2,
      'торговля': 1,
      'услуги': 1,
      'развлечения': 1
    };
    
    let score = 0;
    Object.entries(amenityCategories).forEach(([category, count]) => {
      const weight = weights[category.toLowerCase()] || 0.5;
      score += count * weight;
    });
    
    return Math.round(score);
  };

  const determineDevelopmentLevel = (buildingCount, amenityCount) => {
    const total = buildingCount + amenityCount;
    if (total > 50) return 'Высокий';
    if (total > 20) return 'Средний';
    return 'Низкий';
  };

  const searchPlaces = async (query, lat = null, lon = null) => {
    setLoading(true);
    setError(null);
    
    try {
      const params = { query };
      if (lat && lon) {
        params.lat = lat;
        params.lon = lon;
        params.radius = 5000;
      }
      
      const response = await api.get('/api/geo/search/places', { params });
      
      if (response.data.success && response.data.places) {
        const results = response.data.places.map(place => ({
          display_name: place.address || place.name,
          lat: place.coordinates.lat,
          lon: place.coordinates.lon,
          type: place.category,
          class: place.source,
          feature_type: place.category
        }));
        setGeocodeResults(results);
      } else {
        setError('Не удалось найти места');
      }
    } catch (err) {
      setError('Ошибка при поиске мест');
      console.error('Search error:', err);
    } finally {
      setLoading(false);
    }
  };

  const addLocationForComparison = (lat, lon, name) => {
    if (comparisonLocations.length >= 5) {
      setError('Максимум 5 локаций для сравнения');
      return;
    }
    
    const newLocation = { lat, lon, name };
    setComparisonLocations([...comparisonLocations, newLocation]);
  };

  const compareLocations = async () => {
    if (comparisonLocations.length < 2) {
      setError('Необходимо минимум 2 локации для сравнения');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      // Анализируем каждую локацию через российские сервисы
      const analysisPromises = comparisonLocations.map(async (location) => {
        const [geoResponse, nearbyResponse] = await Promise.all([
          api.get('/api/geo/locate', { params: { lat: location.lat, lon: location.lon } }),
          api.get('/api/geo/nearby', { params: { lat: location.lat, lon: location.lon, radius: 500 } })
        ]);
        
        const buildings = nearbyResponse.data.places?.filter(place => 
          place.category?.includes('здание') || place.category?.includes('building')
        ) || [];
        
        return {
          location: location,
          building_count: buildings.length,
          building_density: buildings.length / 0.25,
          amenity_count: nearbyResponse.data.places?.length - buildings.length || 0
        };
      });
      
      const analyses = await Promise.all(analysisPromises);
      
      // Находим наиболее и наименее урбанизированные локации
      const sortedByDensity = analyses.sort((a, b) => b.building_density - a.building_density);
      
      const comparison = {
        locations: analyses,
        comparison_summary: {
          most_urban: sortedByDensity[0].location.name,
          least_urban: sortedByDensity[sortedByDensity.length - 1].location.name,
          building_density_range: {
            min: sortedByDensity[sortedByDensity.length - 1].building_density,
            max: sortedByDensity[0].building_density
          }
        }
      };
      
      setComparisonResults(comparison);
    } catch (err) {
      setError('Ошибка при сравнении локаций');
      console.error('Comparison error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleLocationClick = (result) => {
    const lat = result.lat || result.coordinates?.[0];
    const lon = result.lon || result.coordinates?.[1];
    
    if (lat && lon) {
      analyzeUrbanContext(lat, lon);
      if (onLocationSelect) {
        onLocationSelect({ lat, lon, name: result.display_name || result.name });
      }
    }
  };

  const handleBuildingClick = (building) => {
    setSelectedBuilding(building);
    setShowBuildingDialog(true);
  };

  const getBuildingIcon = (buildingType) => {
    if (buildingType.includes('residential') || buildingType === 'house') {
      return <HomeIcon color="primary" />;
    } else if (buildingType.includes('commercial') || buildingType === 'retail') {
      return <BusinessIcon color="secondary" />;
    } else if (buildingType === 'school') {
      return <SchoolIcon color="info" />;
    } else if (buildingType === 'hospital') {
      return <HospitalIcon color="error" />;
    }
    return <LocationIcon color="action" />;
  };

  const getAreaTypeColor = (areaType) => {
    switch (areaType) {
      case 'residential': return 'primary';
      case 'commercial': return 'secondary';
      case 'industrial': return 'warning';
      case 'institutional': return 'info';
      case 'mixed_use': return 'success';
      default: return 'default';
    }
  };

  const exportAnalysis = () => {
    const dataToExport = {
      coordinates: coordinates,
      urban_analysis: urbanAnalysis,
      buildings: buildings,
      comparison_results: comparisonResults,
      timestamp: new Date().toISOString()
    };
    
    const blob = new Blob([JSON.stringify(dataToExport, null, 2)], {
      type: 'application/json'
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `urban_analysis_${new Date().getTime()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const TabPanel = ({ children, value, index }) => (
    <div hidden={value !== index}>
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );

  return (
    <Box>
      {/* Header */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">
              Анализ городского контекста (OpenStreetMap)
            </Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                startIcon={<ExportIcon />}
                onClick={exportAnalysis}
                disabled={!urbanAnalysis}
                size="small"
              >
                Экспорт
              </Button>
              <Button
                startIcon={<RefreshIcon />}
                onClick={() => coordinates && analyzeUrbanContext(coordinates.lat, coordinates.lon)}
                disabled={loading || !coordinates}
                size="small"
              >
                Обновить
              </Button>
            </Box>
          </Box>
          
          {/* Search */}
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={8}>
              <TextField
                fullWidth
                label="Поиск адреса или места"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && geocodeAddress()}
                disabled={loading}
                placeholder="Введите адрес или название места..."
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  variant="contained"
                  startIcon={<SearchIcon />}
                  onClick={geocodeAddress}
                  disabled={loading || !searchQuery.trim()}
                  fullWidth
                >
                  Найти
                </Button>
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

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={activeTab}
          onChange={(e, newValue) => setActiveTab(newValue)}
          variant="fullWidth"
        >
          <Tab icon={<SearchIcon />} label="Поиск" />
          <Tab icon={<AssessmentIcon />} label="Анализ" />
          <Tab icon={<HomeIcon />} label="Здания" />
          <Tab icon={<CompareIcon />} label="Сравнение" />
        </Tabs>
      </Paper>

      {/* Search Results Tab */}
      <TabPanel value={activeTab} index={0}>
        {geocodeResults.length > 0 && (
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Результаты поиска ({geocodeResults.length})
              </Typography>
              <List>
                {geocodeResults.map((result, index) => (
                  <React.Fragment key={index}>
                    <ListItem
                      button
                      onClick={() => handleLocationClick(result)}
                      sx={{ borderRadius: 1, mb: 1, bgcolor: 'background.paper' }}
                    >
                      <ListItemIcon>
                        <LocationIcon />
                      </ListItemIcon>
                      <ListItemText
                        primary={result.display_name || result.name}
                        secondary={
                          <Box>
                            <Typography variant="body2" color="textSecondary">
                              Координаты: {result.lat?.toFixed(6)}, {result.lon?.toFixed(6)}
                            </Typography>
                            <Typography variant="body2" color="textSecondary">
                              Тип: {result.type || result.feature_type} • Класс: {result.class}
                            </Typography>
                          </Box>
                        }
                      />
                      <Button
                        size="small"
                        onClick={(e) => {
                          e.stopPropagation();
                          addLocationForComparison(
                            result.lat || result.coordinates?.[0],
                            result.lon || result.coordinates?.[1],
                            result.display_name || result.name
                          );
                        }}
                      >
                        + Сравнить
                      </Button>
                    </ListItem>
                    {index < geocodeResults.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            </CardContent>
          </Card>
        )}
      </TabPanel>

      {/* Urban Analysis Tab */}
      <TabPanel value={activeTab} index={1}>
        {urbanAnalysis && (
          <Grid container spacing={3}>
            {/* Summary Cards */}
            <Grid item xs={12}>
              <Grid container spacing={2}>
                <Grid item xs={6} md={3}>
                  <Card>
                    <CardContent>
                      <Typography color="textSecondary" gutterBottom>
                        Тип района
                      </Typography>
                      <Chip
                        label={urbanAnalysis.area_type}
                        color={getAreaTypeColor(urbanAnalysis.area_type)}
                        size="large"
                      />
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Card>
                    <CardContent>
                      <Typography color="textSecondary" gutterBottom>
                        Зданий
                      </Typography>
                      <Typography variant="h4">
                        {urbanAnalysis.building_count}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Card>
                    <CardContent>
                      <Typography color="textSecondary" gutterBottom>
                        Плотность застройки
                      </Typography>
                      <Typography variant="h4">
                        {urbanAnalysis.building_density?.toFixed(1)}
                      </Typography>
                      <Typography variant="caption" color="textSecondary">
                        зданий/км²
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={6} md={3}>
                  <Card>
                    <CardContent>
                      <Typography color="textSecondary" gutterBottom>
                        Объектов инфраструктуры
                      </Typography>
                      <Typography variant="h4">
                        {urbanAnalysis.amenity_count}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </Grid>

            {/* Address Info */}
            {urbanAnalysis.address_info && (
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Информация об адресе
                    </Typography>
                    <Typography variant="body1">
                      {urbanAnalysis.address_info.display_name}
                    </Typography>
                    <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                      Тип: {urbanAnalysis.address_info.type}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            )}

            {/* Amenity Categories */}
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Категории инфраструктуры
                  </Typography>
                  {Object.entries(urbanAnalysis.amenity_categories || {}).map(([category, count]) => (
                    <Box key={category} sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2">
                        {category}
                      </Typography>
                      <Chip label={count} size="small" />
                    </Box>
                  ))}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}
      </TabPanel>

      {/* Buildings Tab */}
      <TabPanel value={activeTab} index={2}>
        {buildings.length > 0 && (
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Здания в области ({buildings.length})
              </Typography>
              <List>
                {buildings.slice(0, 20).map((building, index) => (
                  <React.Fragment key={building.osm_id || index}>
                    <ListItem
                      button
                      onClick={() => handleBuildingClick(building)}
                      sx={{ borderRadius: 1, mb: 1, bgcolor: 'background.paper' }}
                    >
                      <ListItemIcon>
                        {getBuildingIcon(building.building_type)}
                      </ListItemIcon>
                      <ListItemText
                        primary={building.name || `${building.building_type} здание`}
                        secondary={
                          <Box>
                            <Typography variant="body2" color="textSecondary">
                              Адрес: {building.address || 'Не указан'}
                            </Typography>
                            <Typography variant="body2" color="textSecondary">
                              Тип: {building.building_type}
                              {building.levels && ` • Этажей: ${building.levels}`}
                              {building.amenity && ` • Назначение: ${building.amenity}`}
                            </Typography>
                          </Box>
                        }
                      />
                    </ListItem>
                    {index < Math.min(buildings.length, 20) - 1 && <Divider />}
                  </React.Fragment>
                ))}
                {buildings.length > 20 && (
                  <Typography variant="body2" color="textSecondary" sx={{ mt: 2, textAlign: 'center' }}>
                    Показано 20 из {buildings.length} зданий
                  </Typography>
                )}
              </List>
            </CardContent>
          </Card>
        )}
      </TabPanel>

      {/* Comparison Tab */}
      <TabPanel value={activeTab} index={3}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Локации для сравнения ({comparisonLocations.length}/5)
                </Typography>
                <List>
                  {comparisonLocations.map((location, index) => (
                    <ListItem key={index}>
                      <ListItemIcon>
                        <LocationIcon />
                      </ListItemIcon>
                      <ListItemText
                        primary={location.name}
                        secondary={`${location.lat.toFixed(6)}, ${location.lon.toFixed(6)}`}
                      />
                      <IconButton
                        onClick={() => {
                          const newLocations = comparisonLocations.filter((_, i) => i !== index);
                          setComparisonLocations(newLocations);
                        }}
                      >
                        ×
                      </IconButton>
                    </ListItem>
                  ))}
                </List>
                <Button
                  variant="contained"
                  startIcon={<CompareIcon />}
                  onClick={compareLocations}
                  disabled={comparisonLocations.length < 2 || loading}
                  fullWidth
                  sx={{ mt: 2 }}
                >
                  Сравнить локации
                </Button>
              </CardContent>
            </Card>
          </Grid>

          {comparisonResults && (
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Результаты сравнения
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="textSecondary">
                        Самый урбанизированный
                      </Typography>
                      <Typography variant="body1">
                        {comparisonResults.comparison_summary.most_urban}
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="textSecondary">
                        Наименее урбанизированный
                      </Typography>
                      <Typography variant="body1">
                        {comparisonResults.comparison_summary.least_urban}
                      </Typography>
                    </Grid>
                    <Grid item xs={12}>
                      <Typography variant="body2" color="textSecondary">
                        Диапазон плотности застройки
                      </Typography>
                      <Typography variant="body1">
                        {comparisonResults.comparison_summary.building_density_range.min.toFixed(1)} - {comparisonResults.comparison_summary.building_density_range.max.toFixed(1)} зданий/км²
                      </Typography>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          )}
        </Grid>
      </TabPanel>

      {/* Building Detail Dialog */}
      <Dialog
        open={showBuildingDialog}
        onClose={() => setShowBuildingDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {selectedBuilding && getBuildingIcon(selectedBuilding.building_type)}
            Информация о здании
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedBuilding && (
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableBody>
                  <TableRow>
                    <TableCell><strong>Название</strong></TableCell>
                    <TableCell>{selectedBuilding.name || 'Не указано'}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><strong>Тип здания</strong></TableCell>
                    <TableCell>{selectedBuilding.building_type}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><strong>Адрес</strong></TableCell>
                    <TableCell>{selectedBuilding.address || 'Не указан'}</TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell><strong>Координаты</strong></TableCell>
                    <TableCell>
                      {selectedBuilding.coordinates?.[0]?.toFixed(6)}, {selectedBuilding.coordinates?.[1]?.toFixed(6)}
                    </TableCell>
                  </TableRow>
                  {selectedBuilding.levels && (
                    <TableRow>
                      <TableCell><strong>Этажей</strong></TableCell>
                      <TableCell>{selectedBuilding.levels}</TableCell>
                    </TableRow>
                  )}
                  {selectedBuilding.height && (
                    <TableRow>
                      <TableCell><strong>Высота</strong></TableCell>
                      <TableCell>{selectedBuilding.height} м</TableCell>
                    </TableRow>
                  )}
                  {selectedBuilding.amenity && (
                    <TableRow>
                      <TableCell><strong>Назначение</strong></TableCell>
                      <TableCell>{selectedBuilding.amenity}</TableCell>
                    </TableRow>
                  )}
                  <TableRow>
                    <TableCell><strong>OSM ID</strong></TableCell>
                    <TableCell>{selectedBuilding.osm_id}</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowBuildingDialog(false)}>
            Закрыть
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default UrbanAnalyzer;
