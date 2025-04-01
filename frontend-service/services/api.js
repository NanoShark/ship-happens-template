import axios from 'axios';
import { useState, useEffect, useCallback } from 'react';

const API_URL = '/api';  // Proxied through Nginx to API Gateway

// Configure axios with interceptors
const configureAxios = () => {
  // Add token to requests if available
  axios.interceptors.request.use(
    config => {
      const token = localStorage.getItem('token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    error => {
      return Promise.reject(error);
    }
  );
};

// Call configuration on module load
configureAxios();

// Auth endpoints
export const login = async (credentials) => {
  try {
    const response = await axios.post(`${API_URL}/auth/login`, credentials);
    localStorage.setItem('token', response.data.token);
    return response.data;
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
};

export const register = async (userData) => {
  try {
    const response = await axios.post(`${API_URL}/auth/register`, userData);
    return response.data;
  } catch (error) {
    console.error('Registration error:', error);
    throw error;
  }
};

export const logout = () => {
  localStorage.removeItem('token');
};

// User endpoints as React hooks
export const useUsers = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchUsers = useCallback(async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_URL}/users`);
      setUsers(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch users');
      console.error('Error fetching users:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  return { users, loading, error, refreshUsers: fetchUsers };
};

export const useUser = (userId) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchUser = useCallback(async () => {
    if (!userId) return;
    
    try {
      setLoading(true);
      const response = await axios.get(`${API_URL}/users/${userId}`);
      setUser(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch user');
      console.error('Error fetching user:', err);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  return { user, loading, error, refreshUser: fetchUser };
};

export const useCreateUser = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [createdUser, setCreatedUser] = useState(null);

  const createUser = async (userData) => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.post(`${API_URL}/users`, userData);
      setCreatedUser(response.data);
      return response.data;
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to create user');
      console.error('Error creating user:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { createUser, loading, error, createdUser };
};

export const useUpdateUser = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [updatedUser, setUpdatedUser] = useState(null);

  const updateUser = async (userId, userData) => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.put(`${API_URL}/users/${userId}`, userData);
      setUpdatedUser(response.data);
      return response.data;
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to update user');
      console.error('Error updating user:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { updateUser, loading, error, updatedUser };
};

export const useDeleteUser = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [deleted, setDeleted] = useState(false);

  const deleteUser = async (userId) => {
    try {
      setLoading(true);
      setError(null);
      await axios.delete(`${API_URL}/users/${userId}`);
      setDeleted(true);
      return true;
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to delete user');
      console.error('Error deleting user:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { deleteUser, loading, error, deleted };
};

// Also export the original function versions for flexibility
export const getUsersAsync = async () => {
  try {
    const response = await axios.get(`${API_URL}/users`);
    return response.data;
  } catch (error) {
    console.error('Error fetching users:', error);
    throw error;
  }
};

export const createUserAsync = async (userData) => {
  try {
    const response = await axios.post(`${API_URL}/users`, userData);
    return response.data;
  } catch (error) {
    console.error('Error creating user:', error);
    throw error;
  }
};

export const updateUserAsync = async (userId, userData) => {
  try {
    const response = await axios.put(`${API_URL}/users/${userId}`, userData);
    return response.data;
  } catch (error) {
    console.error('Error updating user:', error);
    throw error;
  }
};

export const deleteUserAsync = async (userId) => {
  try {
    const response = await axios.delete(`${API_URL}/users/${userId}`);
    return response.data;
  } catch (error) {
    console.error('Error deleting user:', error);
    throw error;
  }
};