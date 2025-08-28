import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Box, Button, Typography, Paper, CircularProgress, Grid, Card, CardContent, 
  TextField, LinearProgress, IconButton, Chip, Alert, Dialog, DialogTitle,
  DialogContent, DialogActions, List, ListItem, ListItemText, ListItemIcon
} from '@mui/material';
import {
  CloudUpload as UploadIcon, Image as ImageIcon, Delete as DeleteIcon,
  CheckCircle as CheckIcon, Error as ErrorIcon, Schedule as ScheduleIcon,
  Visibility as ViewIcon, GetApp as DownloadIcon
} from '@mui/icons-material';

const BatchViolationUploader = ({ onUploadComplete, maxFiles = 20 }) => {
  const [files, setFiles] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingQueue, setProcessingQueue] = useState([]);
  const [completedUploads, setCompletedUploads] = useState([]);
  const [locationHint, setLocationHint] = useState('');
  const [showResults, setShowResults] = useState(false);
  const [globalProgress, setGlobalProgress] = useState(0);

  const onDrop = useCallback(acceptedFiles => {
    const newFiles = acceptedFiles
      .filter(file => file.type.startsWith('image/'))
      .slice(0, maxFiles - files.length)
      .map(file => ({
        id: Math.random().toString(36).substr(2, 9),
        file,
        preview: URL.createObjectURL(file),
        status: 'pending', // pending, processing, completed, error
        progress: 0,
        result: null,
        error: null
      }));

    setFiles(prevFiles => [...prevFiles, ...newFiles]);
  }, [files.length, maxFiles]);

  const removeFile = (fileId) => {
    setFiles(prevFiles => {
      const updatedFiles = prevFiles.filter(f => f.id !== fileId);
      // Clean up preview URLs
      const fileToRemove = prevFiles.find(f => f.id === fileId);
      if (fileToRemove?.preview) {
        URL.revokeObjectURL(fileToRemove.preview);
      }
      return updatedFiles;
    });
  };

  const processFiles = async () => {
    if (files.length === 0) return;

    setIsProcessing(true);
    setProcessingQueue([...files]);
    setGlobalProgress(0);

    const results = [];
    
    for (let i = 0; i < files.length; i++) {
      const fileItem = files[i];
      
      // Update file status to processing
      setFiles(prevFiles => 
        prevFiles.map(f => 
          f.id === fileItem.id ? { ...f, status: 'processing', progress: 0 } : f
        )
      );

      try {
        const result = await uploadSingleFile(fileItem, (progress) => {
          setFiles(prevFiles => 
            prevFiles.map(f => 
              f.id === fileItem.id ? { ...f, progress } : f
            )
          );
        });

        // Update file status to completed
        setFiles(prevFiles => 
          prevFiles.map(f => 
            f.id === fileItem.id ? { 
              ...f, 
              status: 'completed', 
              progress: 100, 
              result 
            } : f
          )
        );

        results.push(result);
      } catch (error) {
        // Update file status to error
        setFiles(prevFiles => 
          prevFiles.map(f => 
            f.id === fileItem.id ? { 
              ...f, 
              status: 'error', 
              error: error.message 
            } : f
          )
        );
      }

      // Update global progress
      setGlobalProgress(((i + 1) / files.length) * 100);
    }

    setCompletedUploads(results);
    setIsProcessing(false);
    setShowResults(true);
    
    if (onUploadComplete) {
      onUploadComplete(results);
    }
  };

  const uploadSingleFile = async (fileItem, onProgress) => {
    const formData = new FormData();
    formData.append('file', fileItem.file);
    formData.append('location_hint', locationHint);
    formData.append('user_id', 'current_user_id'); // Replace with actual user ID

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();

      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable) {
          const progress = (event.loaded / event.total) * 50; // Upload is 50% of total progress
          onProgress(progress);
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status === 200) {
          try {
            const response = JSON.parse(xhr.responseText);
            onProgress(100);
            resolve(response);
          } catch (error) {
            reject(new Error('Ошибка обработки ответа сервера'));
          }
        } else {
          reject(new Error(`Ошибка сервера: ${xhr.status}`));
        }
      });

      xhr.addEventListener('error', () => {
        reject(new Error('Ошибка сети'));
      });

      // Simulate processing progress (second 50%)
      xhr.addEventListener('loadend', () => {
        if (xhr.status === 200) {
          let processingProgress = 50;
          const processingInterval = setInterval(() => {
            processingProgress += 10;
            onProgress(processingProgress);
            if (processingProgress >= 100) {
              clearInterval(processingInterval);
            }
          }, 200);
        }
      });

      xhr.open('POST', '/api/violations/detect');
      xhr.send(formData);
    });
  };

  const clearAll = () => {
    files.forEach(file => {
      if (file.preview) {
        URL.revokeObjectURL(file.preview);
      }
    });
    setFiles([]);
    setCompletedUploads([]);
    setGlobalProgress(0);
  };

  const exportResults = () => {
    const dataStr = JSON.stringify(completedUploads, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `batch_upload_results_${new Date().toISOString().split('T')[0]}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {'image/*': ['.jpeg', '.jpg', '.png', '.gif']},
    maxFiles: maxFiles - files.length,
    multiple: true,
    disabled: isProcessing
  });

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return <CheckIcon color="success" />;
      case 'error': return <ErrorIcon color="error" />;
      case 'processing': return <CircularProgress size={20} />;
      default: return <ScheduleIcon color="action" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'success';
      case 'error': return 'error';
      case 'processing': return 'primary';
      default: return 'default';
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Пакетная загрузка нарушений
      </Typography>

      {/* Upload Area */}
      <Paper 
        variant="outlined" 
        sx={{ 
          p: 3, 
          border: '2px dashed',
          borderColor: isDragActive ? 'primary.main' : 'divider',
          backgroundColor: isDragActive ? 'action.hover' : 'background.paper',
          cursor: isProcessing ? 'not-allowed' : 'pointer',
          opacity: isProcessing ? 0.6 : 1,
          mb: 3
        }}
        {...getRootProps()}
      >
        <input {...getInputProps()} />
        
        <Box textAlign="center">
          <UploadIcon sx={{ fontSize: 48, mb: 1, color: 'primary.main' }} />
          <Typography variant="h6" gutterBottom>
            {isDragActive ? 'Отпустите файлы здесь' : 'Перетащите изображения или нажмите для выбора'}
          </Typography>
          <Typography variant="body2" color="textSecondary" paragraph>
            Поддерживаются: JPG, PNG, GIF. Максимум {maxFiles} файлов
          </Typography>
          <Typography variant="body2" color="textSecondary">
            Выбрано: {files.length}/{maxFiles}
          </Typography>
        </Box>
      </Paper>

      {/* Location Hint */}
      {files.length > 0 && (
        <TextField
          label="Подсказка местоположения (для всех фото)"
          placeholder="например: Москва, Красная площадь, рядом с Кремлем"
          fullWidth
          value={locationHint}
          onChange={(e) => setLocationHint(e.target.value)}
          sx={{ mb: 3 }}
          disabled={isProcessing}
        />
      )}

      {/* Global Progress */}
      {isProcessing && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="body2" gutterBottom>
            Общий прогресс: {Math.round(globalProgress)}%
          </Typography>
          <LinearProgress variant="determinate" value={globalProgress} />
        </Box>
      )}

      {/* File List */}
      {files.length > 0 && (
        <Box sx={{ mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">
              Загруженные файлы ({files.length})
            </Typography>
            <Box>
              <Button
                variant="contained"
                onClick={processFiles}
                disabled={isProcessing || files.length === 0}
                sx={{ mr: 1 }}
              >
                {isProcessing ? 'Обработка...' : 'Обработать все'}
              </Button>
              <Button
                variant="outlined"
                onClick={clearAll}
                disabled={isProcessing}
              >
                Очистить все
              </Button>
            </Box>
          </Box>

          <Grid container spacing={2}>
            {files.map((fileItem) => (
              <Grid item xs={12} sm={6} md={4} key={fileItem.id}>
                <Card>
                  <Box sx={{ position: 'relative' }}>
                    <img
                      src={fileItem.preview}
                      alt={fileItem.file.name}
                      style={{
                        width: '100%',
                        height: 150,
                        objectFit: 'cover'
                      }}
                    />
                    {!isProcessing && (
                      <IconButton
                        sx={{ position: 'absolute', top: 8, right: 8, backgroundColor: 'rgba(255,255,255,0.8)' }}
                        onClick={() => removeFile(fileItem.id)}
                        size="small"
                      >
                        <DeleteIcon />
                      </IconButton>
                    )}
                  </Box>
                  <CardContent sx={{ p: 2 }}>
                    <Typography variant="body2" noWrap title={fileItem.file.name}>
                      {fileItem.file.name}
                    </Typography>
                    <Typography variant="caption" color="textSecondary">
                      {(fileItem.file.size / 1024 / 1024).toFixed(2)} MB
                    </Typography>
                    
                    <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                      {getStatusIcon(fileItem.status)}
                      <Chip
                        label={fileItem.status === 'pending' ? 'Ожидание' :
                               fileItem.status === 'processing' ? 'Обработка' :
                               fileItem.status === 'completed' ? 'Завершено' : 'Ошибка'}
                        color={getStatusColor(fileItem.status)}
                        size="small"
                        sx={{ ml: 1 }}
                      />
                    </Box>

                    {fileItem.status === 'processing' && (
                      <LinearProgress 
                        variant="determinate" 
                        value={fileItem.progress} 
                        sx={{ mt: 1 }}
                      />
                    )}

                    {fileItem.error && (
                      <Alert severity="error" sx={{ mt: 1 }}>
                        {fileItem.error}
                      </Alert>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>
      )}

      {/* Results Dialog */}
      <Dialog
        open={showResults}
        onClose={() => setShowResults(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Результаты обработки
          <IconButton
            onClick={exportResults}
            sx={{ float: 'right' }}
          >
            <DownloadIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          <Typography variant="body1" gutterBottom>
            Обработано: {completedUploads.length} из {files.length} файлов
          </Typography>
          
          <List>
            {files.map((fileItem) => (
              <ListItem key={fileItem.id}>
                <ListItemIcon>
                  {getStatusIcon(fileItem.status)}
                </ListItemIcon>
                <ListItemText
                  primary={fileItem.file.name}
                  secondary={
                    fileItem.status === 'completed' && fileItem.result
                      ? `Найдено ${fileItem.result.data?.violations?.length || 0} нарушений`
                      : fileItem.error || 'Ожидание обработки'
                  }
                />
                {fileItem.result && (
                  <IconButton onClick={() => console.log(fileItem.result)}>
                    <ViewIcon />
                  </IconButton>
                )}
              </ListItem>
            ))}
          </List>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowResults(false)}>
            Закрыть
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default BatchViolationUploader;
