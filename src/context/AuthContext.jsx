import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import {
  getStoredToken,
  setStoredToken,
  clearStoredToken,
  getCurrentUser,
  loginUser,
  registerUser,
  logoutUser as apiLogoutUser,
} from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(getStoredToken());
  const [isLoading, setIsLoading] = useState(true);
  const [authError, setAuthError] = useState(null);

  /**
   * Validates stored token on application mount.
   * Note: Merely possessing a token in localStorage is NOT treated as proof of auth.
   * It must be actively verified by the backend (/api/auth/me).
   */
  const verifySession = useCallback(async () => {
    const existingToken = getStoredToken();
    if (!existingToken) {
      setUser(null);
      setToken(null);
      setIsLoading(false);
      return;
    }

    try {
      const verifiedProfile = await getCurrentUser();
      setUser(verifiedProfile);
      setToken(existingToken);
      setAuthError(null);

      // Verify that sessionStorage data belongs to verified user; purge if belongs to someone else
      try {
        const raw = sessionStorage.getItem('herturn_session');
        if (raw) {
          const parsed = JSON.parse(raw);
          const sessionEmail = parsed?.candidate?.email;
          if (sessionEmail && verifiedProfile?.email && sessionEmail.toLowerCase() !== verifiedProfile.email.toLowerCase()) {
            sessionStorage.clear();
          }
        }
      } catch (_) {}

    } catch (err) {
      console.warn('Session verification failed, logging out:', err.message);
      clearStoredToken();
      setUser(null);
      setToken(null);
      try { sessionStorage.clear(); } catch (_) {}
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    verifySession();
  }, [verifySession]);

  /**
   * Authenticates user with credentials
   */
  const login = async (email, password) => {
    setAuthError(null);
    try {
      const result = await loginUser({ email, password });
      setUser(result.user);
      setToken(result.accessToken);

      // Ensure any previous user's sessionStorage is completely cleared
      try {
        const raw = sessionStorage.getItem('herturn_session');
        if (raw) {
          const parsed = JSON.parse(raw);
          const sessionEmail = parsed?.candidate?.email;
          if (sessionEmail && sessionEmail.toLowerCase() !== result.user.email.toLowerCase()) {
            sessionStorage.clear();
          }
        }
      } catch (_) {}

      return result.user;
    } catch (err) {
      setAuthError(err.message);
      throw err;
    }
  };

  /**
   * Registers a new candidate account
   */
  const register = async ({ email, password, fullName, targetRole }) => {
    setAuthError(null);
    try {
      const result = await registerUser({ email, password, fullName, targetRole });
      setUser(result.user);
      setToken(result.accessToken);

      // Purge any stale session from prior guest or other user
      try {
        sessionStorage.clear();
      } catch (_) {}

      return result.user;
    } catch (err) {
      setAuthError(err.message);
      throw err;
    }
  };

  /**
   * Destroys current session and wipes client-side caches
   */
  const logout = () => {
    apiLogoutUser();
    clearStoredToken();
    try {
      sessionStorage.clear();
    } catch (_) {}
    setUser(null);
    setToken(null);
    setAuthError(null);
  };

  const value = {
    user,
    token,
    isAuthenticated: !!user,
    isLoading,
    authError,
    login,
    register,
    logout,
    refreshUser: verifySession,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
