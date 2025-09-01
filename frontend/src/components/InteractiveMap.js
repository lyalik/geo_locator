import React, { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, LayersControl } from 'react-leaflet';
import MarkerClusterGroup from 'react-leaflet-cluster';
import L from 'leaflet';
import { Box, Card, CardContent, Typography, Chip, Button, FormControl, InputLabel, Select, MenuItem, TextField, Switch, FormControlLabel } from '@mui/material';
import { LocationOn, Visibility, FilterList, GetApp, Satellite, Map as MapIcon } from '@mui/icons-material';
import { api } from '../services/api';
import 'leaflet/dist/leaflet.css';

// Fix for default markers in react-leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

// Custom violation icons with AI source differentiation
const violationIcons = {
  illegal_construction: L.divIcon({
    html: '<div style="background-color: #f44336; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white;"></div>',
    className: 'custom-div-icon',
    iconSize: [20, 20],
    iconAnchor: [10, 10]
  }),
  unauthorized_signage: L.divIcon({
    html: '<div style="background-color: #ff9800; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white;"></div>',
    className: 'custom-div-icon',
    iconSize: [20, 20],
    iconAnchor: [10, 10]
  }),
  blocked_entrance: L.divIcon({
    html: '<div style="background-color: #9c27b0; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white;"></div>',
    className: 'custom-div-icon',
    iconSize: [20, 20],
    iconAnchor: [10, 10]
  }),
  improper_waste_disposal: L.divIcon({
    html: '<div style="background-color: #795548; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white;"></div>',
    className: 'custom-div-icon',
    iconSize: [20, 20],
    iconAnchor: [10, 10]
  }),
  unauthorized_modification: L.divIcon({
    html: '<div style="background-color: #607d8b; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white;"></div>',
    className: 'custom-div-icon',
    iconSize: [20, 20],
    iconAnchor: [10, 10]
  }),
  // Mistral AI specific icons (with purple border)
  mistral_illegal_construction: L.divIcon({
    html: '<div style="background-color: #f44336; width: 20px; height: 20px; border-radius: 50%; border: 3px solid #9c27b0;"></div>',
    className: 'custom-div-icon',
    iconSize: [20, 20],
    iconAnchor: [10, 10]
  }),
  mistral_unauthorized_signage: L.divIcon({
    html: '<div style="background-color: #ff9800; width: 20px; height: 20px; border-radius: 50%; border: 3px solid #9c27b0;"></div>',
    className: 'custom-div-icon',
    iconSize: [20, 20],
    iconAnchor: [10, 10]
  }),
  mistral_blocked_entrance: L.divIcon({
    html: '<div style="background-color: #9c27b0; width: 20px; height: 20px; border-radius: 50%; border: 3px solid #673ab7;"></div>',
    className: 'custom-div-icon',
    iconSize: [20, 20],
    iconAnchor: [10, 10]
  }),
  mistral_improper_waste_disposal: L.divIcon({
    html: '<div style="background-color: #795548; width: 20px; height: 20px; border-radius: 50%; border: 3px solid #9c27b0;"></div>',
    className: 'custom-div-icon',
    iconSize: [20, 20],
    iconAnchor: [10, 10]
  }),
  mistral_unauthorized_modification: L.divIcon({
    html: '<div style="background-color: #607d8b; width: 20px; height: 20px; border-radius: 50%; border: 3px solid #9c27b0;"></div>',
    className: 'custom-div-icon',
    iconSize: [20, 20],
    iconAnchor: [10, 10]
  }),
  default: L.divIcon({
    html: '<div style="background-color: #2196f3; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white;"></div>',
    className: 'custom-div-icon',
    iconSize: [20, 20],
    iconAnchor: [10, 10]
  })
};

