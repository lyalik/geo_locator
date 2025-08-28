import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Box, AppBar, Toolbar, Typography, Button } from '@mui/material';
import { useAuth } from './contexts/AuthContext';
import Dashboard from './components/Dashboard';
import LoginPage from './pages/LoginPage';

function App() {
  const { currentUser, logout } = useAuth();

  if (!currentUser) {
    return <LoginPage />;
  }

  return (
    <Router>
      <Box sx={{ flexGrow: 1 }}>
        <AppBar position="static">
          <Toolbar>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              🏢 Geo Locator - Анализ нарушений
            </Typography>
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
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Box>
    </Router>
  );
}

export default App;
