import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Switch,
  FormControlLabel,
  FormGroup,
  Button,
  Alert,
  Snackbar,
  Divider,
  Grid,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip
} from '@mui/material';
import {
  Notifications as NotificationsIcon,
  Email as EmailIcon,
  Sms as SmsIcon,
  Security as SecurityIcon,
  Schedule as ScheduleIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon
} from '@mui/icons-material';
import { api } from '../services/api';

const NotificationSettings = () => {
  const [preferences, setPreferences] = useState({
    email_notifications: true,
    sms_notifications: false,
    push_notifications: true,
    violation_alerts: true,
    weekly_reports: true,
    immediate_alerts: true
  });
  
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });

  useEffect(() => {
    loadPreferences();
    loadNotifications();
  }, []);

  const loadPreferences = async () => {
    try {
      const response = await api.get('/api/notifications/preferences');
      setPreferences(response.data);
    } catch (error) {
      console.error('Failed to load preferences:', error);
      showSnackbar('Ошибка загрузки настроек', 'error');
    } finally {
      setLoading(false);
    }
  };

  const loadNotifications = async () => {
    try {
      const response = await api.get('/api/notifications');
      setNotifications(response.data.notifications || []);
    } catch (error) {
      console.error('Failed to load notifications:', error);
    }
  };

  const savePreferences = async () => {
    setSaving(true);
    try {
      await api.put('/api/notifications/preferences', preferences);
      showSnackbar('Настройки сохранены', 'success');
    } catch (error) {
      console.error('Failed to save preferences:', error);
      showSnackbar('Ошибка сохранения настроек', 'error');
    } finally {
      setSaving(false);
    }
  };

  const sendTestEmail = async () => {
    try {
      await api.post('/api/notifications/test-email');
      showSnackbar('Тестовое письмо отправлено', 'success');
    } catch (error) {
      console.error('Failed to send test email:', error);
      showSnackbar('Ошибка отправки тестового письма', 'error');
    }
  };

  const sendWeeklyReport = async () => {
    try {
      await api.post('/api/notifications/weekly-report');
      showSnackbar('Еженедельный отчет отправлен', 'success');
      loadNotifications(); // Refresh notifications list
    } catch (error) {
      console.error('Failed to send weekly report:', error);
      showSnackbar('Ошибка отправки отчета', 'error');
    }
  };

  const markAsRead = async (notificationId) => {
    try {
      await api.put(`/api/notifications/${notificationId}/read`);
      loadNotifications(); // Refresh notifications list
    } catch (error) {
      console.error('Failed to mark as read:', error);
    }
  };

  const showSnackbar = (message, severity) => {
    setSnackbar({ open: true, message, severity });
  };

  const handlePreferenceChange = (key) => (event) => {
    setPreferences(prev => ({
      ...prev,
      [key]: event.target.checked
    }));
  };

  const getNotificationIcon = (type) => {
    switch (type) {
      case 'email': return <EmailIcon />;
      case 'sms': return <SmsIcon />;
      default: return <NotificationsIcon />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'sent': return 'success';
      case 'failed': return 'error';
      case 'read': return 'default';
      default: return 'warning';
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <Typography>Загрузка настроек...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 1200, margin: '0 auto', padding: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <NotificationsIcon />
        Настройки уведомлений
      </Typography>

      <Grid container spacing={3}>
        {/* Настройки уведомлений */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <SecurityIcon />
                Типы уведомлений
              </Typography>
              
              <FormGroup>
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferences.violation_alerts}
                      onChange={handlePreferenceChange('violation_alerts')}
                    />
                  }
                  label="Уведомления о нарушениях"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferences.weekly_reports}
                      onChange={handlePreferenceChange('weekly_reports')}
                    />
                  }
                  label="Еженедельные отчеты"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferences.immediate_alerts}
                      onChange={handlePreferenceChange('immediate_alerts')}
                    />
                  }
                  label="Мгновенные уведомления"
                />
              </FormGroup>

              <Divider sx={{ my: 2 }} />

              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <ScheduleIcon />
                Способы доставки
              </Typography>

              <FormGroup>
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferences.email_notifications}
                      onChange={handlePreferenceChange('email_notifications')}
                    />
                  }
                  label="Email уведомления"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferences.sms_notifications}
                      onChange={handlePreferenceChange('sms_notifications')}
                      disabled
                    />
                  }
                  label="SMS уведомления (скоро)"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferences.push_notifications}
                      onChange={handlePreferenceChange('push_notifications')}
                      disabled
                    />
                  }
                  label="Push уведомления (скоро)"
                />
              </FormGroup>

              <Box sx={{ mt: 3, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                <Button
                  variant="contained"
                  onClick={savePreferences}
                  disabled={saving}
                >
                  {saving ? 'Сохранение...' : 'Сохранить настройки'}
                </Button>
                <Button
                  variant="outlined"
                  onClick={sendTestEmail}
                  disabled={!preferences.email_notifications}
                >
                  Тестовое письмо
                </Button>
                <Button
                  variant="outlined"
                  onClick={sendWeeklyReport}
                  disabled={!preferences.weekly_reports}
                >
                  Отправить отчет
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* История уведомлений */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                История уведомлений
              </Typography>
              
              {notifications.length === 0 ? (
                <Typography color="text.secondary">
                  Уведомлений пока нет
                </Typography>
              ) : (
                <List>
                  {notifications.slice(0, 10).map((notification) => (
                    <ListItem
                      key={notification.id}
                      sx={{
                        border: 1,
                        borderColor: 'divider',
                        borderRadius: 1,
                        mb: 1,
                        cursor: notification.status === 'pending' ? 'pointer' : 'default'
                      }}
                      onClick={() => {
                        if (notification.status === 'pending') {
                          markAsRead(notification.id);
                        }
                      }}
                    >
                      <ListItemIcon>
                        {getNotificationIcon(notification.type)}
                      </ListItemIcon>
                      <ListItemText
                        primary={notification.subject || 'Уведомление'}
                        secondary={
                          <Box>
                            <Typography variant="body2" color="text.secondary">
                              {notification.message}
                            </Typography>
                            <Box sx={{ mt: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Chip
                                size="small"
                                label={notification.status}
                                color={getStatusColor(notification.status)}
                              />
                              <Typography variant="caption" color="text.secondary">
                                {new Date(notification.created_at).toLocaleString('ru-RU')}
                              </Typography>
                            </Box>
                          </Box>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default NotificationSettings;
