import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  IconButton,
  Tooltip,
  Switch,
  FormControlLabel,
  Chip,
  Button,
  Menu,
  MenuItem
} from '@mui/material';
import {
  Map as MapIcon,
  Satellite as SatelliteIcon,
  Layers as LayersIcon,
  Fullscreen as FullscreenIcon,
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  MyLocation as MyLocationIcon
} from '@mui/icons-material';

const InteractiveResultsMap = ({ 
  coordinates, 
  satelliteData, 
  locationInfo, 
  height = 400,
  showControls = true,
  showSatelliteToggle = true 
}) => {
  const mapRef = useRef(null);
  const [map, setMap] = useState(null);
  const [satelliteMode, setSatelliteMode] = useState(false);
  const [layersMenuAnchor, setLayersMenuAnchor] = useState(null);
  const [currentLayer, setCurrentLayer] = useState('osm');
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Доступные слои карты
  const mapLayers = {
    osm: {
      name: 'OpenStreetMap',
      url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      attribution: '© OpenStreetMap contributors'
    },
    yandex_map: {
      name: 'Яндекс Карты',
      url: 'https://core-renderer-tiles.maps.yandex.net/tiles?l=map&v=21.06.03-0&x={x}&y={y}&z={z}&scale=1&lang=ru_RU',
      attribution: '© Яндекс'
    },
    yandex_satellite: {
      name: 'Яндекс Спутник',
      url: 'https://core-sat.maps.yandex.net/tiles?l=sat&v=3.1021.0&x={x}&y={y}&z={z}&scale=1',
      attribution: '© Яндекс'
    },
    yandex_hybrid: {
      name: 'Яндекс Гибрид',
      url: 'https://core-sat.maps.yandex.net/tiles?l=sat&v=3.1021.0&x={x}&y={y}&z={z}&scale=1',
      attribution: '© Яндекс'
    }
  };

  useEffect(() => {
    if (!coordinates || !mapRef.current) return;

    // Динамический импорт Leaflet
    const initMap = async () => {
      const L = await import('leaflet');
      await import('leaflet/dist/leaflet.css');

      // Исправляем иконки маркеров Leaflet
      delete L.Icon.Default.prototype._getIconUrl;
      L.Icon.Default.mergeOptions({
        iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
        iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
      });

      const mapInstance = L.map(mapRef.current).setView(
        [coordinates.latitude, coordinates.longitude], 
        15
      );

      // Добавляем базовый слой
      const tileLayer = L.tileLayer(mapLayers[currentLayer].url, {
        attribution: mapLayers[currentLayer].attribution,
        maxZoom: 18
      }).addTo(mapInstance);

      // Создаем кастомную иконку для найденных координат
      const resultIcon = L.divIcon({
        html: `
          <div style="
            background: #2196F3;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            border: 3px solid white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 12px;
          ">📍</div>
        `,
        className: 'custom-result-marker',
        iconSize: [30, 30],
        iconAnchor: [15, 15]
      });

      // Добавляем маркер с результатами
      const marker = L.marker([coordinates.latitude, coordinates.longitude], {
        icon: resultIcon
      }).addTo(mapInstance);

      // Создаем popup с информацией
      const popupContent = `
        <div style="min-width: 200px;">
          <h4 style="margin: 0 0 8px 0; color: #2196F3;">📍 Найденные координаты</h4>
          <p style="margin: 4px 0;"><strong>Широта:</strong> ${coordinates.latitude.toFixed(6)}</p>
          <p style="margin: 4px 0;"><strong>Долгота:</strong> ${coordinates.longitude.toFixed(6)}</p>
          <p style="margin: 4px 0;"><strong>Точность:</strong> ${Math.round(coordinates.confidence * 100)}%</p>
          <p style="margin: 4px 0;"><strong>Источник:</strong> ${coordinates.source}</p>
          ${locationInfo?.address ? `<p style="margin: 4px 0;"><strong>Адрес:</strong> ${locationInfo.address}</p>` : ''}
          <div style="margin-top: 8px;">
            <a href="https://yandex.ru/maps/?ll=${coordinates.longitude},${coordinates.latitude}&z=15&pt=${coordinates.longitude},${coordinates.latitude}" 
               target="_blank" style="color: #2196F3; text-decoration: none;">
              🗺️ Открыть в Яндекс.Картах
            </a>
          </div>
        </div>
      `;

      marker.bindPopup(popupContent).openPopup();

      // Добавляем круг точности
      const accuracyRadius = (1 - coordinates.confidence) * 100; // Радиус в метрах
      L.circle([coordinates.latitude, coordinates.longitude], {
        color: '#2196F3',
        fillColor: '#2196F3',
        fillOpacity: 0.1,
        radius: accuracyRadius
      }).addTo(mapInstance);

      setMap(mapInstance);

      return () => {
        mapInstance.remove();
      };
    };

    initMap();
  }, [coordinates, currentLayer]);

  // Переключение слоев карты
  const handleLayerChange = (layerKey) => {
    setCurrentLayer(layerKey);
    setLayersMenuAnchor(null);
  };

  // Переключение в полноэкранный режим
  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  // Центрирование на координатах
  const centerOnCoordinates = () => {
    if (map && coordinates) {
      map.setView([coordinates.latitude, coordinates.longitude], 15);
    }
  };

  // Увеличение масштаба
  const zoomIn = () => {
    if (map) {
      map.zoomIn();
    }
  };

  // Уменьшение масштаба
  const zoomOut = () => {
    if (map) {
      map.zoomOut();
    }
  };

  if (!coordinates) {
    return (
      <Card>
        <CardContent>
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <MapIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary">
              Координаты не найдены
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Загрузите изображение или видео для отображения на карте
            </Typography>
          </Box>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card sx={{ 
      position: isFullscreen ? 'fixed' : 'relative',
      top: isFullscreen ? 0 : 'auto',
      left: isFullscreen ? 0 : 'auto',
      width: isFullscreen ? '100vw' : '100%',
      height: isFullscreen ? '100vh' : height,
      zIndex: isFullscreen ? 9999 : 'auto'
    }}>
      <CardContent sx={{ p: 0, height: '100%', position: 'relative' }}>
        {/* Заголовок карты */}
        <Box sx={{ 
          position: 'absolute', 
          top: 8, 
          left: 8, 
          right: 8, 
          zIndex: 1000,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Chip 
              icon={<MapIcon />} 
              label="Интерактивная карта" 
              size="small"
              sx={{ backgroundColor: 'rgba(255,255,255,0.9)' }}
            />
            <Chip 
              label={`${coordinates.latitude.toFixed(4)}, ${coordinates.longitude.toFixed(4)}`}
              size="small"
              sx={{ backgroundColor: 'rgba(33,150,243,0.9)', color: 'white' }}
            />
          </Box>

          {/* Элементы управления */}
          {showControls && (
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Tooltip title="Слои карты">
                <IconButton 
                  size="small"
                  onClick={(e) => setLayersMenuAnchor(e.currentTarget)}
                  sx={{ backgroundColor: 'rgba(255,255,255,0.9)' }}
                >
                  <LayersIcon />
                </IconButton>
              </Tooltip>

              <Tooltip title="Увеличить">
                <IconButton 
                  size="small"
                  onClick={zoomIn}
                  sx={{ backgroundColor: 'rgba(255,255,255,0.9)' }}
                >
                  <ZoomInIcon />
                </IconButton>
              </Tooltip>

              <Tooltip title="Уменьшить">
                <IconButton 
                  size="small"
                  onClick={zoomOut}
                  sx={{ backgroundColor: 'rgba(255,255,255,0.9)' }}
                >
                  <ZoomOutIcon />
                </IconButton>
              </Tooltip>

              <Tooltip title="Центрировать">
                <IconButton 
                  size="small"
                  onClick={centerOnCoordinates}
                  sx={{ backgroundColor: 'rgba(255,255,255,0.9)' }}
                >
                  <MyLocationIcon />
                </IconButton>
              </Tooltip>

              <Tooltip title={isFullscreen ? "Выйти из полноэкранного режима" : "Полноэкранный режим"}>
                <IconButton 
                  size="small"
                  onClick={toggleFullscreen}
                  sx={{ backgroundColor: 'rgba(255,255,255,0.9)' }}
                >
                  <FullscreenIcon />
                </IconButton>
              </Tooltip>
            </Box>
          )}
        </Box>

        {/* Меню выбора слоев */}
        <Menu
          anchorEl={layersMenuAnchor}
          open={Boolean(layersMenuAnchor)}
          onClose={() => setLayersMenuAnchor(null)}
        >
          {Object.entries(mapLayers).map(([key, layer]) => (
            <MenuItem 
              key={key}
              onClick={() => handleLayerChange(key)}
              selected={currentLayer === key}
            >
              {layer.name}
            </MenuItem>
          ))}
        </Menu>

        {/* Контейнер карты */}
        <div 
          ref={mapRef} 
          style={{ 
            width: '100%', 
            height: '100%',
            borderRadius: isFullscreen ? 0 : 8
          }} 
        />

        {/* Информация о спутниковых данных */}
        {satelliteData && (
          <Box sx={{ 
            position: 'absolute', 
            bottom: 8, 
            left: 8, 
            zIndex: 1000 
          }}>
            <Chip 
              icon={<SatelliteIcon />}
              label={`Спутник: ${satelliteData.source || 'Доступно'}`}
              size="small"
              sx={{ backgroundColor: 'rgba(76,175,80,0.9)', color: 'white' }}
            />
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default InteractiveResultsMap;
