import React, { useState } from 'react';
import { TextField, Button, Box, Typography } from '@mui/material';
import { useNavigate } from 'react-router-dom';

const Register = () => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  const handleRegister = async () => {
    try {
      // УМНОЕ определение API URL
      const hostname = window.location.hostname;
      const apiUrl = (hostname === '192.168.1.67' || hostname === 'localhost' || hostname === '127.0.0.1')
        ? 'http://192.168.1.67:5001'  // Локальная сеть - прямое обращение
        : '';  // Внешний доступ - через nginx
      console.log(`📝 Register API URL: ${apiUrl || 'nginx proxy'}`);
      
      const response = await fetch(`${apiUrl}/auth/register`, {
        method: 'POST',
        credentials: 'include', // Важно для сессионной авторизации
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, email, password }),
      });
      const data = await response.json();
      if (response.ok) {
        // Handle successful registration
        navigate('/login');
      } else {
        alert(data.message);
      }
    } catch (error) {
      console.error('Error registering:', error);
    }
  };

  return (
    <Box sx={{ maxWidth: 400, mx: 'auto', mt: 10 }}>
      <Typography variant="h4" gutterBottom>
        Register
      </Typography>
      <TextField
        label="Username"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        fullWidth
        margin="normal"
      />
      <TextField
        label="Email"
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        fullWidth
        margin="normal"
      />
      <TextField
        label="Password"
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        fullWidth
        margin="normal"
      />
      <Button variant="contained" color="primary" onClick={handleRegister} fullWidth>
        Register
      </Button>
    </Box>
  );
};

export default Register;
