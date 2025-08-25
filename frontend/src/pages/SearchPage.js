import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { useSnackbar } from 'notistack';
import { 
  Box, 
  Button, 
  Container, 
  Typography, 
  Paper, 
  Tabs, 
  Tab, 
  Grid, 
  CircularProgress,
  TextField,
  Card,
  CardContent,
  CardMedia,
  IconButton,
  Divider,
  Chip,
  Stack,
  LinearProgress,
} from '@mui/material';
import { 
  CloudUpload as CloudUploadIcon, 
  Search as SearchIcon, 
  Close as CloseIcon,
  Panorama as PanoramaIcon,
  Videocam as VideoIcon,
  Image as ImageIcon,
  TextFields as TextIcon,
} from '@mui/icons-material';
import { search } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

const SearchPage = () => {
  const { currentUser } = useAuth();
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const [activeTab, setActiveTab] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState(null);
  const [searchId, setSearchId] = useState(null);
  const [progress, setProgress] = useState(0);
  const progressInterval = useRef(null);

  // Redirect to login if not authenticated
  React.useEffect(() => {
    if (!currentUser) {
      navigate('/login', { state: { from: '/search' } });
    }
  }, [currentUser, navigate]);

  // Handle tab change
  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
    setSearchResults(null);
    setSearchQuery('');
  };

  // Handle search form submission
  const handleSearchSubmit = async (e) => {
    e.preventDefault();
    
    if (!searchQuery.trim()) {
      enqueueSnackbar('Please enter a search query', { variant: 'warning' });
      return;
    }

    try {
      setIsSearching(true);
      setProgress(0);
      
      // Simulate progress
      progressInterval.current = setInterval(() => {
        setProgress((prevProgress) => {
          if (prevProgress >= 90) {
            clearInterval(progressInterval.current);
            return 90;
          }
          return prevProgress + 10;
        });
      }, 500);

      // Call the appropriate search API based on the active tab
      let response;
      switch (activeTab) {
        case 0: // Text search
          response = await search.byText(searchQuery);
          break;
        case 1: // Image search
          // This will be handled by the dropzone
          return;
        case 2: // Video search
          // This will be handled by the dropzone
          return;
        case 3: // Panorama search
          // This will be handled by the dropzone
          return;
        default:
          throw new Error('Invalid search type');
      }

      handleSearchResponse(response);
    } catch (error) {
      console.error('Search error:', error);
      enqueueSnackbar('Error performing search', { variant: 'error' });
      setIsSearching(false);
      clearInterval(progressInterval.current);
    }
  };

  // Handle search response
  const handleSearchResponse = (response) => {
    clearInterval(progressInterval.current);
    setProgress(100);
    
    setTimeout(() => {
      setSearchResults(response.data);
      setSearchId(response.data.request_id);
      setIsSearching(false);
      setProgress(0);
    }, 500);
  };

  // Handle file upload
  const onDrop = async (acceptedFiles) => {
    if (acceptedFiles.length === 0) return;
    
    const file = acceptedFiles[0];
    const fileType = file.type.split('/')[0];
    
    try {
      setIsSearching(true);
      setProgress(0);
      
      // Simulate progress
      progressInterval.current = setInterval(() => {
        setProgress((prevProgress) => {
          if (prevProgress >= 90) {
            clearInterval(progressInterval.current);
            return 90;
          }
          return prevProgress + 10;
        });
      }, 500);

      let response;
      
      // Call the appropriate API based on file type
      if (fileType === 'image') {
        if (activeTab === 3) { // Panorama tab
          response = await search.byPanorama(file);
        } else { // Image tab
          response = await search.byImage(file);
        }
      } else if (fileType === 'video') {
        response = await search.byVideo(file);
      } else {
        throw new Error('Unsupported file type');
      }
      
      handleSearchResponse(response);
    } catch (error) {
      console.error('File upload error:', error);
      enqueueSnackbar('Error uploading file', { variant: 'error' });
      setIsSearching(false);
      clearInterval(progressInterval.current);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.gif'],
      'video/*': ['.mp4', '.mov', '.avi']
    },
    multiple: false,
  });

  // Get tab icon based on index
  const getTabIcon = (index) => {
    switch (index) {
      case 0: return <TextIcon />;
      case 1: return <ImageIcon />;
      case 2: return <VideoIcon />;
      case 3: return <PanoramaIcon />;
      default: return null;
    }
  };

  // Get tab label based on index
  const getTabLabel = (index) => {
    switch (index) {
      case 0: return 'Text Search';
      case 1: return 'Image Search';
      case 2: return 'Video Search';
      case 3: return 'Panorama Search';
      default: return '';
    }
  };

  // Render search form based on active tab
  const renderSearchForm = () => {
    switch (activeTab) {
      case 0: // Text search
        return (
          <Box component="form" onSubmit={handleSearchSubmit} sx={{ mt: 2 }}>
            <TextField
              fullWidth
              variant="outlined"
              placeholder="Enter location, landmark, or address..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              InputProps={{
                startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                sx: { borderRadius: 2 },
              }}
              disabled={isSearching}
            />
            <Button
              type="submit"
              variant="contained"
              color="primary"
              size="large"
              fullWidth
              sx={{ mt: 2, py: 1.5, borderRadius: 2 }}
              disabled={isSearching || !searchQuery.trim()}
            >
              {isSearching ? 'Searching...' : 'Search'}
            </Button>
          </Box>
        );
      
      case 1: // Image search
      case 2: // Video search
      case 3: // Panorama search
        return (
          <Box 
            {...getRootProps()} 
            sx={{
              border: '2px dashed',
              borderColor: 'divider',
              borderRadius: 2,
              p: 4,
              mt: 2,
              textAlign: 'center',
              cursor: 'pointer',
              backgroundColor: isDragActive ? 'action.hover' : 'background.paper',
              transition: 'background-color 0.2s ease-in-out',
              '&:hover': {
                backgroundColor: 'action.hover',
              },
            }}
          >
            <input {...getInputProps()} />
            <CloudUploadIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              {isDragActive 
                ? 'Drop the file here' 
                : `Drag and drop a ${activeTab === 1 ? 'photo' : activeTab === 2 ? 'video' : 'panorama image'} here, or click to select`}
            </Typography>
            <Typography variant="body2" color="textSecondary">
              {activeTab === 1 
                ? 'Supports JPG, JPEG, PNG' 
                : activeTab === 2 
                  ? 'Supports MP4, MOV, AVI' 
                  : 'Supports 360° panoramic images'}
            </Typography>
          </Box>
        );
      
      default:
        return null;
    }
  };

  // Render search results
  const renderSearchResults = () => {
    if (!searchResults) return null;

    return (
      <Box sx={{ mt: 4 }}>
        <Typography variant="h5" gutterBottom>
          Search Results
        </Typography>
        
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom>
                  Yandex Maps
                </Typography>
                {searchResults.yandex ? (
                  <>
                    <Typography variant="body1" gutterBottom>
                      {searchResults.yandex.address || 'No address available'}
                    </Typography>
                    <Chip 
                      label={`Confidence: ${searchResults.yandex.confidence || 'N/A'}%`} 
                      color="primary" 
                      size="small" 
                      sx={{ mb: 1 }}
                    />
                  </>
                ) : (
                  <Typography color="textSecondary">No data available</Typography>
                )}
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom>
                  2GIS
                </Typography>
                {searchResults.dgis ? (
                  <>
                    <Typography variant="body1" gutterBottom>
                      {searchResults.dgis.address || 'No address available'}
                    </Typography>
                    <Chip 
                      label={`Confidence: ${searchResults.dgis.confidence || 'N/A'}%`} 
                      color="secondary" 
                      size="small" 
                      sx={{ mb: 1 }}
                    />
                  </>
                ) : (
                  <Typography color="textSecondary">No data available</Typography>
                )}
              </Grid>
              
              {searchResults.sentinel && (
                <Grid item xs={12}>
                  <Typography variant="h6" gutterBottom>
                    Satellite Analysis
                  </Typography>
                  <Typography variant="body1">
                    {searchResults.sentinel.analysis || 'No analysis available'}
                  </Typography>
                </Grid>
              )}
              
              {searchResults.gemini_analysis && (
                <Grid item xs={12}>
                  <Typography variant="h6" gutterBottom>
                    AI Analysis
                  </Typography>
                  <Typography variant="body1">
                    {searchResults.gemini_analysis}
                  </Typography>
                </Grid>
              )}
            </Grid>
          </CardContent>
        </Card>
        
        <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between' }}>
          <Button 
            variant="outlined" 
            onClick={() => setSearchResults(null)}
            startIcon={<CloseIcon />}
          >
            Clear Results
          </Button>
          
          <Button 
            variant="contained" 
            color="primary"
            onClick={() => {
              // TODO: Implement save to history
              enqueueSnackbar('Search saved to history', { variant: 'success' });
            }}
          >
            Save to History
          </Button>
        </Box>
      </Box>
    );
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Search Locations
      </Typography>
      
      <Paper sx={{ mb: 4 }}>
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          variant="scrollable"
          scrollButtons="auto"
          aria-label="search tabs"
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          {[0, 1, 2, 3].map((index) => (
            <Tab 
              key={index} 
              icon={getTabIcon(index)} 
              label={getTabLabel(index)} 
              disabled={isSearching}
            />
          ))}
        </Tabs>
        
        <Box sx={{ p: 3 }}>
          {isSearching && (
            <Box sx={{ width: '100%', mb: 2 }}>
              <LinearProgress 
                variant={progress === 100 ? 'indeterminate' : 'determinate'} 
                value={progress} 
                sx={{ height: 8, borderRadius: 4 }}
              />
              <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
                {progress < 100 ? 'Processing your request...' : 'Finalizing results...'}
              </Typography>
            </Box>
          )}
          
          {!isSearching && renderSearchForm()}
          
          {searchResults && renderSearchResults()}
        </Box>
      </Paper>
      
      {/* Map comparison section */}
      {searchResults && (
        <Box sx={{ mt: 4 }}>
          <Typography variant="h5" gutterBottom>
            Map Comparison
          </Typography>
          
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 2, height: '400px', overflow: 'hidden' }}>
                <Typography variant="subtitle1" gutterBottom>
                  Yandex Maps
                </Typography>
                <Box 
                  component="iframe"
                  src={`https://yandex.ru/map-widget/v1/?ll=${searchResults.longitude || 37.6173},${searchResults.latitude || 55.7558}&z=15`}
                  width="100%" 
                  height="350" 
                  frameBorder="0"
                  allowFullScreen={true}
                  style={{ border: 'none', borderRadius: '8px' }}
                  title="Yandex Map"
                />
              </Paper>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 2, height: '400px', overflow: 'hidden' }}>
                <Typography variant="subtitle1" gutterBottom>
                  2GIS
                </Typography>
                <Box 
                  component="iframe"
                  src={`https://widgets.2gis.com/widget?type=firmsonmap&options=${encodeURIComponent(JSON.stringify({
                    zoom: 15,
                    lat: searchResults.latitude || 55.7558,
                    lon: searchResults.longitude || 37.6173,
                    searchText: searchResults.yandex?.address || '',
                  }))}`}
                  width="100%" 
                  height="350" 
                  frameBorder="0"
                  allowFullScreen={true}
                  style={{ border: 'none', borderRadius: '8px' }}
                  title="2GIS Map"
                />
              </Paper>
            </Grid>
          </Grid>
        </Box>
      )}
    </Container>
  );
};

export default SearchPage;
