import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Box, Button, Typography, Paper, CircularProgress, Grid, Card, CardContent, TextField, Chip, Switch, FormControlLabel } from '@mui/material';
import { CloudUpload as UploadIcon, Image as ImageIcon, Satellite as SatelliteIcon, Analytics as AnalyticsIcon } from '@mui/icons-material';
import { api } from '../services/api';

const ViolationUploader = ({ onUploadComplete }) => {
  const [files, setFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [results, setResults] = useState([]);
  const [locationHint, setLocationHint] = useState('');
  const [manualCoordinates, setManualCoordinates] = useState({ lat: '', lon: '' });
  const [showManualInput, setShowManualInput] = useState(false);
  const [enableSatelliteAnalysis, setEnableSatelliteAnalysis] = useState(true);
  const [enableGeoAnalysis, setEnableGeoAnalysis] = useState(true);
  const [satelliteData, setSatelliteData] = useState(null);
  
  const onDrop = useCallback(acceptedFiles => {
    const imageFiles = acceptedFiles.filter(file => file.type.startsWith('image/'));
    const filesWithPreview = imageFiles.map(file => ({
      ...file,
      preview: URL.createObjectURL(file),
      id: Math.random().toString(36).substr(2, 9)
    }));
    setFiles(prevFiles => [...prevFiles, ...filesWithPreview]);
  }, []);

  const handleSubmit = async () => {
    if (files.length === 0) return;

    setIsUploading(true);
    const formData = new FormData();

    // Add all files
    files.forEach(file => {
      formData.append('file', file);
    });

    // Add metadata
    formData.append('user_id', 'current_user_id'); // Replace with actual user ID
    formData.append('location_notes', 'User notes');
    formData.append('location_hint', locationHint);

    try {
      const response = await fetch('/api/violations/detect', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (data.success && enableSatelliteAnalysis && data.location) {
        // Получаем спутниковые данные для обнаруженного местоположения
        await loadSatelliteData(data.location.coordinates[0], data.location.coordinates[1]);
      }

      if (!data.success) {
        if (data.error === 'UNABLE_TO_DETERMINE_LOCATION' || data.suggest_manual_input) {
          setShowManualInput(true);
          alert('Unable to determine location automatically. Please enter coordinates manually.');
        } else {
          alert(`Error: ${data.message}`);
        }
        return;
      }

      // Process successful response
      setResults([data]);
      setFiles([]);
      
      if (onUploadComplete) {
        onUploadComplete([data]);
      }
    } catch (error) {
      console.error('Upload error:', error);
    } finally {
      setIsUploading(false);
    }
  };

  const loadSatelliteData = async (lat, lon) => {
    try {
      const bbox = `${lon - 0.01},${lat - 0.01},${lon + 0.01},${lat + 0.01}`;
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
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {'image/*': ['.jpeg', '.jpg', '.png', '.gif']},
    maxFiles: 10,
    multiple: true
  });

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Report Property Violation
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper 
            variant="outlined" 
            sx={{ 
              p: 3, 
              border: '2px dashed',
              borderColor: 'divider',
              height: 300,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              '&:hover': { borderColor: 'primary.main' },
              ...(isDragActive && { borderColor: 'primary.main' })
            }}
            {...getRootProps()}
          >
            <input {...getInputProps()} />
            
            {isUploading ? (
              <Box textAlign="center">
                <CircularProgress />
                <Typography>Processing...</Typography>
              </Box>
            ) : (
              <Box textAlign="center">
                <UploadIcon sx={{ fontSize: 48, mb: 1 }} />
                <Typography variant="h6" gutterBottom>
                  {isDragActive ? 'Drop images here' : 'Drag & drop images here'}
                </Typography>
                <Typography variant="body2" color="textSecondary" paragraph>
                  or click to select files
                </Typography>
                <Button variant="contained" startIcon={<ImageIcon />}>
                  Select Images
                </Button>
              </Box>
            )}
          </Paper>
          
          {files.length > 0 && (
            <Box mt={2}>
              {/* Настройки анализа */}
              <Box sx={{ mb: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Настройки анализа
                </Typography>
                <FormControlLabel
                  control={
                    <Switch
                      checked={enableSatelliteAnalysis}
                      onChange={(e) => setEnableSatelliteAnalysis(e.target.checked)}
                    />
                  }
                  label="Спутниковый анализ"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={enableGeoAnalysis}
                      onChange={(e) => setEnableGeoAnalysis(e.target.checked)}
                    />
                  }
                  label="Геолокационный анализ"
                />
              </Box>
              
              <TextField
                label="Location Hint (optional)"
                placeholder="e.g., Moscow, Red Square, near Kremlin"
                fullWidth
                value={locationHint}
                onChange={(e) => setLocationHint(e.target.value)}
                sx={{ mb: 2 }}
              />

              {showManualInput && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Manual Coordinates (if automatic detection fails)
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <TextField
                        label="Latitude"
                        type="number"
                        fullWidth
                        value={manualCoordinates.lat}
                        onChange={(e) => setManualCoordinates({...manualCoordinates, lat: e.target.value})}
                      />
                    </Grid>
                    <Grid item xs={6}>
                      <TextField
                        label="Longitude"
                        type="number"
                        fullWidth
                        value={manualCoordinates.lon}
                        onChange={(e) => setManualCoordinates({...manualCoordinates, lon: e.target.value})}
                      />
                    </Grid>
                  </Grid>
                </Box>
              )}

              <Button
                variant="contained"
                color="primary"
                fullWidth
                onClick={handleSubmit}
                disabled={isUploading}
              >
                {isUploading ? 'Processing...' : 'Submit for Analysis'}
              </Button>
            </Box>
          )}
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Typography variant="h6" gutterBottom>
            Results ({results.length})
          </Typography>
          
          {results.length === 0 ? (
            <Paper sx={{ p: 3, textAlign: 'center', color: 'text.secondary' }}>
              <Typography>No results yet. Upload images to detect violations.</Typography>
            </Paper>
          ) : (
            <Box sx={{ maxHeight: 500, overflowY: 'auto' }}>
              {results.map((result, index) => (
                <Card key={index} sx={{ mb: 2 }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', gap: 2 }}>
                      <img 
                        src={result.image} 
                        alt="Violation"
                        style={{
                          width: 120,
                          height: 90,
                          objectFit: 'cover',
                          borderRadius: 4
                        }}
                      />
                      <Box>
                        <Typography variant="subtitle1">
                          Violation Detected: {result.violations[0].category.replace(/_/g, ' ')}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Confidence: {(result.violations[0].confidence * 100).toFixed(1)}%
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Location: {result.location.has_gps ? 'GPS Available' : 'No GPS Data'}
                        </Typography>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              ))}
            </Box>
          )}
        </Grid>
      </Grid>
    </Box>
  );
};

export default ViolationUploader;
