import React, { createContext, useContext, useState, useEffect } from 'react';
import { auth } from '../services/api';

const AuthContext = createContext();

export function useAuth() {
  return useContext(AuthContext);
}

export function AuthProvider({ children }) {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Сохранение пользователя в localStorage
  const saveUserToStorage = (user) => {
    if (user) {
      localStorage.setItem('currentUser', JSON.stringify(user));
      // Сохраняем токен из разных возможных полей
      const token = user.token || user.access_token || user.authToken || '';
      localStorage.setItem('authToken', token);
      localStorage.setItem('token', token); // Дублируем для совместимости
      console.log('Saved user to storage with token:', token ? 'YES' : 'NO');
    }
  };

  // Загрузка пользователя из localStorage
  const loadUserFromStorage = () => {
    try {
      const savedUser = localStorage.getItem('currentUser');
      const savedToken = localStorage.getItem('authToken');
      if (savedUser && savedToken) {
        return JSON.parse(savedUser);
      }
    } catch (error) {
      console.error('Error loading user from storage:', error);
    }
    return null;
  };

  // Очистка данных из localStorage
  const clearUserFromStorage = () => {
    localStorage.removeItem('currentUser');
    localStorage.removeItem('authToken');
    localStorage.removeItem('token');
    console.log('Cleared all auth data from storage');
  };

  // Sign up function
  const signup = async (username, email, password) => {
    try {
      const response = await auth.signup(username, email, password);
      const user = response.data.user;
      
      // Добавляем фиктивный токен для сессионной авторизации
      const userWithToken = {
        ...user,
        token: `session_${user.id}_${Date.now()}`,
        sessionId: user.id
      };
      
      setCurrentUser(userWithToken);
      saveUserToStorage(userWithToken);
      return response;
    } catch (error) {
      throw error;
    }
  };

  // Login function
  const login = async (email, password) => {
    try {
      const response = await auth.login(email, password);
      const user = response.data.user;
      
      // Добавляем фиктивный токен для сессионной авторизации
      const userWithToken = {
        ...user,
        token: `session_${user.id}_${Date.now()}`,
        sessionId: user.id
      };
      
      setCurrentUser(userWithToken);
      saveUserToStorage(userWithToken);
      return response;
    } catch (error) {
      throw error;
    }
  };

  // Logout function
  const logout = async () => {
    try {
      // Попытаться выполнить logout на backend
      await auth.logout();
    } catch (error) {
      // Даже если backend logout не удался, очищаем локальные данные
      console.warn('Backend logout failed, clearing local data:', error);
    } finally {
      // Всегда очищаем локальные данные
      setCurrentUser(null);
      clearUserFromStorage();
    }
  };

  // Check if user is logged in on initial load
  useEffect(() => {
    const checkAuth = async () => {
      // Сначала проверяем localStorage
      const savedUser = loadUserFromStorage();
      if (savedUser) {
        console.log('Loaded user from localStorage:', savedUser);
        setCurrentUser(savedUser);
        setLoading(false);
        
        // Для сессионной авторизации не проверяем токен через API
        // Просто используем сохраненные данные
        console.log('Using saved session data');
        return;
      }

      // Если нет сохраненного пользователя, проверяем через API
      try {
        const response = await auth.getCurrentUser();
        const user = response.data;
        setCurrentUser(user);
        saveUserToStorage(user);
      } catch (error) {
        console.error('Auth check failed:', error);
        setCurrentUser(null);
        clearUserFromStorage();
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  const value = {
    currentUser,
    signup,
    login,
    logout,
    clearUserFromStorage,
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
}

export default AuthContext;
