import React, { createContext, useState, useEffect, ReactNode } from 'react';
import axios from 'axios';
import jwtDecode from 'jwt-decode';

interface AuthContextType {
  isAuthenticated: boolean;
  user: User | null;
  login: (accessToken: string, refreshToken: string) => void;
  logout: () => void;
  refreshAuth: () => Promise<boolean>;
}

interface User {
  id: number;
  username: string;
  role: string;
}

interface JwtPayload {
  sub: number;
  username: string;
  role: string;
  exp: number;
  type: string;
}

export const AuthContext = createContext<AuthContextType>({
  isAuthenticated: false,
  user: null,
  login: () => {},
  logout: () => {},
  refreshAuth: async () => false,
});

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [user, setUser] = useState<User | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(
    localStorage.getItem('accessToken')
  );
  const [refreshToken, setRefreshToken] = useState<string | null>(
    localStorage.getItem('refreshToken')
  );

  // Set up axios interceptor for authentication
  useEffect(() => {
    const interceptor = axios.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;
        
        // If the error is 401 and we haven't tried to refresh the token yet
        if (
          error.response?.status === 401 &&
          !originalRequest._retry &&
          refreshToken
        ) {
          originalRequest._retry = true;
          
          // Try to refresh the token
          const refreshed = await refreshAuth();
          
          if (refreshed && accessToken) {
            // Update the authorization header
            originalRequest.headers['Authorization'] = `Bearer ${accessToken}`;
            return axios(originalRequest);
          }
        }
        
        return Promise.reject(error);
      }
    );
    
    return () => {
      axios.interceptors.response.eject(interceptor);
    };
  }, [refreshToken, accessToken]);

  // Set up axios default headers
  useEffect(() => {
    if (accessToken) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`;
    } else {
      delete axios.defaults.headers.common['Authorization'];
    }
  }, [accessToken]);

  // Check if token is valid on mount
  useEffect(() => {
    const validateToken = async () => {
      if (accessToken) {
        try {
          // Decode token to check expiration
          const decoded = jwtDecode<JwtPayload>(accessToken);
          const currentTime = Date.now() / 1000;
          
          if (decoded.exp < currentTime) {
            // Token is expired, try to refresh
            await refreshAuth();
          } else {
            // Token is valid
            setIsAuthenticated(true);
            setUser({
              id: decoded.sub,
              username: decoded.username,
              role: decoded.role,
            });
          }
        } catch (error) {
          // Invalid token
          logout();
        }
      }
    };
    
    validateToken();
  }, []);

  const login = (newAccessToken: string, newRefreshToken: string) => {
    localStorage.setItem('accessToken', newAccessToken);
    localStorage.setItem('refreshToken', newRefreshToken);
    
    setAccessToken(newAccessToken);
    setRefreshToken(newRefreshToken);
    
    try {
      const decoded = jwtDecode<JwtPayload>(newAccessToken);
      setUser({
        id: decoded.sub,
        username: decoded.username,
        role: decoded.role,
      });
      setIsAuthenticated(true);
    } catch (error) {
      console.error('Failed to decode token:', error);
      logout();
    }
  };

  const logout = () => {
    // If we have a refresh token, try to revoke it
    if (refreshToken) {
      axios.post('/auth/logout', { refresh_token: refreshToken })
        .catch((error) => {
          console.error('Failed to logout on server:', error);
        });
    }
    
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    
    setAccessToken(null);
    setRefreshToken(null);
    setUser(null);
    setIsAuthenticated(false);
    
    delete axios.defaults.headers.common['Authorization'];
  };

  const refreshAuth = async (): Promise<boolean> => {
    if (!refreshToken) {
      logout();
      return false;
    }
    
    try {
      const response = await axios.post('/auth/refresh', {
        refresh_token: refreshToken,
      });
      
      const { access_token, refresh_token } = response.data;
      
      login(access_token, refresh_token);
      return true;
    } catch (error) {
      console.error('Failed to refresh token:', error);
      logout();
      return false;
    }
  };

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        user,
        login,
        logout,
        refreshAuth,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export default AuthProvider;
