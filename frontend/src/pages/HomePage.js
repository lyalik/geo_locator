import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Box, Button, Container, Typography, Grid, Card, CardContent, CardActions, CardMedia } from '@mui/material';
import { styled } from '@mui/material/styles';
import SearchIcon from '@mui/icons-material/Search';
import HistoryIcon from '@mui/icons-material/History';
import LocationOnIcon from '@mui/icons-material/LocationOn';

const StyledCard = styled(Card)(({ theme }) => ({
  height: '100%',
  display: 'flex',
  flexDirection: 'column',
  transition: 'transform 0.3s ease-in-out',
  '&:hover': {
    transform: 'translateY(-5px)',
    boxShadow: theme.shadows[8],
  },
}));

const FeatureCard = ({ icon, title, description, buttonText, onClick }) => (
  <StyledCard>
    <CardContent sx={{ flexGrow: 1 }}>
      <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
        {icon}
      </Box>
      <Typography gutterBottom variant="h5" component="h2" align="center">
        {title}
      </Typography>
      <Typography color="textSecondary" align="center">
        {description}
      </Typography>
    </CardContent>
    <CardActions sx={{ justifyContent: 'center', pb: 2 }}>
      <Button size="small" color="primary" onClick={onClick}>
        {buttonText}
      </Button>
    </CardActions>
  </StyledCard>
);

const HomePage = () => {
  const { currentUser } = useAuth();
  const navigate = useNavigate();

  const handleSearchClick = () => {
    if (currentUser) {
      navigate('/search');
    } else {
      navigate('/login', { state: { from: '/search' } });
    }
  };

  const handleHistoryClick = () => {
    if (currentUser) {
      navigate('/history');
    } else {
      navigate('/login', { state: { from: '/history' } });
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box textAlign="center" mb={6}>
        <Typography variant="h3" component="h1" gutterBottom>
          Geo Locator
        </Typography>
        <Typography variant="h6" color="textSecondary" paragraph>
          Find and compare locations using multiple mapping services
        </Typography>
      </Box>

      <Grid container spacing={4}>
        <Grid item xs={12} md={4}>
          <FeatureCard
            icon={<SearchIcon sx={{ fontSize: 60, color: 'primary.main' }} />}
            title="Search Locations"
            description="Search for locations using text, images, videos, or panoramic views"
            buttonText={currentUser ? "Start Searching" : "Sign In to Search"}
            onClick={handleSearchClick}
          />
        </Grid>
        <Grid item xs={12} md={4}>
          <FeatureCard
            icon={<HistoryIcon sx={{ fontSize: 60, color: 'secondary.main' }} />}
            title="View History"
            description="Access your search history and previous results"
            buttonText={currentUser ? "View History" : "Sign In to View History"}
            onClick={handleHistoryClick}
          />
        </Grid>
        <Grid item xs={12} md={4}>
          <FeatureCard
            icon={<LocationOnIcon sx={{ fontSize: 60, color: 'success.main' }} />}
            title="Compare Maps"
            description="Compare results from different mapping services"
            buttonText="Learn More"
            onClick={() => {}}
          />
        </Grid>
      </Grid>

      <Box mt={8} textAlign="center">
        <Typography variant="h5" gutterBottom>
          How It Works
        </Typography>
        <Grid container spacing={4} mt={2}>
          <Grid item xs={12} md={4}>
            <Typography variant="h6">1. Upload or Search</Typography>
            <Typography>
              Upload an image, video, or enter a location to start your search.
            </Typography>
          </Grid>
          <Grid item xs={12} md={4}>
            <Typography variant="h6">2. Analyze</Typography>
            <Typography>
              Our system processes your input using advanced algorithms and multiple data sources.
            </Typography>
          </Grid>
          <Grid item xs={12} md={4}>
            <Typography variant="h6">3. Get Results</Typography>
            <Typography>
              View and compare results from different mapping services in one place.
            </Typography>
          </Grid>
        </Grid>
      </Box>
    </Container>
  );
};

export default HomePage;
