import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext();

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API_BASE = `${BACKEND_URL}/api`;

export function useAuth() {
  return useContext(AuthContext);
}

export function AuthProvider({ children }) {
  const [currentUser, setCurrentUser] = useState(null);
  const [userProfile, setUserProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('token'));

  useEffect(() => {
    // Check if user is logged in
    const checkAuth = async () => {
      const storedToken = localStorage.getItem('token');
      
      if (storedToken) {
        try {
          // Verify token and get user profile
          const response = await axios.get(`${API_BASE}/users/profile`, {
            headers: {
              'Authorization': `Bearer ${storedToken}`
            }
          });
          
          setUserProfile(response.data);
          setCurrentUser({ uid: response.data.uid, email: response.data.email });
          setToken(storedToken);
        } catch (error) {
          console.error('Token validation failed:', error);
          localStorage.removeItem('token');
          setToken(null);
          setCurrentUser(null);
          setUserProfile(null);
        }
      }
      
      setLoading(false);
    };

    checkAuth();
  }, []);

  const login = async (email, password, deviceId = null) => {
    try {
      const response = await axios.post(`${API_BASE}/auth/login`, {
        email,
        password,
        device_id: deviceId
      });
      
      const { token: newToken, user } = response.data;
      
      // Store token
      localStorage.setItem('token', newToken);
      setToken(newToken);
      setCurrentUser({ uid: user.uid, email: user.email });
      setUserProfile(user);
      
      return { user };
    } catch (error) {
      throw error;
    }
  };

  const signOut = async () => {
    try {
      localStorage.removeItem('token');
      setToken(null);
      setCurrentUser(null);
      setUserProfile(null);
    } catch (error) {
      throw error;
    }
  };

  const getToken = () => {
    return token || localStorage.getItem('token');
  };

  const value = {
    currentUser,
    userProfile,
    token,
    login,
    signOut,
    getToken,
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
}