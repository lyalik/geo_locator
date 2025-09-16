import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Tabs,
  Tab,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  Grid,
  FormControl,
  InputLabel,
  MenuItem,
  Chip,
  IconButton,
  Alert,
  Card,
  CardContent,
  Pagination
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  Block as BlockIcon,
  CheckCircle as ApproveIcon,
  Person as PersonIcon,
  Report as ReportIcon,
  Analytics as AnalyticsIcon
} from '@mui/icons-material';
import { api } from '../services/api';

function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`admin-tabpanel-${index}`}
      aria-labelledby={`admin-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export default function AdminPanel() {
  const [tabValue, setTabValue] = useState(0);
  const [users, setUsers] = useState([]);
  const [violations, setViolations] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [violationFilters, setViolationFilters] = useState({
    status: '',
    category: '',
    user_id: '',
    date_from: '',
    date_to: ''
  });
  const [analyticsFilters, setAnalyticsFilters] = useState({
    period: '30',
    category: '',
    user_id: ''
  });
  const [loading, setLoading] = useState(false);
  const [editDialog, setEditDialog] = useState({ open: false, type: null, data: null });
  const [deleteDialog, setDeleteDialog] = useState({ open: false, type: null, id: null });
  const [alert, setAlert] = useState({ open: false, message: '', severity: 'info' });
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => {
    loadData();
  }, [tabValue, page]);

  const loadData = async () => {
    setLoading(true);
    try {
      switch (tabValue) {
        case 0: // Пользователи
          await loadUsers();
          break;
        case 1: // Нарушения
          await loadViolations();
          break;
        case 2: // Аналитика
          await loadAnalytics();
          break;
      }
    } catch (error) {
      showAlert('Ошибка загрузки данных', 'error');
    } finally {
      setLoading(false);
    }
  };

  const loadUsers = async () => {
    try {
      const response = await api.get('/admin/users', {
        params: { page, per_page: 20 }
      });
      setUsers(response.data.users || []);
      setTotalPages(Math.ceil((response.data.total || 0) / 20));
    } catch (error) {
      console.error('Ошибка загрузки пользователей:', error);
    }
  };

  const loadViolations = async () => {
    try {
      const params = { page, per_page: 20 };
      
      // Добавляем фильтры если они установлены
      if (violationFilters.status) params.status = violationFilters.status;
      if (violationFilters.category) params.category = violationFilters.category;
      if (violationFilters.user_id) params.user_id = violationFilters.user_id;
      if (violationFilters.date_from) params.date_from = violationFilters.date_from;
      if (violationFilters.date_to) params.date_to = violationFilters.date_to;
      
      const response = await api.get('/admin/violations', { params });
      setViolations(response.data.violations || []);
      setTotalPages(Math.ceil((response.data.total || 0) / 20));
    } catch (error) {
      console.error('Ошибка загрузки нарушений:', error);
    }
  };

  const loadAnalytics = async () => {
    try {
      const params = {};
      
      // Добавляем фильтры аналитики
      if (analyticsFilters.period) params.period = analyticsFilters.period;
      if (analyticsFilters.category) params.category = analyticsFilters.category;
      if (analyticsFilters.user_id) params.user_id = analyticsFilters.user_id;
      
      const response = await api.get('/admin/analytics/detailed', { params });
      setAnalytics(response.data.data || response.data);
    } catch (error) {
      console.error('Ошибка загрузки аналитики:', error);
    }
  };

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
    setPage(1);
  };

  const handleEdit = (type, data) => {
    setEditDialog({ open: true, type, data: { ...data } });
  };

  const handleDelete = (type, id) => {
    setDeleteDialog({ open: true, type, id });
  };

  const handleSaveEdit = async () => {
    try {
      const { type, data } = editDialog;
      
      if (type === 'user') {
        await api.put(`/admin/users/${data.id}`, {
          username: data.username,
          email: data.email,
          role: data.role,
          is_active: data.is_active
        });
        await loadUsers();
        showAlert('Пользователь обновлен', 'success');
      } else if (type === 'violation') {
        await api.put(`/api/violations/details/${data.id}`, {
          category: data.category,
          status: data.status,
          notes: data.notes
        });
        await loadViolations();
        showAlert('Нарушение обновлено', 'success');
      }
      
      setEditDialog({ open: false, type: null, data: null });
    } catch (error) {
      showAlert('Ошибка сохранения', 'error');
    }
  };

  const handleConfirmDelete = async () => {
    try {
      const { type, id } = deleteDialog;
      
      if (type === 'user') {
        await api.delete(`/admin/users/${id}`);
        await loadUsers();
        showAlert('Пользователь удален', 'success');
      } else if (type === 'violation') {
        await api.delete(`/api/violations/${id}`);
        await loadViolations();
        showAlert('Нарушение удалено', 'success');
      }
      
      setDeleteDialog({ open: false, type: null, id: null });
    } catch (error) {
      showAlert('Ошибка удаления', 'error');
    }
  };

  const handleModerateViolation = async (violationId, action) => {
    try {
      const status = action === 'approve' ? 'approved' : 'rejected';
      await api.put(`/api/violations/details/${violationId}`, { status });
      await loadViolations();
      showAlert(`Нарушение ${action === 'approve' ? 'одобрено' : 'отклонено'}`, 'success');
    } catch (error) {
      showAlert('Ошибка модерации', 'error');
    }
  };

  const showAlert = (message, severity = 'info') => {
    setAlert({ open: true, message, severity });
    setTimeout(() => setAlert({ open: false, message: '', severity: 'info' }), 3000);
  };

  const getStatusColor = (status) => {
    const colors = {
      active: 'error',
      resolved: 'success',
      pending: 'warning',
      approved: 'success',
      rejected: 'error',
      deleted: 'default'
    };
    return colors[status] || 'default';
  };

  const getRoleColor = (role) => {
    const colors = {
      admin: 'error',
      moderator: 'warning',
      user: 'primary'
    };
    return colors[role] || 'default';
  };

  return (
    <Box sx={{ width: '100%', bgcolor: 'background.paper' }}>
      {alert.open && (
        <Alert severity={alert.severity} sx={{ mb: 2 }}>
          {alert.message}
        </Alert>
      )}

      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab icon={<PersonIcon />} label="Пользователи" />
          <Tab icon={<ReportIcon />} label="Нарушения" />
          <Tab icon={<AnalyticsIcon />} label="Аналитика" />
        </Tabs>
      </Box>

      {/* Панель пользователей */}
      <TabPanel value={tabValue} index={0}>
        <Typography variant="h5" gutterBottom>
          Управление пользователями
        </Typography>
        
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>ID</TableCell>
                <TableCell>Имя пользователя</TableCell>
                <TableCell>Email</TableCell>
                <TableCell>Роль</TableCell>
                <TableCell>Статус</TableCell>
                <TableCell>Дата регистрации</TableCell>
                <TableCell>Действия</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {users.map((user) => (
                <TableRow key={user.id}>
                  <TableCell>{user.id}</TableCell>
                  <TableCell>{user.username}</TableCell>
                  <TableCell>{user.email}</TableCell>
                  <TableCell>
                    <Chip 
                      label={user.role || 'user'} 
                      color={getRoleColor(user.role)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Chip 
                      label={user.is_active ? 'Активен' : 'Заблокирован'} 
                      color={user.is_active ? 'success' : 'error'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    {new Date(user.created_at).toLocaleDateString('ru-RU')}
                  </TableCell>
                  <TableCell>
                    <IconButton 
                      onClick={() => handleEdit('user', user)}
                      color="primary"
                      size="small"
                    >
                      <EditIcon />
                    </IconButton>
                    <IconButton 
                      onClick={() => handleDelete('user', user.id)}
                      color="error"
                      size="small"
                    >
                      <DeleteIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>

        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
          <Pagination 
            count={totalPages} 
            page={page} 
            onChange={(e, value) => setPage(value)}
            color="primary"
          />
        </Box>
      </TabPanel>

      {/* Панель нарушений */}
      <TabPanel value={tabValue} index={1}>
        <Typography variant="h5" gutterBottom>
          Управление нарушениями
        </Typography>
        
        {/* Фильтры нарушений */}
        <Paper sx={{ p: 2, mb: 3 }}>
          <Typography variant="h6" gutterBottom>Фильтры</Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={2}>
              <FormControl fullWidth size="small">
                <InputLabel>Статус</InputLabel>
                <Select
                  value={violationFilters.status}
                  onChange={(e) => setViolationFilters({...violationFilters, status: e.target.value})}
                  label="Статус"
                >
                  <MenuItem value="">Все</MenuItem>
                  <MenuItem value="pending">В ожидании</MenuItem>
                  <MenuItem value="approved">Одобрено</MenuItem>
                  <MenuItem value="rejected">Отклонено</MenuItem>
                  <MenuItem value="resolved">Решено</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={2}>
              <FormControl fullWidth size="small">
                <InputLabel>Категория</InputLabel>
                <Select
                  value={violationFilters.category}
                  onChange={(e) => setViolationFilters({...violationFilters, category: e.target.value})}
                  label="Категория"
                >
                  <MenuItem value="">Все</MenuItem>
                  <MenuItem value="parking_violation">Парковка</MenuItem>
                  <MenuItem value="traffic_violation">ПДД</MenuItem>
                  <MenuItem value="building_violation">Строительство</MenuItem>
                  <MenuItem value="environmental">Экология</MenuItem>
                  <MenuItem value="unauthorized_modification">Несанкционированные изменения</MenuItem>
                  <MenuItem value="unauthorized_signage">Несанкционированные вывески</MenuItem>
                  <MenuItem value="blocked_entrance">Заблокированный вход</MenuItem>
                  <MenuItem value="improper_waste_disposal">Неправильная утилизация</MenuItem>
                  <MenuItem value="structural_damage">Структурные повреждения</MenuItem>
                  <MenuItem value="unsafe_conditions">Небезопасные условия</MenuItem>
                  <MenuItem value="other">Другое</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={2}>
              <TextField
                fullWidth
                size="small"
                label="ID пользователя"
                value={violationFilters.user_id}
                onChange={(e) => setViolationFilters({...violationFilters, user_id: e.target.value})}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={2}>
              <TextField
                fullWidth
                size="small"
                label="Дата от"
                type="date"
                value={violationFilters.date_from}
                onChange={(e) => setViolationFilters({...violationFilters, date_from: e.target.value})}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={2}>
              <TextField
                fullWidth
                size="small"
                label="Дата до"
                type="date"
                value={violationFilters.date_to}
                onChange={(e) => setViolationFilters({...violationFilters, date_to: e.target.value})}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={2}>
              <Button
                fullWidth
                variant="contained"
                onClick={() => {
                  setPage(1);
                  loadViolations();
                }}
                sx={{ height: '40px' }}
              >
                Применить
              </Button>
            </Grid>
          </Grid>
        </Paper>
        
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>ID</TableCell>
                <TableCell>Категория</TableCell>
                <TableCell>Пользователь</TableCell>
                <TableCell>Статус</TableCell>
                <TableCell>Уверенность</TableCell>
                <TableCell>Дата</TableCell>
                <TableCell>Действия</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {violations.map((violation) => (
                <TableRow key={violation.violation_id}>
                  <TableCell>{violation.violation_id}</TableCell>
                  <TableCell>{violation.category}</TableCell>
                  <TableCell>{violation.user_id}</TableCell>
                  <TableCell>
                    <Chip 
                      label={violation.status || 'pending'} 
                      color={getStatusColor(violation.status)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    {Math.round((violation.confidence || 0) * 100)}%
                  </TableCell>
                  <TableCell>
                    {new Date(violation.created_at).toLocaleDateString('ru-RU')}
                  </TableCell>
                  <TableCell>
                    <IconButton 
                      onClick={() => handleEdit('violation', violation)}
                      color="primary"
                      size="small"
                    >
                      <EditIcon />
                    </IconButton>
                    <IconButton 
                      onClick={() => handleModerateViolation(violation.violation_id, 'approve')}
                      color="success"
                      size="small"
                    >
                      <ApproveIcon />
                    </IconButton>
                    <IconButton 
                      onClick={() => handleModerateViolation(violation.violation_id, 'reject')}
                      color="warning"
                      size="small"
                    >
                      <BlockIcon />
                    </IconButton>
                    <IconButton 
                      onClick={() => handleDelete('violation', violation.violation_id)}
                      color="error"
                      size="small"
                    >
                      <DeleteIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>

        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
          <Pagination 
            count={totalPages} 
            page={page} 
            onChange={(e, value) => setPage(value)}
            color="primary"
          />
        </Box>
      </TabPanel>

      {/* Панель аналитики */}
      <TabPanel value={tabValue} index={2}>
        <Typography variant="h5" gutterBottom>
          Системная аналитика
        </Typography>
        
        {/* Фильтры аналитики */}
        <Paper sx={{ p: 2, mb: 3 }}>
          <Typography variant="h6" gutterBottom>Фильтры</Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={4} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel>Период</InputLabel>
                <Select
                  value={analyticsFilters.period}
                  onChange={(e) => setAnalyticsFilters({...analyticsFilters, period: e.target.value})}
                  label="Период"
                >
                  <MenuItem value="7">7 дней</MenuItem>
                  <MenuItem value="30">30 дней</MenuItem>
                  <MenuItem value="90">90 дней</MenuItem>
                  <MenuItem value="365">1 год</MenuItem>
                  <MenuItem value="all">Все время</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={4} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel>Категория</InputLabel>
                <Select
                  value={analyticsFilters.category}
                  onChange={(e) => setAnalyticsFilters({...analyticsFilters, category: e.target.value})}
                  label="Категория"
                >
                  <MenuItem value="">Все</MenuItem>
                  <MenuItem value="parking_violation">Парковка</MenuItem>
                  <MenuItem value="traffic_violation">ПДД</MenuItem>
                  <MenuItem value="building_violation">Строительство</MenuItem>
                  <MenuItem value="environmental">Экология</MenuItem>
                  <MenuItem value="other">Другое</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={4} md={3}>
              <TextField
                fullWidth
                size="small"
                label="ID пользователя"
                value={analyticsFilters.user_id}
                onChange={(e) => setAnalyticsFilters({...analyticsFilters, user_id: e.target.value})}
              />
            </Grid>
            <Grid item xs={12} sm={4} md={3}>
              <Button
                fullWidth
                variant="contained"
                onClick={loadAnalytics}
                sx={{ height: '40px' }}
              >
                Обновить
              </Button>
            </Grid>
          </Grid>
        </Paper>
        
        {analytics && (
          <Grid container spacing={3}>
            <Grid item xs={12} md={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Всего нарушений
                  </Typography>
                  <Typography variant="h4">
                    {analytics.summary?.total_violations || 0}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Всего фотографий
                  </Typography>
                  <Typography variant="h4">
                    {analytics.summary?.total_photos || 0}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Средняя уверенность
                  </Typography>
                  <Typography variant="h4">
                    {Math.round((analytics.summary?.avg_confidence || 0) * 100)}%
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Недавние нарушения
                  </Typography>
                  <Typography variant="h4">
                    {analytics.summary?.recent_violations || 0}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}
      </TabPanel>

      {/* Диалог редактирования */}
      <Dialog 
        open={editDialog.open} 
        onClose={() => setEditDialog({ open: false, type: null, data: null })}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          Редактировать {editDialog.type === 'user' ? 'пользователя' : 'нарушение'}
        </DialogTitle>
        <DialogContent>
          {editDialog.type === 'user' && editDialog.data && (
            <>
              <TextField
                fullWidth
                label="Имя пользователя"
                value={editDialog.data.username || ''}
                onChange={(e) => setEditDialog({
                  ...editDialog,
                  data: { ...editDialog.data, username: e.target.value }
                })}
                margin="normal"
              />
              <TextField
                fullWidth
                label="Email"
                value={editDialog.data.email || ''}
                onChange={(e) => setEditDialog({
                  ...editDialog,
                  data: { ...editDialog.data, email: e.target.value }
                })}
                margin="normal"
              />
              <FormControl fullWidth margin="normal">
                <InputLabel>Роль</InputLabel>
                <Select
                  value={editDialog.data.role || 'user'}
                  onChange={(e) => setEditDialog({
                    ...editDialog,
                    data: { ...editDialog.data, role: e.target.value }
                  })}
                >
                  <MenuItem value="user">Пользователь</MenuItem>
                  <MenuItem value="moderator">Модератор</MenuItem>
                  <MenuItem value="admin">Администратор</MenuItem>
                </Select>
              </FormControl>
            </>
          )}
          
          {editDialog.type === 'violation' && editDialog.data && (
            <>
              <TextField
                fullWidth
                label="Категория"
                value={editDialog.data.category || ''}
                onChange={(e) => setEditDialog({
                  ...editDialog,
                  data: { ...editDialog.data, category: e.target.value }
                })}
                margin="normal"
              />
              <FormControl fullWidth margin="normal">
                <InputLabel>Статус</InputLabel>
                <Select
                  value={editDialog.data.status || 'pending'}
                  onChange={(e) => setEditDialog({
                    ...editDialog,
                    data: { ...editDialog.data, status: e.target.value }
                  })}
                >
                  <MenuItem value="pending">В ожидании</MenuItem>
                  <MenuItem value="approved">Одобрено</MenuItem>
                  <MenuItem value="rejected">Отклонено</MenuItem>
                  <MenuItem value="resolved">Решено</MenuItem>
                </Select>
              </FormControl>
              <TextField
                fullWidth
                label="Заметки"
                multiline
                rows={3}
                value={editDialog.data.notes || ''}
                onChange={(e) => setEditDialog({
                  ...editDialog,
                  data: { ...editDialog.data, notes: e.target.value }
                })}
                margin="normal"
              />
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialog({ open: false, type: null, data: null })}>
            Отмена
          </Button>
          <Button onClick={handleSaveEdit} variant="contained">
            Сохранить
          </Button>
        </DialogActions>
      </Dialog>

      {/* Диалог подтверждения удаления */}
      <Dialog 
        open={deleteDialog.open} 
        onClose={() => setDeleteDialog({ open: false, type: null, id: null })}
      >
        <DialogTitle>Подтверждение удаления</DialogTitle>
        <DialogContent>
          <Typography>
            Вы уверены, что хотите удалить этот {deleteDialog.type === 'user' ? 'пользователь' : 'нарушение'}?
            Это действие нельзя отменить.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialog({ open: false, type: null, id: null })}>
            Отмена
          </Button>
          <Button onClick={handleConfirmDelete} color="error" variant="contained">
            Удалить
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
