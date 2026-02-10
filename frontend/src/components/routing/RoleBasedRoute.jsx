import { Navigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { ShieldX } from 'lucide-react';
import styles from './ProtectedRoute.module.css';

/**
 * Componente que protege rutas basadas en roles
 * @param {Array|string} allowedRoles - Roles permitidos para acceder
 * @param {React.ReactNode} children - Contenido a renderizar si tiene permiso
 * @param {string} redirectTo - Ruta de redirección si no tiene permiso (default: /admin)
 */
export default function RoleBasedRoute({
  allowedRoles,
  children,
  redirectTo = '/admin',
  showAccessDenied = false,
}) {
  const { user, hasRole, loading } = useAuth();

  // Loading se maneja en ProtectedRoute padre
  if (loading) {
    return null;
  }

  // Verificar si el usuario tiene uno de los roles permitidos
  const hasAccess = hasRole(allowedRoles);

  if (!hasAccess) {
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
