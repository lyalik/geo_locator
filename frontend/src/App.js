import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { Box, AppBar, Toolbar, Typography, Button, IconButton } from '@mui/material';
import { Notifications as NotificationsIcon } from '@mui/icons-material';
import { useAuth } from './contexts/AuthContext';
import Dashboard from './components/Dashboard';
import NotificationSettings from './components/NotificationSettings';
import LoginPage from './pages/LoginPage';

function AppContent() {
  const { currentUser, logout } = useAuth();
  const navigate = useNavigate();

  if (!currentUser) {
    return <LoginPage />;
  }

  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            🏢 Geo Locator - Анализ нарушений
          </Typography>
          <IconButton 
            color="inherit" 
            onClick={() => navigate('/notifications')}
            sx={{ mr: 1 }}
          >
            <NotificationsIcon />
          </IconButton>
          <Typography variant="body2" sx={{ mr: 2 }}>
            Добро пожаловать, {currentUser.username}
          </Typography>
          <Button color="inherit" onClick={logout}>
            Выйти
          </Button>
        </Toolbar>
      </AppBar>
      
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/notifications" element={<NotificationSettings />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Box>
  );
}

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;
