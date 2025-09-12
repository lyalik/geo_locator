import React, { useState, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Chip,
  IconButton,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  Divider,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Image as ImageIcon,
  VideoFile as VideoIcon,
  Edit as EditIcon,
  ExpandMore as ExpandMoreIcon,
  PhotoLibrary as PhotoLibraryIcon,
  LocationOn as LocationIcon
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';

const ObjectGrouper = ({ onObjectsChange, locationHint, setLocationHint }) => {
  const [objects, setObjects] = useState([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingObject, setEditingObject] = useState(null);
  const [objectName, setObjectName] = useState('');
  const [objectDescription, setObjectDescription] = useState('');

  // Создание нового объекта
  const createNewObject = () => {
    setEditingObject(null);
    setObjectName('');
    setObjectDescription('');
    setDialogOpen(true);
  };

  // Редактирование существующего объекта
  const editObject = (objectId) => {
    const obj = objects.find(o => o.id === objectId);
    if (obj) {
      setEditingObject(obj);
      setObjectName(obj.name);
      setObjectDescription(obj.description);
      setDialogOpen(true);
    }
  };

  // Сохранение объекта
  const saveObject = () => {
    if (!objectName.trim()) return;

    const newObject = {
      id: editingObject ? editingObject.id : Date.now(),
      name: objectName.trim(),
      description: objectDescription.trim(),
      files: editingObject ? editingObject.files : [],
      status: 'pending'
    };

    let updatedObjects;
    if (editingObject) {
      updatedObjects = objects.map(obj => 
        obj.id === editingObject.id ? newObject : obj
      );
    } else {
      updatedObjects = [...objects, newObject];
    }

    setObjects(updatedObjects);
    onObjectsChange(updatedObjects);
    setDialogOpen(false);
    setObjectName('');
    setObjectDescription('');
    setEditingObject(null);
  };

  // Удаление объекта
  const deleteObject = (objectId) => {
    const updatedObjects = objects.filter(obj => obj.id !== objectId);
    setObjects(updatedObjects);
    onObjectsChange(updatedObjects);
  };

  // Добавление файлов к объекту
  const addFilesToObject = (objectId, newFiles) => {
    const updatedObjects = objects.map(obj => {
      if (obj.id === objectId) {
        const existingFiles = obj.files || [];
        const filesToAdd = newFiles.filter(newFile => 
          !existingFiles.some(existing => 
            existing.name === newFile.name && existing.size === newFile.size
          )
        );
        
        return {
          ...obj,
          files: [...existingFiles, ...filesToAdd.map(file => ({
            file,
            name: file.name,
            size: file.size,
            type: file.type,
            preview: file.type.startsWith('image/') ? URL.createObjectURL(file) : null
          }))]
        };
      }
      return obj;
    });

    setObjects(updatedObjects);
    onObjectsChange(updatedObjects);
  };

  // Удаление файла из объекта
  const removeFileFromObject = (objectId, fileIndex) => {
    const updatedObjects = objects.map(obj => {
      if (obj.id === objectId) {
        const newFiles = obj.files.filter((_, index) => index !== fileIndex);
        return { ...obj, files: newFiles };
      }
      return obj;
    });

    setObjects(updatedObjects);
    onObjectsChange(updatedObjects);
  };

  // Компонент для загрузки файлов в объект
  const ObjectDropzone = ({ objectId, maxFiles = 10 }) => {
    const currentObject = objects.find(obj => obj.id === objectId);
    const currentFileCount = currentObject?.files?.length || 0;
    const remainingSlots = maxFiles - currentFileCount;

    const onDrop = useCallback((acceptedFiles) => {
      if (remainingSlots > 0) {
        const filesToAdd = acceptedFiles.slice(0, remainingSlots);
        addFilesToObject(objectId, filesToAdd);
      }
    }, [objectId, remainingSlots]);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
      onDrop,
      accept: {
        'image/*': ['.jpeg', '.jpg', '.png', '.gif', '.bmp', '.webp'],
        'video/*': ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']
      },
      maxFiles: remainingSlots,
      disabled: remainingSlots <= 0
    });

    return (
      <Box
        {...getRootProps()}
        sx={{
          border: '2px dashed',
          borderColor: isDragActive ? 'primary.main' : 'grey.300',
          borderRadius: 2,
          p: 2,
          textAlign: 'center',
          cursor: remainingSlots > 0 ? 'pointer' : 'not-allowed',
          bgcolor: isDragActive ? 'action.hover' : 'transparent',
          opacity: remainingSlots > 0 ? 1 : 0.5
        }}
      >
        <input {...getInputProps()} />
        <PhotoLibraryIcon sx={{ fontSize: 48, color: 'grey.400', mb: 1 }} />
        <Typography variant="body2" color="textSecondary">
          {remainingSlots > 0 
            ? `Перетащите файлы сюда или нажмите для выбора (${currentFileCount}/${maxFiles})`
            : `Достигнут лимит файлов (${maxFiles})`
          }
        </Typography>
        <Typography variant="caption" color="textSecondary">
          Поддерживаются изображения и видео
        </Typography>
      </Box>
    );
  };

  return (
    <Box>
      {/* Заголовок и подсказка местоположения */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            📸 Группировка фотографий по объектам
          </Typography>
          <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
            Сгруппируйте фотографии одного объекта (здания, места) для более точного определения координат.
            Можно загрузить 1-10 фото с разных ракурсов.
          </Typography>
          
          <TextField
            fullWidth
            label="Подсказка местоположения (город, район, улица)"
            placeholder="Например: Краснодар, ул. Красная"
            value={locationHint}
            onChange={(e) => setLocationHint(e.target.value)}
            sx={{ mb: 2 }}
            InputProps={{
              startAdornment: <LocationIcon sx={{ mr: 1, color: 'grey.400' }} />
            }}
          />

          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={createNewObject}
            sx={{ mb: 2 }}
          >
            Создать новый объект
          </Button>
        </CardContent>
      </Card>

      {/* Список объектов */}
      {objects.length > 0 && (
        <Box>
          {objects.map((obj) => (
            <Accordion key={obj.id} sx={{ mb: 2 }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                  <Typography variant="h6" sx={{ flexGrow: 1 }}>
                    {obj.name}
                  </Typography>
                  <Chip 
                    label={`${obj.files?.length || 0} файлов`}
                    size="small"
                    color={obj.files?.length > 0 ? 'primary' : 'default'}
                    sx={{ mr: 1 }}
                  />
                  <Chip 
                    label={obj.status === 'pending' ? 'Ожидает' : obj.status}
                    size="small"
                    color={obj.status === 'completed' ? 'success' : 'default'}
                  />
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={2}>
                  <Grid item xs={12}>
                    <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                      <Button
                        size="small"
                        startIcon={<EditIcon />}
                        onClick={() => editObject(obj.id)}
                      >
                        Редактировать
                      </Button>
                      <Button
                        size="small"
                        color="error"
                        startIcon={<DeleteIcon />}
                        onClick={() => deleteObject(obj.id)}
                      >
                        Удалить
                      </Button>
                    </Box>
                  </Grid>

                  <Grid item xs={12}>
                    <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                      {obj.description}
                    </Typography>
                  </Grid>

                  <Grid item xs={12}>
                    <ObjectDropzone objectId={obj.id} />
                  </Grid>

                  {/* Список файлов объекта */}
                  {obj.files && obj.files.length > 0 && (
                    <Grid item xs={12}>
                      <Typography variant="subtitle2" sx={{ mb: 1 }}>
                        Файлы ({obj.files.length}):
                      </Typography>
                      <Grid container spacing={1}>
                        {obj.files.map((fileData, index) => (
                          <Grid item xs={12} sm={6} md={4} key={index}>
                            <Card variant="outlined" sx={{ p: 1 }}>
                              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                {fileData.type.startsWith('image/') ? (
                                  <ImageIcon color="primary" sx={{ mr: 1 }} />
                                ) : (
                                  <VideoIcon color="secondary" sx={{ mr: 1 }} />
                                )}
                                <Box sx={{ flexGrow: 1, minWidth: 0 }}>
                                  <Typography variant="body2" noWrap>
                                    {fileData.name}
                                  </Typography>
                                  <Typography variant="caption" color="textSecondary">
                                    {(fileData.size / 1024 / 1024).toFixed(1)} MB
                                  </Typography>
                                </Box>
                                <IconButton
                                  size="small"
                                  color="error"
                                  onClick={() => removeFileFromObject(obj.id, index)}
                                >
                                  <DeleteIcon />
                                </IconButton>
                              </Box>
                              {fileData.preview && (
                                <Box sx={{ mt: 1 }}>
                                  <img
                                    src={fileData.preview}
                                    alt={fileData.name}
                                    style={{
                                      width: '100%',
                                      height: '80px',
                                      objectFit: 'cover',
                                      borderRadius: '4px'
                                    }}
                                  />
                                </Box>
                              )}
                            </Card>
                          </Grid>
                        ))}
                      </Grid>
                    </Grid>
                  )}
                </Grid>
              </AccordionDetails>
            </Accordion>
          ))}
        </Box>
      )}

      {/* Диалог создания/редактирования объекта */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingObject ? 'Редактировать объект' : 'Создать новый объект'}
        </DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            fullWidth
            label="Название объекта"
            placeholder="Например: Жилой дом на Тополиной"
            value={objectName}
            onChange={(e) => setObjectName(e.target.value)}
            sx={{ mb: 2, mt: 1 }}
          />
          <TextField
            fullWidth
            multiline
            rows={3}
            label="Описание (необязательно)"
            placeholder="Краткое описание объекта, особенности, адрес..."
            value={objectDescription}
            onChange={(e) => setObjectDescription(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>
            Отмена
          </Button>
          <Button 
            onClick={saveObject} 
            variant="contained"
            disabled={!objectName.trim()}
          >
            {editingObject ? 'Сохранить' : 'Создать'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Информационное сообщение */}
      {objects.length === 0 && (
        <Alert severity="info" sx={{ mt: 2 }}>
          <Typography variant="body2">
            Создайте объекты и добавьте к ним фотографии для анализа. 
            Каждый объект может содержать до 10 фотографий с разных ракурсов.
          </Typography>
        </Alert>
      )}
    </Box>
  );
};

export default ObjectGrouper;
