import React, { useState } from 'react';
import { Box, Card, CardContent, Typography, Button, Alert } from '@mui/material';
import api from '../services/api';

const DatasetManager = () => {
  const [loading, setLoading] = useState(false);
  const [alert, setAlert] = useState({ show: false, type: 'info', message: '' });

  const importDataset = async () => {
    setLoading(true);
    try {
      const response = await api.post('/api/dataset/import');
      setAlert({
        show: true,
        type: 'success',
        message: `Импорт завершен: ${response.data.data.total} записей`
      });
    } catch (error) {
      setAlert({
        show: true,
        type: 'error',
        message: `Ошибка: ${error.message}`
      });
    } finally {
      setLoading(false);
    }
  };

  const exportToXLSX = async () => {
    setLoading(true);
    try {
      await api.get('/api/dataset/export');
      setAlert({
        show: true,
        type: 'success',
        message: 'Экспорт в XLSX завершен'
      });
    } catch (error) {
      setAlert({
        show: true,
        type: 'error',
        message: `Ошибка экспорта: ${error.message}`
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>
        Датасет ЛЦТ 2025
      </Typography>

      {alert.show && (
        <Alert severity={alert.type} sx={{ mb: 2 }}>
          {alert.message}
        </Alert>
      )}

      <Card>
        <CardContent>
          <Button
            variant="contained"
            onClick={importDataset}
            disabled={loading}
            sx={{ mr: 2 }}
          >
            Импорт датасета
          </Button>
          
          <Button
            variant="outlined"
            onClick={exportToXLSX}
            disabled={loading}
          >
            Экспорт XLSX
          </Button>
        </CardContent>
      </Card>
    </Box>
  );
};

export default DatasetManager;
