import React, { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, LayersControl } from 'react-leaflet';
import MarkerClusterGroup from 'react-leaflet-cluster';
import L from 'leaflet';
import { Box, Card, CardContent, Typography, Chip, Button, FormControl, InputLabel, Select, MenuItem, TextField, Switch, FormControlLabel } from '@mui/material';
import { LocationOn, Visibility, FilterList, GetApp, Satellite } from '@mui/icons-material';
import { api } from '../services/api';
import 'leaflet/dist/leaflet.css';

// Fix for default markers in react-leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

// Custom violation icons
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
  const [satelliteData, setSatelliteData] = useState(null);
  const [loadingSatellite, setLoadingSatellite] = useState(false);
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

  const getViolationIcon = (category) => {
    return violationIcons[category] || violationIcons.default;
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
    const newShowSatellite = !showSatellite;
    setShowSatellite(newShowSatellite);
    
    if (newShowSatellite && mapRef.current && !satelliteData) {
      const map = mapRef.current;
      const bounds = map.getBounds();
      await loadSatelliteData(bounds);
    }
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
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
                checked={showSatellite}
                onChange={toggleSatelliteLayer}
                disabled={loadingSatellite}
              />
            }
            label="Спутниковый слой"
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
      <Box sx={{ flex: 1, position: 'relative' }}>
        <MapContainer
          center={defaultCenter}
          zoom={10}
          style={{ height: '100%', width: '100%' }}
          ref={mapRef}
        >
          <LayersControl position="topright">
            <LayersControl.BaseLayer checked name="OpenStreetMap">
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
            </LayersControl.BaseLayer>
            
            <LayersControl.BaseLayer name="Спутниковая">
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
            {filteredViolations.map((violation, index) => (
              violation.lat && violation.lon && (
                <Marker
                  key={`${violation.id}-${index}`}
                  position={[violation.lat, violation.lon]}
                  icon={getViolationIcon(violation.category)}
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
                            📍 {violation.address}
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
              )
            ))}
          </MarkerClusterGroup>
        </MapContainer>
      </Box>
    </Box>
  );
};

export default InteractiveMap;
