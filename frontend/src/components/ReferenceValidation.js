import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  LinearProgress,
  Alert,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  ExpandMore as ExpandMoreIcon,
  Visibility as VisibilityIcon,
  LocationOn as LocationOnIcon
} from '@mui/icons-material';
import { api } from '../services/api';

const ReferenceValidation = ({ coordinates, violations, onValidationComplete }) => {
  const [validationResult, setValidationResult] = useState(null);
  const [referenceMatches, setReferenceMatches] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (coordinates && violations && violations.length > 0) {
      performValidation();
    }
  }, [coordinates, violations]);

  const performValidation = async () => {
    setLoading(true);
    setError(null);

    try {
      // Поиск в готовой базе данных заказчика
      const searchResponse = await api.post('/dataset/reference_db/search', {
        latitude: coordinates.latitude,
        longitude: coordinates.longitude,
        radius_km: 0.1
      });

      if (searchResponse.data.success) {
        setReferenceMatches(searchResponse.data.data);

        // Валидация результатов
        const validationData = {
          violations: violations,
          coordinates: coordinates
        };

        const validationResponse = await api.post('/dataset/reference_db/validate', validationData);

        if (validationResponse.data.success) {
          setValidationResult(validationResponse.data.data);
          
          if (onValidationComplete) {
            onValidationComplete({
              validated: validationResponse.data.data.validated,
              matches: searchResponse.data.data,
              validation: validationResponse.data.data
            });
          }
        }
      }
    } catch (err) {
      console.error('Validation error:', err);
      setError('Ошибка валидации против готовой базы данных');
    } finally {
      setLoading(false);
    }
  };

  const getValidationIcon = () => {
    if (!validationResult) return <InfoIcon color="info" />;
    
    if (validationResult.validated) {
      return <CheckCircleIcon color="success" />;
    } else if (validationResult.location_match) {
      return <WarningIcon color="warning" />;
    } else {
      return <CancelIcon color="error" />;
    }
  };

  const getValidationColor = () => {
    if (!validationResult) return 'info';
    
    if (validationResult.validated) {
      return 'success';
    } else if (validationResult.location_match) {
      return 'warning';
    } else {
      return 'error';
    }
  };

  const getValidationMessage = () => {
    if (!validationResult) return 'Выполняется валидация...';
    
    if (validationResult.validated) {
      return '✅ Результат подтвержден готовой базой заказчика';
    } else if (validationResult.location_match) {
      return '⚠️ Найдено совпадение по местоположению, но тип нарушения отличается';
    } else {
      return '❌ Совпадений в готовой базе заказчика не найдено';
    }
  };

  if (loading) {
    return (
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Box display="flex" alignItems="center" mb={2}>
            <InfoIcon color="info" sx={{ mr: 1 }} />
            <Typography variant="h6">
              Валидация против готовой базы данных заказчика
            </Typography>
          </Box>
          <LinearProgress />
          <Typography variant="body2" sx={{ mt: 1 }}>
            Проверяем результаты в базе из 71,895 записей...
          </Typography>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }

  return (
    <Card sx={{ mb: 2 }}>
      <CardContent>
        <Box display="flex" alignItems="center" mb={2}>
          {getValidationIcon()}
          <Typography variant="h6" sx={{ ml: 1 }}>
            Валидация готовой базой заказчика
          </Typography>
          <Chip 
            label={`71,895 записей`} 
            size="small" 
            color="primary" 
            sx={{ ml: 2 }}
          />
        </Box>

        <Alert severity={getValidationColor()} sx={{ mb: 2 }}>
          {getValidationMessage()}
        </Alert>

        {validationResult && (
          <Box mb={2}>
            <Typography variant="body2" color="text.secondary">
              Результат валидации:
            </Typography>
            <Box display="flex" gap={1} mt={1}>
              <Chip 
                label={`Местоположение: ${validationResult.location_match ? '✅' : '❌'}`}
                color={validationResult.location_match ? 'success' : 'default'}
                size="small"
              />
              <Chip 
                label={`Тип нарушения: ${validationResult.type_match ? '✅' : '❌'}`}
                color={validationResult.type_match ? 'success' : 'default'}
                size="small"
              />
              <Chip 
                label={`Общий score: ${(validationResult.validation_score * 100).toFixed(0)}%`}
                color={validationResult.validation_score >= 0.5 ? 'success' : 'warning'}
                size="small"
              />
            </Box>
          </Box>
        )}

        {referenceMatches.length > 0 && (
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle2">
                📊 Найдено {referenceMatches.length} совпадений в готовой базе
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              <List dense>
                {referenceMatches.slice(0, 5).map((match, index) => (
                  <ListItem key={index} divider>
                    <ListItemIcon>
                      <LocationOnIcon color="primary" />
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box display="flex" alignItems="center" gap={1}>
                          <Typography variant="body2" fontWeight="bold">
                            {match.violation_name}
                          </Typography>
                          <Chip 
                            label={match.violation_type} 
                            size="small" 
                            color="primary" 
                          />
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="caption" display="block">
                            Уверенность: {(match.confidence * 100).toFixed(1)}% | 
                            Расстояние: {(match.distance_km * 1000).toFixed(0)}м
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Координаты: {match.latitude.toFixed(5)}, {match.longitude.toFixed(5)}
                          </Typography>
                        </Box>
                      }
                    />
                    {match.image_url && (
                      <Tooltip title="Посмотреть изображение в системе заказчика">
                        <IconButton
                          size="small"
                          onClick={() => window.open(match.image_url, '_blank')}
                        >
                          <VisibilityIcon />
                        </IconButton>
                      </Tooltip>
                    )}
                  </ListItem>
                ))}
              </List>
              
              {referenceMatches.length > 5 && (
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
                  ... и еще {referenceMatches.length - 5} записей
                </Typography>
              )}
            </AccordionDetails>
          </Accordion>
        )}

        <Box mt={2}>
          <Typography variant="caption" color="text.secondary">
            💡 Валидация выполняется против готовой базы данных заказчика (система fivegen)
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
};

export default ReferenceValidation;
