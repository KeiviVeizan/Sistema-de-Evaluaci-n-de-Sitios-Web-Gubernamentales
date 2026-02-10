import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import authService from '../services/authService';

// Roles del sistema (deben coincidir con backend)
export const ROLES = {
  SUPERADMIN: 'superadmin',
  SECRETARY: 'secretary',
  EVALUATOR: 'evaluator',
  ENTITY_USER: 'entity_user',
};

// Permisos por rol
export const ROLE_PERMISSIONS = {
  [ROLES.SUPERADMIN]: [
    'manage_users',
    'manage_roles',
    'manage_institutions',
    'view_all_evaluations',
    'create_evaluations',
    'edit_evaluations',
    'delete_evaluations',
    'view_reports',
    'export_reports',
    'manage_settings',
  ],
  [ROLES.SECRETARY]: [
    'manage_users',
    'manage_institutions',
    'view_all_evaluations',
    'create_evaluations',
    'edit_evaluations',
    'view_reports',
    'export_reports',
  ],
  [ROLES.EVALUATOR]: [
    'view_all_evaluations',
    'create_evaluations',
    'edit_own_evaluations',
    'view_reports',
  ],
  [ROLES.ENTITY_USER]: [
    'view_own_evaluations',
    'view_reports',
  ],
};

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [requires2FA, setRequires2FA] = useState(false);
  const [pendingUsername, setPendingUsername] = useState(null);

  // Verificar sesión al cargar
  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      if (authService.isAuthenticated()) {
        const userData = await authService.getProfile();
        setUser(userData);
      }
    } catch (err) {
      // Token inválido o expirado
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
    } finally {
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    setError(null);
    try {
      const response = await authService.login(username, password);

      // El backend siempre requiere 2FA ahora
      // Guarda el username para el paso 2
      setRequires2FA(true);
      setPendingUsername(response.username);
      return { requires2FA: true };
    } catch (err) {
      const message = err.response?.data?.detail || 'Error al iniciar sesión';
      setError(message);
      throw new Error(message);
    }
  };

  const verify2FA = async (code) => {
    setError(null);
    try {
      const response = await authService.verify2FA(pendingUsername, code);
      authService.saveTokens(response.access_token, response.refresh_token);
      setUser(response.user);
      setRequires2FA(false);
      setPendingUsername(null);
      return { success: true };
    } catch (err) {
      const message = err.response?.data?.detail || 'Código inválido';
      setError(message);
      throw new Error(message);
    }
  };

  const logout = useCallback(async () => {
    try {
      await authService.logout();
    } finally {
      setUser(null);
      setRequires2FA(false);
      setPendingUsername(null);
    }
  }, []);

  const cancelLogin = () => {
    setRequires2FA(false);
    setPendingUsername(null);
    setError(null);
  };

  // Verificar si el usuario tiene un rol específico
  const hasRole = useCallback((role) => {
    if (!user) return false;
    if (Array.isArray(role)) {
      return role.includes(user.role);
    }
    return user.role === role;
  }, [user]);

  // Verificar si el usuario tiene un permiso específico
  const hasPermission = useCallback((permission) => {
    if (!user) return false;
    const userPermissions = ROLE_PERMISSIONS[user.role] || [];
    return userPermissions.includes(permission);
  }, [user]);

  // Verificar múltiples permisos (todos deben cumplirse)
  const hasAllPermissions = useCallback((permissions) => {
    return permissions.every(p => hasPermission(p));
  }, [hasPermission]);

  // Verificar múltiples permisos (al menos uno debe cumplirse)
  const hasAnyPermission = useCallback((permissions) => {
    return permissions.some(p => hasPermission(p));
  }, [hasPermission]);

  const value = {
    user,
    loading,
    error,
    requires2FA,
    isAuthenticated: !!user,
    login,
    verify2FA,
    logout,
    cancelLogin,
    hasRole,
    hasPermission,
    hasAllPermissions,
    hasAnyPermission,
    checkAuth,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth debe usarse dentro de un AuthProvider');
  }
  return context;
}

export default AuthContext;
