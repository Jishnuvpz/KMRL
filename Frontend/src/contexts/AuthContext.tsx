/**
 * Enhanced Authentication Context with backend integration
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiService, LoginRequest } from '../services/api';

export interface User {
  username: string;
  role: 'Staff' | 'Manager' | 'Director' | 'Board Member' | 'Admin';
  department: 'Operations' | 'HR' | 'Finance' | 'Legal' | 'IT' | 'Safety' | 'All' | 'Engineering' | 'Maintenance';
}

interface AuthContextType {
  user: User | null;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => void;
  loading: boolean;
  error: string | null;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Check for existing session on mount
  useEffect(() => {
    const initAuth = async () => {
      const savedUser = localStorage.getItem('user');
      const token = localStorage.getItem('access_token');
      
      if (savedUser && token) {
        try {
          // Verify token is still valid by making a test request
          const healthResult = await apiService.getHealth();
          if (healthResult.success) {
            setUser(JSON.parse(savedUser));
          } else {
            // Token is invalid, clear storage
            localStorage.removeItem('user');
            localStorage.removeItem('access_token');
          }
        } catch {
          // Token is invalid, clear storage
          localStorage.removeItem('user');
          localStorage.removeItem('access_token');
        }
      }
      
      setLoading(false);
    };

    initAuth();
  }, []);

  const login = async (credentials: LoginRequest) => {
    setLoading(true);
    setError(null);

    try {
      const result = await apiService.login(credentials);
      
      if (result.success && result.data) {
        const userData: User = {
          username: result.data.user.username,
          role: result.data.user.role as User['role'],
          department: result.data.user.department as User['department'],
        };
        
        setUser(userData);
        localStorage.setItem('user', JSON.stringify(userData));
        // Token is already stored by apiService
      } else {
        const errorMessage = result.error?.message || 'Login failed';
        setError(errorMessage);
        throw new Error(errorMessage);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Network error during login';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    setError(null);
    localStorage.removeItem('user');
    apiService.logout();
  };

  const value: AuthContextType = {
    user,
    login,
    logout,
    loading,
    error,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;