const InteractiveMap = ({ violations = [], onViolationClick, height = 600 }) => {
  const [filteredViolations, setFilteredViolations] = useState(violations);
  const [filters, setFilters] = useState({
    category: 'all',
    dateFrom: '',
    dateTo: '',
    confidenceMin: 0.5
  });
  const [showFilters, setShowFilters] = useState(false);
  const [showSatellite, setShowSatellite] = useState(false);
  const [showSatelliteData, setShowSatelliteData] = useState(false);
  const [showOSMBuildings, setShowOSMBuildings] = useState(false);
  const [satelliteData, setSatelliteData] = useState(null);
  const [osmBuildingsData, setOsmBuildingsData] = useState([]);
  const [osmBuildings, setOsmBuildings] = useState([]);
  const [loadingSatellite, setLoadingSatellite] = useState(false);
  const [loadingOSM, setLoadingOSM] = useState(false);
  const mapRef = useRef();

  // Default center (Moscow)
  const defaultCenter = [55.7558, 37.6176];

  useEffect(() => {
    applyFilters();
  }, [violations, filters]);

  const applyFilters = () => {
    let filtered = [...violations];

    // Filter by category
    if (filters.category !== 'all') {
      filtered = filtered.filter(v => v.category === filters.category);
    }

    // Filter by confidence
    filtered = filtered.filter(v => v.confidence >= filters.confidenceMin);

    // Filter by date range
    if (filters.dateFrom) {
      filtered = filtered.filter(v => new Date(v.created_at) >= new Date(filters.dateFrom));
    }
    if (filters.dateTo) {
      filtered = filtered.filter(v => new Date(v.created_at) <= new Date(filters.dateTo));
    }

    setFilteredViolations(filtered);
  };

  const handleFilterChange = (field, value) => {
    setFilters(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const getViolationIcon = (category, source) => {
    // Для Mistral AI используем специальные иконки с фиолетовой границей
    if (source === 'mistral_ai') {
      const mistralKey = `mistral_${category}`;
      return violationIcons[mistralKey] || violationIcons.default;
    }
    return violationIcons[category] || violationIcons.default;
  };

  const loadOSMBuildings = async () => {
    setLoadingOSM(true);
    try {
      const map = mapRef.current;
      const bounds = map.getBounds();
      
      const params = new URLSearchParams({
        bbox: `${bounds.getWest()},${bounds.getSouth()},${bounds.getEast()},${bounds.getNorth()}`,
        limit: 100
      });
      
      const response = await api.get(`/api/osm/buildings?${params}`);
      
      if (response.data.success) {
        const buildings = response.data.data.map(building => ({
          lat: building.lat || building.latitude,
          lon: building.lon || building.longitude,
          name: building.name || building.tags?.name || 'Здание',
          levels: building.levels || building.tags?.['building:levels'],
          height: building.height || building.tags?.height,
          amenity: building.amenity || building.tags?.amenity
        }));
        setOsmBuildings(buildings);
        setOsmBuildingsData(response.data.data);
      }
    } catch (error) {
      console.error('Error loading OSM buildings:', error);
      // Mock OSM buildings data for demo
      const mockBuildings = [
        { lat: 55.7558, lon: 37.6176, name: 'Красная площадь', levels: 1, amenity: 'historic' },
        { lat: 55.7520, lon: 37.6156, name: 'ГУМ', levels: 3, amenity: 'shop' },
        { lat: 55.7539, lon: 37.6208, name: 'Большой театр', levels: 4, amenity: 'theatre' }
      ];
      setOsmBuildings(mockBuildings);
    } finally {
      setLoadingOSM(false);
    }
  };

  const toggleOSMBuildings = async () => {
    const newShowOSM = !showOSMBuildings;
    setShowOSMBuildings(newShowOSM);
    
    if (newShowOSM && osmBuildings.length === 0) {
      await loadOSMBuildings();
    }
  };

  const getCategoryColor = (category) => {
    const colors = {
      illegal_construction: '#f44336',
      unauthorized_signage: '#ff9800',
      blocked_entrance: '#9c27b0',
      improper_waste_disposal: '#795548',
      unauthorized_modification: '#607d8b'
    };
    return colors[category] || '#2196f3';
  };

  const formatCategory = (category) => {
    return category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const exportData = () => {
    const dataStr = JSON.stringify(filteredViolations, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `violations_export_${new Date().toISOString().split('T')[0]}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  const loadSatelliteData = async (bounds) => {
    if (!bounds) return;
    
    try {
      setLoadingSatellite(true);
      const bbox = `${bounds.getWest()},${bounds.getSouth()},${bounds.getEast()},${bounds.getNorth()}`;
      
      const params = new URLSearchParams({
        bbox,
        date_from: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        date_to: new Date().toISOString().split('T')[0],
        resolution: 10,
        max_cloud_coverage: 20
      });
      
      const response = await api.get(`/api/satellite/image?${params}`);
      
      if (response.data.success) {
        setSatelliteData(response.data.data);
      }
    } catch (error) {
      console.error('Error loading satellite data:', error);
    } finally {
      setLoadingSatellite(false);
    }
  };

  const toggleSatelliteLayer = async () => {
    const newShowSatelliteData = !showSatelliteData;
    setShowSatelliteData(newShowSatelliteData);
    
    if (newShowSatelliteData && mapRef.current && !satelliteData) {
      const map = mapRef.current;
      const bounds = map.getBounds();
      await loadSatelliteData(bounds);
    }
  };

  return (
    <Box sx={{ height: height, display: 'flex', flexDirection: 'column' }}>
      {/* Controls */}
      <Box sx={{ p: 2, borderBottom: '1px solid #e0e0e0' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: showFilters ? 2 : 0 }}>
          <Button
            startIcon={<FilterList />}
            onClick={() => setShowFilters(!showFilters)}
            variant={showFilters ? 'contained' : 'outlined'}
          >
            Фильтры
          </Button>
          <FormControlLabel
            control={
              <Switch
                checked={showSatelliteData}
                onChange={toggleSatelliteLayer}
                color="primary"
              />
            }
            label={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Satellite />
                Спутниковые данные
              </Box>
            }
          />
          <FormControlLabel
            control={
              <Switch
                checked={showOSMBuildings}
                onChange={(e) => {
                  const newShowOSM = e.target.checked;
                  setShowOSMBuildings(newShowOSM);
                  if (newShowOSM && osmBuildings.length === 0) {
                    loadOSMBuildings();
                  }
                }}
                color="primary"
              />
            }
            label={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <MapIcon />
                OSM здания
              </Box>
            }
          />
          <Button
            startIcon={<GetApp />}
            onClick={exportData}
            variant="outlined"
          >
            Экспорт ({filteredViolations.length})
          </Button>
          <Typography variant="body2" color="textSecondary">
            Показано: {filteredViolations.length} из {violations.length} нарушений
          </Typography>
        </Box>

        {showFilters && (
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
            <FormControl size="small" sx={{ minWidth: 150 }}>
              <InputLabel>Категория</InputLabel>
              <Select
                value={filters.category}
                onChange={(e) => handleFilterChange('category', e.target.value)}
                label="Категория"
              >
                <MenuItem value="all">Все</MenuItem>
                <MenuItem value="illegal_construction">Незаконное строительство</MenuItem>
                <MenuItem value="unauthorized_signage">Несанкционированные вывески</MenuItem>
                <MenuItem value="blocked_entrance">Заблокированный вход</MenuItem>
                <MenuItem value="improper_waste_disposal">Неправильная утилизация отходов</MenuItem>
                <MenuItem value="unauthorized_modification">Несанкционированные изменения</MenuItem>
              </Select>
            </FormControl>

            <TextField
              size="small"
              label="Дата от"
              type="date"
              value={filters.dateFrom}
              onChange={(e) => handleFilterChange('dateFrom', e.target.value)}
              InputLabelProps={{ shrink: true }}
            />

            <TextField
              size="small"
              label="Дата до"
              type="date"
              value={filters.dateTo}
              onChange={(e) => handleFilterChange('dateTo', e.target.value)}
              InputLabelProps={{ shrink: true }}
            />

            <TextField
              size="small"
              label="Мин. достоверность"
              type="number"
              inputProps={{ min: 0, max: 1, step: 0.1 }}
              value={filters.confidenceMin}
              onChange={(e) => handleFilterChange('confidenceMin', parseFloat(e.target.value))}
            />
          </Box>
        )}
      </Box>

      {/* Map */}
      <Box sx={{ flex: 1, position: 'relative', minHeight: '500px' }}>
        <MapContainer
          center={defaultCenter}
          zoom={10}
          style={{ height: '500px', width: '100%' }}
          ref={mapRef}
        >
          <LayersControl position="topright">
            <LayersControl.BaseLayer checked name="OpenStreetMap">
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
            </LayersControl.BaseLayer>
            
            <LayersControl.BaseLayer name="Яндекс Карты">
              <TileLayer
                attribution='&copy; <a href="https://yandex.ru/maps/">Яндекс</a>'
                url="https://core-renderer-tiles.maps.yandex.net/tiles?l=map&v=21.06.03-0&x={x}&y={y}&z={z}&scale=1&lang=ru_RU"
              />
            </LayersControl.BaseLayer>

            <LayersControl.BaseLayer name="2GIS">
              <TileLayer
                attribution='&copy; <a href="https://2gis.ru/">2GIS</a>'
                url="https://tile2.maps.2gis.com/tiles?x={x}&y={y}&z={z}&v=1.1"
              />
            </LayersControl.BaseLayer>
            
            <LayersControl.BaseLayer name="Спутниковая (Esri)">
              <TileLayer
                attribution='&copy; <a href="https://www.esri.com/">Esri</a>'
                url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
              />
            </LayersControl.BaseLayer>

            <LayersControl.BaseLayer name="Топографическая">
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png"
              />
            </LayersControl.BaseLayer>

            {/* Спутниковые данные слой */}
            {showSatelliteData && (
              <LayersControl.Overlay checked name="Спутниковые данные">
                <TileLayer
                  attribution='Роскосмос &copy; Спутниковые данные'
                  url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                  opacity={0.7}
                />
              </LayersControl.Overlay>
            )}

            {/* OSM здания слой */}
            {showOSMBuildings && (
              <LayersControl.Overlay checked name="OSM здания">
                {osmBuildings.map((building, index) => (
                  <Marker
                    key={`building-${index}`}
                    position={[building.lat, building.lon]}
                    icon={L.divIcon({
                      html: '<div style="background-color: #4caf50; width: 8px; height: 8px; border-radius: 2px; border: 1px solid white;"></div>',
                      className: 'osm-building-icon',
                      iconSize: [8, 8],
                      iconAnchor: [4, 4]
                    })}
                  >
                    <Popup>
                      <Typography variant="body2">
                        <strong>Здание OSM</strong><br/>
                        {building.name && `Название: ${building.name}`}<br/>
                        {building.levels && `Этажей: ${building.levels}`}<br/>
                        {building.height && `Высота: ${building.height}м`}<br/>
                        {building.amenity && `Тип: ${building.amenity}`}
                      </Typography>
                    </Popup>
                  </Marker>
                ))}
              </LayersControl.Overlay>
            )}
          </LayersControl>

          <MarkerClusterGroup
            chunkedLoading
            iconCreateFunction={(cluster) => {
              const count = cluster.getChildCount();
              let size = 'small';
              if (count >= 100) size = 'large';
              else if (count >= 10) size = 'medium';
              
              return L.divIcon({
                html: `<div style="background-color: #2196f3; color: white; border-radius: 50%; width: ${size === 'large' ? '50px' : size === 'medium' ? '40px' : '30px'}; height: ${size === 'large' ? '50px' : size === 'medium' ? '40px' : '30px'}; display: flex; align-items: center; justify-content: center; border: 2px solid white; font-weight: bold;">${count}</div>`,
                className: 'custom-cluster-icon',
                iconSize: [size === 'large' ? 50 : size === 'medium' ? 40 : 30, size === 'large' ? 50 : size === 'medium' ? 40 : 30]
              });
            }}
          >
            {filteredViolations.map((violation, index) => {
              // Проверяем различные варианты координат
              const lat = violation.lat || violation.latitude || 
                         (violation.location && violation.location.coordinates && violation.location.coordinates.latitude);
              const lon = violation.lon || violation.longitude || 
                         (violation.location && violation.location.coordinates && violation.location.coordinates.longitude);
              
              console.log('Map violation check:', {
                id: violation.id,
                category: violation.category,
                lat: lat,
                lon: lon,
                violation: violation
              });
              
              return lat && lon && (
                <Marker
                  key={`${violation.id}-${index}`}
                  position={[lat, lon]}
                  icon={getViolationIcon(violation.category, violation.source)}
                  eventHandlers={{
                    click: () => onViolationClick && onViolationClick(violation)
                  }}
                >
                  <Popup>
                    <Card sx={{ minWidth: 200, maxWidth: 300 }}>
                      <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                          <LocationOn sx={{ color: getCategoryColor(violation.category) }} />
                          <Typography variant="h6" component="div">
                            {formatCategory(violation.category)}
                          </Typography>
                        </Box>
                        
                        <Chip
                          label={`${(violation.confidence * 100).toFixed(1)}% уверенность`}
                          color={violation.confidence > 0.8 ? 'success' : violation.confidence > 0.6 ? 'warning' : 'error'}
                          size="small"
                          sx={{ mb: 1 }}
                        />
                        
                        {violation.address && (
                          <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
                            📍 {typeof violation.address === 'object' ? violation.address.formatted || JSON.stringify(violation.address) : violation.address}
                          </Typography>
                        )}
                        
                        {violation.created_at && (
                          <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
                            📅 {new Date(violation.created_at).toLocaleDateString('ru-RU')}
                          </Typography>
                        )}
                        
                        {violation.image_path && (
                          <Button
                            startIcon={<Visibility />}
                            size="small"
                            onClick={() => onViolationClick && onViolationClick(violation)}
                          >
                            Подробнее
                          </Button>
                        )}
                      </CardContent>
                    </Card>
                  </Popup>
                </Marker>
              );
            })}
          </MarkerClusterGroup>

          {/* OSM Buildings Layer */}
          {showOSMBuildings && osmBuildingsData.map((building, index) => (
            building.lat && building.lon && (
              <Marker
                key={`osm-building-${building.osm_id || index}`}
                position={[building.lat, building.lon]}
                icon={L.divIcon({
                  html: '<div style="background-color: #4caf50; width: 12px; height: 12px; border-radius: 2px; border: 1px solid white;"></div>',
                  className: 'osm-building-icon',
                  iconSize: [12, 12],
                  iconAnchor: [6, 6]
                })}
              >
                <Popup>
                  <Card sx={{ minWidth: 200, maxWidth: 300 }}>
                    <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <MapIcon sx={{ color: '#4caf50' }} />
                        <Typography variant="h6" component="div">
                          {building.name || 'Здание OSM'}
                        </Typography>
                      </Box>
                      
                      <Chip
                        label="OpenStreetMap"
                        color="success"
                        size="small"
                        sx={{ mb: 1 }}
                      />
                      
                      {building.address && (
                        <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
                          📍 {typeof building.address === 'object' ? building.address.formatted || JSON.stringify(building.address) : building.address}
                        </Typography>
                      )}
                      
                      {building.building_type && (
                        <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
                          🏢 Тип: {building.building_type}
                        </Typography>
                      )}
                      
                      {building.levels && (
                        <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
                          🏗️ Этажей: {building.levels}
                        </Typography>
                      )}
                      
                      {building.amenity && (
                        <Typography variant="body2" color="textSecondary">
                          🎯 Назначение: {building.amenity}
                        </Typography>
                      )}
                    </CardContent>
                  </Card>
                </Popup>
              </Marker>
            )
          ))}
        </MapContainer>
      </Box>
    </Box>
  );
};

export default InteractiveMap;
