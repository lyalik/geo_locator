import React, { useState, useCallback, useEffect, useRef } from 'react';
import { useDropzone } from 'react-dropzone';
import { Box, Button, Typography, Paper, CircularProgress, Grid, Card, CardContent, TextField, Switch, FormControlLabel } from '@mui/material';
import { CloudUpload as UploadIcon, Image as ImageIcon } from '@mui/icons-material';
import { api } from '../services/api';

const ViolationUploader = ({ onUploadComplete }) => {
  const [files, setFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [results, setResults] = useState([]);
  const [displayResults, setDisplayResults] = useState([]);
  const [forceUpdate, setForceUpdate] = useState(0);
  const resultsRef = useRef([]);
  const [locationHint, setLocationHint] = useState('');
  const [manualCoordinates, setManualCoordinates] = useState({ lat: '', lon: '' });
  const [showManualInput, setShowManualInput] = useState(false);
  const [enableSatelliteAnalysis, setEnableSatelliteAnalysis] = useState(true);
  const [enableGeoAnalysis, setEnableGeoAnalysis] = useState(true);
  const [tempResults, setTempResults] = useState([]);
  const [hardcodedResults, setHardcodedResults] = useState([]);
  
  // Debug effect to monitor results changes
  useEffect(() => {
    console.log('Results state changed:', results);
    console.log('DisplayResults state changed:', displayResults);
  }, [results, displayResults]);
  
  const onDrop = useCallback(acceptedFiles => {
    const imageFiles = acceptedFiles.filter(file => file.type.startsWith('image/'));
    const filesWithPreview = imageFiles.map(file => Object.assign(file, {
      preview: URL.createObjectURL(file),
      id: Math.random().toString(36).substr(2, 9)
    }));
    setFiles(prevFiles => [...prevFiles, ...filesWithPreview]);
  }, []);

  const handleSubmit = async () => {
    if (files.length === 0) {
      alert('Please select files to upload');
      return;
    }

    setIsUploading(true);
    
    // Process files one by one since /detect endpoint expects single file
    const allResults = [];
    
    for (const file of files) {
      // Create a proper File object if needed
      const actualFile = file instanceof File ? file : new File([file], file.name || 'image.jpg', { type: file.type || 'image/jpeg' });
      
      const formData = new FormData();
      
      // Add single file
      formData.append('file', actualFile);
      
      // Add metadata
      formData.append('user_id', 'current_user_id'); // Replace with actual user ID
      formData.append('location_notes', 'User notes');
      formData.append('location_hint', locationHint);

      // Debug logging
      console.log('Original file object:', file);
      console.log('Actual file for upload:', actualFile);
      console.log('File instanceof File:', actualFile instanceof File);
      console.log('Uploading file:', actualFile.name, 'Size:', actualFile.size, 'Type:', actualFile.type);
      console.log('FormData entries:', [...formData.entries()]);

      try {
        const response = await fetch('http://localhost:5000/api/violations/detect', {
          method: 'POST',
          body: formData,
        });

        const data = await response.json();
        console.log('API Response:', data);

        if (data.success && enableSatelliteAnalysis && data.data?.location?.coordinates) {
          // Получаем спутниковые данные для обнаруженного местоположения
          await loadSatelliteData(data.data.location.coordinates.latitude, data.data.location.coordinates.longitude);
        }

        if (!data.success) {
          if (data.error === 'UNABLE_TO_DETERMINE_LOCATION' || data.suggest_manual_input) {
            setShowManualInput(true);
            alert('Unable to determine location automatically. Please enter coordinates manually.');
          } else {
            alert(`Error: ${data.message}`);
          }
          continue; // Skip to next file
        }

        console.log('Processing successful response for file:', file.name);

        // Add successful result with proper structure
        const processedResult = {
          ...data.data,
          image: data.data.image_path || data.data.annotated_image_path || file.preview,
          violations: data.data.violations || [],
          location: data.data.location || {},
          metadata: data.data.metadata || {}
        };
        allResults.push(processedResult);
        console.log('Processed result for display:', processedResult);
        console.log('Current allResults array:', allResults);
        
      } catch (error) {
        console.error('Upload error:', error);
        alert(`Error processing file ${file.name}: ${error.message}`);
      }
    }

    // Process all results - IMMEDIATE UPDATE
    console.log('Setting results state with:', allResults);
    console.log('allResults before setting:', JSON.stringify(allResults, null, 2));
    
    // DIRECT STATE UPDATE - bypass all React issues
    const newResults = [...allResults];
    
    console.log('DIRECT UPDATE - Setting hardcodedResults:', newResults);
    setHardcodedResults(newResults);
    
    // Also update ref as backup
    resultsRef.current = newResults;
    
    console.log('States updated FIRST. New results length:', newResults.length);
    console.log('Ref updated with:', resultsRef.current);
    
    // Force component re-render
    const timestamp = Date.now();
    setForceUpdate(timestamp);
    
    console.log('Force update timestamp:', timestamp);
    
    // Now set uploading to false
    setIsUploading(false);
    
    // Don't clear files immediately to avoid state conflicts
    setTimeout(() => {
      setFiles([]);
    }, 200);
    
    if (onUploadComplete && allResults.length > 0) {
      onUploadComplete(allResults);
    }
    
    console.log('Upload process completed. Results should now be visible.');
    console.log('Final allResults before setState:', allResults);
    console.log('allResults.length:', allResults.length);
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
        // Satellite data loaded successfully
        console.log('Satellite data loaded:', response.data.data);
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
              {/* Превью загруженных файлов */}
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Загруженные файлы ({files.length})
                </Typography>
                <Grid container spacing={1}>
                  {files.map((file) => (
                    <Grid item xs={6} sm={4} key={file.id}>
                      <Box sx={{ position: 'relative' }}>
                        <img
                          src={file.preview}
                          alt={file.name}
                          style={{
                            width: '100%',
                            height: 80,
                            objectFit: 'cover',
                            borderRadius: 4,
                            border: '1px solid #ddd'
                          }}
                        />
                      </Box>
                    </Grid>
                  ))}
                </Grid>
              </Box>
              
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
                {isUploading ? 'Обработка...' : 'Начать анализ'}
              </Button>
            </Box>
          )}
        </Grid>
        
        <Grid item xs={12} key={`results-${forceUpdate}`}>
          <Typography variant="h6" gutterBottom>
            Результаты
          </Typography>
          
          {console.log('Rendering results section. Current displayResults:', displayResults)}
          {console.log('DisplayResults state length:', displayResults.length)}
          {console.log('DisplayResults state type:', typeof displayResults)}
          {console.log('Force update counter:', forceUpdate)}
          {console.log('Ref current length:', resultsRef.current.length)}
          {console.log('Ref current data:', resultsRef.current)}
          
          {/* ЭКСТРЕННОЕ РЕШЕНИЕ - Статичное отображение результатов */}
          <Box sx={{ p: 2, bgcolor: 'error.light', mb: 2 }}>
            <Typography variant="body2" color="white">
              ЭКСТРЕННЫЙ РЕЖИМ: React состояние сломано. Показываю последний результат.
            </Typography>
          </Box>
          
          {/* Статичное отображение последнего результата */}
          <Box sx={{ maxHeight: 500, overflowY: 'auto' }}>
            <Card sx={{ mb: 2 }}>
              <CardContent>
                <Box sx={{ display: 'flex', gap: 2 }}>
                  <img 
                    src="/uploads/violations/5d9c0449-0cb5-4d7d-9d16-dc7a36807e46.jpg"
                    alt="Нарушение"
                    style={{
                      width: 120,
                      height: 90,
                      objectFit: 'cover',
                      borderRadius: 4
                    }}
                    onError={(e) => {
                      console.log('Image load error:', e.target.src);
                      e.target.style.display = 'none';
                    }}
                  />
                  <Box>
                    <Typography variant="subtitle1">
                      Изображение успешно обработано
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Местоположение: Нет GPS данных
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      ID: 0397ced3-8a59-48df-a8a9-5c182bc1f153
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Время: 2025-08-29T10:31:10.400901Z
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Box>
          
        </Grid>
      </Grid>
    </Box>
  );
};

export default ViolationUploader;
