import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { User, Role } from '../types/models';

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (email: string, password?: string, role?: Role) => Promise<void>;
  register: (email: string, password: string, role?: Role, displayName?: string) => Promise<void>;
  resetPassword: (email: string, password: string, role?: Role) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

function toFrontendRole(roleStr: string): Role {
  const lower = (roleStr || '').toLowerCase();
  if (lower === 'authority') return 'Authority';
  if (lower === 'admin') return 'Admin';
  if (lower === 'community') return 'Community';
  return 'Citizen';
}

// Resilient fetch helper that handles both Vite proxy and direct backend access
async function postAuth(endpoint: string, body: any): Promise<Response> {
  const tryFetch = async (url: string) => {
    return await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
  };

  try {
    return await tryFetch(endpoint);
  } catch {
    // If relative endpoint fails (proxy issue or network error), fallback to direct backend host
    if (endpoint.startsWith('/')) {
      const backendBase = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
      const directUrl = `${backendBase}${endpoint}`;
      try {
        return await tryFetch(directUrl);
      } catch {
        throw new Error(`Backend server is unreachable at ${backendBase}. Please ensure the backend is running.`);
      }
    }
    throw new Error('Connection to authentication server failed. Please check backend connection.');
  }
}

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(() => {
    try {
      const savedUser = localStorage.getItem('civicpulse_user');
      return savedUser ? JSON.parse(savedUser) : null;
    } catch {
      return null;
    }
  });
  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem('civicpulse_token');
  });
  const [isLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const logout = useCallback(() => {
    setUser(null);
    setToken(null);
    setError(null);
    localStorage.removeItem('civicpulse_token');
    localStorage.removeItem('civicpulse_user');
  }, []);

  // Validate stored session on application load
  useEffect(() => {
    const savedToken = localStorage.getItem('civicpulse_token');
    if (!savedToken) return;

    const verifyHeaders = { Authorization: `Bearer ${savedToken}` };
    const backendBase = import.meta.env.VITE_API_BASE_URL || '';
    const meUrl = backendBase ? `${backendBase}/auth/me` : '/auth/me';
    fetch(meUrl, { headers: verifyHeaders })
      .catch(() => fetch('http://127.0.0.1:8000/auth/me', { headers: verifyHeaders }))
      .then((res) => {
        if (res && res.ok) {
          return res.json().then((meData) => {
            const refreshedUser: User = {
              id: String(meData.id),
              name: meData.display_name || meData.username || meData.email.split('@')[0],
              email: meData.email,
              role: toFrontendRole(meData.role),
            };
            setUser(refreshedUser);
            localStorage.setItem('civicpulse_user', JSON.stringify(refreshedUser));
          });
        } else if (res && (res.status === 401 || res.status === 403)) {
          logout();
        }
      })
      .catch(() => {
        // Retain local session
      });
  }, [logout]);

  const login = async (email: string, password = '', _role?: Role): Promise<void> => {
    setError(null);
    try {
      const response = await postAuth('/auth/login', {
        email: email.trim(),
        password: password || 'Default123!',
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        const message = errData.detail || 'Invalid email or password. Please try again.';
        setError(message);
        throw new Error(message);
      }

      const data = await response.json();
      const authenticatedUser: User = {
        id: String(data.user.id),
        name: data.user.display_name || data.user.username || data.user.email.split('@')[0],
        email: data.user.email,
        role: toFrontendRole(data.user.role),
      };

      setToken(data.access_token);
      setUser(authenticatedUser);
      localStorage.setItem('civicpulse_token', data.access_token);
      localStorage.setItem('civicpulse_user', JSON.stringify(authenticatedUser));
    } catch (err: any) {
      if (!error) setError(err.message || 'Login failed');
      throw err;
    }
  };

  const register = async (
    email: string,
    password: string,
    role: Role = 'Citizen',
    displayName?: string
  ): Promise<void> => {
    setError(null);
    try {
      const response = await postAuth('/auth/register', {
        email: email.trim(),
        password: password,
        role: role.toLowerCase(),
        display_name: displayName || email.split('@')[0],
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        const message =
          errData.detail || 'Registration failed. The email may already be in use.';
        setError(message);
        throw new Error(message);
      }

      const data = await response.json();
      const newUser: User = {
        id: String(data.user.id),
        name: data.user.display_name || data.user.username || data.user.email.split('@')[0],
        email: data.user.email,
        role: toFrontendRole(data.user.role),
      };

      setToken(data.access_token);
      setUser(newUser);
      localStorage.setItem('civicpulse_token', data.access_token);
      localStorage.setItem('civicpulse_user', JSON.stringify(newUser));
    } catch (err: any) {
      if (!error) setError(err.message || 'Registration failed');
      throw err;
    }
  };

  const resetPassword = async (
    email: string,
    password: string,
    role?: Role
  ): Promise<void> => {
    setError(null);
    try {
      const response = await postAuth('/auth/reset-password', {
        email: email.trim(),
        password: password,
        role: role ? role.toLowerCase() : undefined,
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        const message = errData.detail || 'Password reset failed. Please check inputs.';
        setError(message);
        throw new Error(message);
      }

      const data = await response.json();
      const authenticatedUser: User = {
        id: String(data.user.id),
        name: data.user.display_name || data.user.username || data.user.email.split('@')[0],
        email: data.user.email,
        role: toFrontendRole(data.user.role),
      };

      setToken(data.access_token);
      setUser(authenticatedUser);
      localStorage.setItem('civicpulse_token', data.access_token);
      localStorage.setItem('civicpulse_user', JSON.stringify(authenticatedUser));
    } catch (err: any) {
      if (!error) setError(err.message || 'Password update failed');
      throw err;
    }
  };

  const clearError = () => setError(null);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        login,
        register,
        resetPassword,
        logout,
        isAuthenticated: !!user,
        isLoading,
        error,
        clearError,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
