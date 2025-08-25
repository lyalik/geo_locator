import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Box, Button, Typography, Paper, CircularProgress, Grid, Card, CardContent } from '@mui/material';
import { CloudUpload as UploadIcon, Image as ImageIcon } from '@mui/icons-material';

const ViolationUploader = () => {
  const [files, setFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [results, setResults] = useState([]);
  
  const onDrop = useCallback(acceptedFiles => {
    const imageFiles = acceptedFiles.filter(file => file.type.startsWith('image/'));
    const filesWithPreview = imageFiles.map(file => ({
      ...file,
      preview: URL.createObjectURL(file),
      id: Math.random().toString(36).substr(2, 9)
    }));
    setFiles(prevFiles => [...prevFiles, ...filesWithPreview]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {'image/*': ['.jpeg', '.jpg', '.png', '.gif']},
    maxFiles: 10,
    multiple: true
  });

  const handleSubmit = async () => {
    if (files.length === 0) return;
    
    setIsUploading(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // In a real app, you would upload to your backend here
      // const formData = new FormData();
      // files.forEach(file => formData.append('files', file));
      // const response = await fetch('/api/violations/detect', {
      //   method: 'POST',
      //   body: formData,
      // });
      // const result = await response.json();
      
      // Mock response
      const mockResults = files.map(file => ({
        id: Math.random().toString(36).substr(2, 9),
        image: file.preview,
        violations: [{
          category: 'unauthorized_construction',
          confidence: 0.85 + Math.random() * 0.14
        }],
        location: {
          coordinates: {
            latitude: 55.7558 + (Math.random() * 0.1 - 0.05),
            longitude: 37.6173 + (Math.random() * 0.1 - 0.05)
          },
          has_gps: Math.random() > 0.5
        }
      }));
      
      setResults(prev => [...prev, ...mockResults]);
      setFiles([]);
      
    } catch (error) {
      console.error('Error uploading files:', error);
    } finally {
      setIsUploading(false);
    }
  };

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
