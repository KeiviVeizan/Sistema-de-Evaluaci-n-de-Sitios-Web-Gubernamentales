import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { Loader } from 'lucide-react';
import styles from './ProtectedRoute.module.css';

/**
 * Componente que protege rutas que requieren autenticación
 * Redirige a /login si el usuario no está autenticado
 */
export default function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  // Mostrar loading mientras se verifica la autenticación
  if (loading) {
    return (
      <div className={styles.loading}>
        <Loader size={32} className={styles.spinner} />
        <span>Verificando sesión...</span>
      </div>
    );
  }

  // Redirigir a login si no está autenticado
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
}
