import React from 'react';
import {
  Box, Card, CardContent, Typography, Chip, Grid, LinearProgress,
  Accordion, AccordionSummary, AccordionDetails, List, ListItem,
  ListItemText, Divider, Alert
} from '@mui/material';
import {
  CheckCircle as ValidIcon,
  Cancel as InvalidIcon,
  Info as InfoIcon,
  ExpandMore as ExpandMoreIcon,
  LocationOn as LocationIcon,
  Category as CategoryIcon,
  Verified as VerifiedIcon
} from '@mui/icons-material';

/**
 * Компонент для отображения результатов валидации по готовой базе заказчика
 */
const ValidationDisplay = ({ validation, referenceMatches }) => {
  if (!validation && (!referenceMatches || referenceMatches.length === 0)) {
    return null;
  }

  // Получаем данные валидации
  const validated = validation?.validated || false;
  const validationScore = validation?.validation_score || 0;
  const locationMatch = validation?.location_match || false;
  const typeMatch = validation?.type_match || false;
  const message = validation?.message || 'Валидация не проведена';
  const referenceCount = validation?.reference_records?.length || referenceMatches?.length || 0;

  // Определяем цвет и иконку в зависимости от результата
  const getValidationColor = () => {
    if (validationScore >= 0.7) return 'success';
    if (validationScore >= 0.5) return 'warning';
    return 'error';
  };

  const getValidationIcon = () => {
    if (validated) {
      return <ValidIcon sx={{ color: 'success.main', fontSize: 40 }} />;
    }
    return <InvalidIcon sx={{ color: 'error.main', fontSize: 40 }} />;
  };

  // Форматирование типов нарушений
  const formatViolationType = (type) => {
    const typeMapping = {
      '18-001': 'Строительная площадка',
      '00-022': 'Нарушения недвижимости'
    };
    return typeMapping[type] || type;
  };

  return (
    <Card elevation={3} sx={{ mt: 2, border: `2px solid ${validated ? '#4caf50' : '#ff9800'}` }}>
      <CardContent>
        {/* Заголовок */}
        <Box display="flex" alignItems="center" mb={2}>
          {getValidationIcon()}
          <Box ml={2} flex={1}>
            <Typography variant="h6" fontWeight="bold">
              🔍 Валидация по готовой базе заказчика
            </Typography>
            <Typography variant="body2" color="text.secondary">
              База данных: 71,895 записей (18-001, 00-022)
            </Typography>
          </Box>
          <Chip
            label={validated ? 'ВАЛИДИРОВАНО' : 'НЕ ВАЛИДИРОВАНО'}
            color={getValidationColor()}
            icon={validated ? <VerifiedIcon /> : <InfoIcon />}
            sx={{ fontWeight: 'bold' }}
          />
        </Box>

        {/* Прогресс валидации */}
        <Box mb={2}>
          <Box display="flex" justifyContent="space-between" mb={1}>
            <Typography variant="body2" fontWeight="bold">
              Степень валидации
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {(validationScore * 100).toFixed(0)}%
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={validationScore * 100}
            color={getValidationColor()}
            sx={{ height: 8, borderRadius: 4 }}
          />
        </Box>

        {/* Статистика валидации */}
        <Grid container spacing={2} mb={2}>
          <Grid item xs={4}>
            <Box textAlign="center" p={1} bgcolor={locationMatch ? '#e8f5e9' : '#ffebee'} borderRadius={2}>
              <LocationIcon sx={{ color: locationMatch ? 'success.main' : 'error.main', fontSize: 30 }} />
              <Typography variant="caption" display="block" fontWeight="bold">
                Координаты
              </Typography>
              <Chip
                label={locationMatch ? 'СОВПАЛО' : 'НЕ СОВПАЛО'}
                size="small"
                color={locationMatch ? 'success' : 'error'}
                sx={{ mt: 0.5 }}
              />
            </Box>
          </Grid>
          <Grid item xs={4}>
            <Box textAlign="center" p={1} bgcolor={typeMatch ? '#e8f5e9' : '#ffebee'} borderRadius={2}>
              <CategoryIcon sx={{ color: typeMatch ? 'success.main' : 'error.main', fontSize: 30 }} />
              <Typography variant="caption" display="block" fontWeight="bold">
                Тип нарушения
              </Typography>
              <Chip
                label={typeMatch ? 'СОВПАЛО' : 'НЕ СОВПАЛО'}
                size="small"
                color={typeMatch ? 'success' : 'error'}
                sx={{ mt: 0.5 }}
              />
            </Box>
          </Grid>
          <Grid item xs={4}>
            <Box textAlign="center" p={1} bgcolor={referenceCount > 0 ? '#e8f5e9' : '#fff3e0'} borderRadius={2}>
              <VerifiedIcon sx={{ color: referenceCount > 0 ? 'success.main' : 'warning.main', fontSize: 30 }} />
              <Typography variant="caption" display="block" fontWeight="bold">
                Совпадений в базе
              </Typography>
              <Chip
                label={referenceCount}
                size="small"
                color={referenceCount > 0 ? 'success' : 'warning'}
                sx={{ mt: 0.5 }}
              />
            </Box>
          </Grid>
        </Grid>

        {/* Сообщение */}
        <Alert severity={validated ? 'success' : 'info'} icon={<InfoIcon />} sx={{ mb: 2 }}>
          {message}
        </Alert>

        {/* Список совпадений в базе заказчика */}
        {referenceMatches && referenceMatches.length > 0 && (
          <Accordion defaultExpanded={referenceCount > 0}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle1" fontWeight="bold">
                📋 Совпадения в готовой базе ({referenceMatches.length})
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              <List dense>
                {referenceMatches.slice(0, 5).map((match, index) => (
                  <React.Fragment key={index}>
                    <ListItem>
                      <ListItemText
                        primary={
                          <Box display="flex" alignItems="center" gap={1}>
                            <Chip
                              label={match.violation_type}
                              size="small"
                              color={match.violation_type === '18-001' ? 'warning' : 'info'}
                            />
                            <Typography variant="body2" fontWeight="bold">
                              {formatViolationType(match.violation_type)}
                            </Typography>
                          </Box>
                        }
                        secondary={
                          <Box mt={1}>
                            <Typography variant="caption" display="block">
                              📍 Расстояние: <strong>{(match.distance_km * 1000).toFixed(0)} м</strong>
                            </Typography>
                            <Typography variant="caption" display="block">
                              🎯 Уверенность: <strong>{(match.confidence * 100).toFixed(0)}%</strong>
                            </Typography>
                            <Typography variant="caption" display="block" color="text.secondary">
                              📸 ID: {match.id?.substring(0, 8)}... | Camera: {match.camera_id?.substring(0, 8)}...
                            </Typography>
                            {match.timestamp && (
                              <Typography variant="caption" display="block" color="text.secondary">
                                🕒 {new Date(match.timestamp * 1000).toLocaleString('ru-RU')}
                              </Typography>
                            )}
                          </Box>
                        }
                      />
                    </ListItem>
                    {index < referenceMatches.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
              {referenceMatches.length > 5 && (
                <Typography variant="caption" color="text.secondary" display="block" textAlign="center" mt={1}>
                  Показано 5 из {referenceMatches.length} совпадений
                </Typography>
              )}
            </AccordionDetails>
          </Accordion>
        )}

        {/* Если нет совпадений */}
        {(!referenceMatches || referenceMatches.length === 0) && (
          <Alert severity="warning" icon={<InfoIcon />}>
            Нет совпадений в готовой базе заказчика в радиусе 50 метров
          </Alert>
        )}
      </CardContent>
    </Card>
  );
};

export default ValidationDisplay;
