import { Navigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { ShieldX } from 'lucide-react';
import styles from './ProtectedRoute.module.css';

/**
 * Componente que protege rutas basadas en roles y/o permisos granulares
 * @param {Array|string} allowedRoles - Roles permitidos para acceder
 * @param {string} requiredPermission - Permiso granular requerido (opcional)
 * @param {React.ReactNode} children - Contenido a renderizar si tiene permiso
 * @param {React.ReactNode} fallback - Contenido alternativo si no tiene permiso (en lugar de redirigir)
 * @param {string} redirectTo - Ruta de redirección si no tiene permiso (default: /admin)
 * @param {boolean} showAccessDenied - Mostrar mensaje de acceso denegado en lugar de redirigir
 */
export default function RoleBasedRoute({
  allowedRoles,
  requiredPermission,
  children,
  fallback = null,
  redirectTo = '/admin',
  showAccessDenied = false,
}) {
  const { user, hasRole, hasPermission, loading } = useAuth();

  // Loading se maneja en ProtectedRoute padre
  if (loading) {
    return null;
  }

  // Verificar si el usuario tiene uno de los roles permitidos
  // y si se requiere un permiso granular, verificarlo también
  const hasAccess = hasRole(allowedRoles) && (!requiredPermission || hasPermission(requiredPermission));

  if (!hasAccess) {
    // Si hay un fallback, renderizarlo en lugar de redirigir
    if (fallback !== null) {
      return fallback;
    }

    // Opcionalmente mostrar mensaje de acceso denegado en lugar de redirigir
    if (showAccessDenied) {
      return (
        <div className={styles.accessDenied}>
          <ShieldX size={48} className={styles.accessDeniedIcon} />
          <h2>Acceso Denegado</h2>
          <p>No tienes permisos para acceder a esta sección.</p>
          <p className={styles.roleInfo}>
            Tu rol actual: <strong>{user?.role}</strong>
          </p>
        </div>
      );
    }

    return <Navigate to={redirectTo} replace />;
  }

  return children;
}
