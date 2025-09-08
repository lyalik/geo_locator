import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Typography,
  Box,
  Chip,
  Alert,
  CircularProgress
} from '@mui/material';
import { Edit as EditIcon, Delete as DeleteIcon, Save as SaveIcon } from '@mui/icons-material';

const ViolationEditDialog = ({ open, onClose, violation, onUpdate, onDelete }) => {
  const [editedViolation, setEditedViolation] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (violation) {
      setEditedViolation({
        category: violation.category || violation.violations?.[0]?.category || '',
        confidence: violation.confidence || violation.violations?.[0]?.confidence || 0,
        location_hint: violation.metadata?.location_hint || '',
        coordinates: violation.coordinates || violation.location?.coordinates || null,
        address: violation.address || violation.location?.address || {}
      });
    }
  }, [violation]);

  const handleInputChange = (field, value) => {
    setEditedViolation(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleCoordinatesChange = (field, value) => {
    setEditedViolation(prev => ({
      ...prev,
      coordinates: {
        ...prev.coordinates,
        [field]: parseFloat(value) || 0
      }
    }));
  };

  const handleSave = async () => {
    setLoading(true);
    setError('');
    
    try {
      const updateData = {
        category: editedViolation.category,
        confidence: editedViolation.confidence,
        location_hint: editedViolation.location_hint,
        coordinates: editedViolation.coordinates,
        address: editedViolation.address
      };

      await onUpdate(violation.violation_id || violation.id, updateData);
      onClose();
    } catch (err) {
      setError('Ошибка при сохранении изменений: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (window.confirm('Вы уверены, что хотите удалить это нарушение?')) {
      setLoading(true);
      setError('');
      
      try {
        await onDelete(violation.violation_id || violation.id);
        onClose();
      } catch (err) {
        setError('Ошибка при удалении нарушения: ' + err.message);
      } finally {
        setLoading(false);
      }
    }
  };

  const violationCategories = [
    { value: 'unauthorized_signage', label: 'Несанкционированная реклама' },
    { value: 'illegal_construction', label: 'Незаконная постройка' },
    { value: 'blocked_entrance', label: 'Заблокированный вход' },
    { value: 'parking_violation', label: 'Нарушение парковки' },
    { value: 'waste_disposal', label: 'Неправильная утилизация отходов' },
    { value: 'noise_violation', label: 'Шумовое нарушение' },
    { value: 'building_code_violation', label: 'Нарушение строительных норм' },
    { value: 'environmental_violation', label: 'Экологическое нарушение' },
    { value: 'other', label: 'Другое' }
  ];

  if (!violation) return null;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box display="flex" alignItems="center" gap={1}>
          <EditIcon />
          Редактирование нарушения
        </Box>
      </DialogTitle>
      
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Grid container spacing={3}>
          {/* Основная информация */}
          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom>
              Основная информация
            </Typography>
          </Grid>

          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Категория нарушения</InputLabel>
              <Select
                value={editedViolation.category || ''}
                onChange={(e) => handleInputChange('category', e.target.value)}
                label="Категория нарушения"
              >
                {violationCategories.map((cat) => (
                  <MenuItem key={cat.value} value={cat.value}>
                    {cat.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Уверенность (%)"
              type="number"
              value={Math.round((editedViolation.confidence || 0) * 100)}
              onChange={(e) => handleInputChange('confidence', parseFloat(e.target.value) / 100)}
              inputProps={{ min: 0, max: 100 }}
            />
          </Grid>

          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Подсказка местоположения"
              multiline
              rows={2}
              value={editedViolation.location_hint || ''}
              onChange={(e) => handleInputChange('location_hint', e.target.value)}
              placeholder="Дополнительная информация о местоположении..."
            />
          </Grid>

          {/* Координаты */}
          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom>
              Координаты
            </Typography>
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Широта"
              type="number"
              value={editedViolation.coordinates?.latitude || ''}
              onChange={(e) => handleCoordinatesChange('latitude', e.target.value)}
              inputProps={{ step: 'any' }}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Долгота"
              type="number"
              value={editedViolation.coordinates?.longitude || ''}
              onChange={(e) => handleCoordinatesChange('longitude', e.target.value)}
              inputProps={{ step: 'any' }}
            />
          </Grid>

          {/* Информация об изображении */}
          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom>
              Информация об изображении
            </Typography>
          </Grid>

          <Grid item xs={12}>
            <Box display="flex" flexWrap="wrap" gap={1}>
              <Chip label={`ID: ${violation.violation_id || violation.id}`} size="small" />
              <Chip 
                label={`Источник: ${violation.violations?.[0]?.source || 'unknown'}`} 
                size="small" 
                color="primary" 
              />
              <Chip 
                label={`Время: ${new Date(violation.metadata?.timestamp).toLocaleString('ru-RU')}`} 
                size="small" 
                color="secondary" 
              />
            </Box>
          </Grid>

          {violation.image_path && (
            <Grid item xs={12}>
              <Box sx={{ textAlign: 'center', mt: 2 }}>
                <img
                  src={violation.image_path}
                  alt="Нарушение"
                  style={{
                    maxWidth: '100%',
                    maxHeight: '300px',
                    objectFit: 'contain',
                    border: '1px solid #ddd',
                    borderRadius: '8px'
                  }}
                />
              </Box>
            </Grid>
          )}
        </Grid>
      </DialogContent>

      <DialogActions>
        <Button
          onClick={handleDelete}
          color="error"
          startIcon={<DeleteIcon />}
          disabled={loading}
        >
          Удалить
        </Button>
        <Button onClick={onClose} disabled={loading}>
          Отмена
        </Button>
        <Button
          onClick={handleSave}
          variant="contained"
          startIcon={loading ? <CircularProgress size={20} /> : <SaveIcon />}
          disabled={loading}
        >
          Сохранить
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ViolationEditDialog;
