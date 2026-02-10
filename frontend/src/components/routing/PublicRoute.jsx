import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { Loader } from 'lucide-react';
import styles from './ProtectedRoute.module.css';

/**
 * Componente para rutas públicas (solo accesibles sin autenticación)
 * Redirige a /admin si el usuario ya está autenticado
 */
export default function PublicRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  // Mostrar loading mientras se verifica
  if (loading) {
    return (
      <div className={styles.loading}>
        <Loader size={32} className={styles.spinner} />
        <span>Cargando...</span>
      </div>
    );
  }

  // Redirigir a donde venía o al dashboard si ya está autenticado
  if (isAuthenticated) {
    const from = location.state?.from?.pathname || '/admin';
    return <Navigate to={from} replace />;
  }

  return children;
}
