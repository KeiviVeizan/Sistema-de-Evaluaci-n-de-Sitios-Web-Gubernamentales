import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ROLES } from '../contexts/AuthContext';

// Componentes de routing
import { ProtectedRoute, RoleBasedRoute, PublicRoute } from '../components/routing';

// Layouts
import { AdminLayout } from '../components/layouts';

// Páginas de autenticación
import { Login, TwoFactorAuth } from '../pages/auth';

// Páginas del panel administrativo
import { Dashboard, Institutions, InstitutionDetail, Users, NewEvaluation, EvaluationDetail } from '../pages/admin';

// Página pública (evaluador público)
import PublicEvaluator from '../pages/public/PublicEvaluator';

// Páginas del panel de institución
import MyFollowups from '../pages/institution/MyFollowups';
import InstitutionEvaluations from '../pages/institution/InstitutionEvaluations';

// Páginas placeholder para rutas que se implementarán después
function PlaceholderPage({ title }) {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '60vh',
      textAlign: 'center',
      padding: '24px',
    }}>
      <h1 style={{ fontSize: '1.5rem', fontWeight: 600, marginBottom: '8px' }}>
        {title}
      </h1>
      <p style={{ color: '#666' }}>
        Esta sección está en desarrollo
      </p>
    </div>
  );
}

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Raíz → redirige al login */}
        <Route path="/" element={<Navigate to="/login" replace />} />

        {/* Rutas de autenticación (solo sin autenticación) */}
        <Route
          path="/login"
          element={
            <PublicRoute>
              <Login />
            </PublicRoute>
          }
        />
        <Route path="/auth/2fa" element={<TwoFactorAuth />} />
        <Route
          path="/auth/forgot-password"
          element={
            <PublicRoute>
              <PlaceholderPage title="Recuperar Contraseña" />
            </PublicRoute>
          }
        />

        {/* Rutas del panel administrativo (protegidas) */}
        <Route
          path="/admin"
          element={
            <ProtectedRoute>
              <AdminLayout />
            </ProtectedRoute>
          }
        >
          {/* Dashboard - Todos los roles */}
          <Route index element={<Dashboard />} />

          {/* Evaluaciones */}
          <Route
            path="evaluations"
            element={
              <RoleBasedRoute
                allowedRoles={[ROLES.SUPERADMIN, ROLES.SECRETARY, ROLES.EVALUATOR]}
                showAccessDenied
              >
                <NewEvaluation />
              </RoleBasedRoute>
            }
          />
          <Route
            path="evaluations/new"
            element={
              <RoleBasedRoute
                allowedRoles={[ROLES.SUPERADMIN, ROLES.SECRETARY, ROLES.EVALUATOR]}
                showAccessDenied
              >
                <NewEvaluation />
              </RoleBasedRoute>
            }
          />
          <Route
            path="evaluations/:id"
            element={
              <RoleBasedRoute
                allowedRoles={[ROLES.SUPERADMIN, ROLES.SECRETARY, ROLES.EVALUATOR, ROLES.ENTITY_USER]}
                showAccessDenied
              >
                <EvaluationDetail />
              </RoleBasedRoute>
            }
          />

          {/* Reportes - Todos los roles */}
          <Route
            path="reports"
            element={<PlaceholderPage title="Reportes" />}
          />

          {/* Instituciones - Solo Secretary y Superadmin */}
          <Route
            path="institutions"
            element={
              <RoleBasedRoute
                allowedRoles={[ROLES.SUPERADMIN, ROLES.SECRETARY]}
                showAccessDenied
              >
                <Institutions />
              </RoleBasedRoute>
            }
          />
          <Route
            path="institutions/:id"
            element={
              <RoleBasedRoute
                allowedRoles={[ROLES.SUPERADMIN, ROLES.SECRETARY]}
                showAccessDenied
              >
                <InstitutionDetail />
              </RoleBasedRoute>
            }
          />

          {/* Usuarios - Solo Superadmin */}
          <Route
            path="users"
            element={
              <RoleBasedRoute
                allowedRoles={[ROLES.SUPERADMIN, ROLES.SECRETARY]}
                showAccessDenied
              >
                <Users />
              </RoleBasedRoute>
            }
          />
          <Route
            path="users/:id"
            element={
              <RoleBasedRoute
                allowedRoles={[ROLES.SUPERADMIN, ROLES.SECRETARY]}
                showAccessDenied
              >
                <PlaceholderPage title="Detalle de Usuario" />
              </RoleBasedRoute>
            }
          />

          {/* Configuración - Solo Superadmin */}
          <Route
            path="settings"
            element={
              <RoleBasedRoute
                allowedRoles={[ROLES.SUPERADMIN]}
                showAccessDenied
              >
                <PlaceholderPage title="Configuración del Sistema" />
              </RoleBasedRoute>
            }
          />

          {/* Evaluaciones de institución - Solo entity_user */}
          <Route
            path="my-evaluations"
            element={
              <RoleBasedRoute
                allowedRoles={[ROLES.ENTITY_USER]}
                showAccessDenied
              >
                <InstitutionEvaluations />
              </RoleBasedRoute>
            }
          />

          {/* Seguimientos de institución - Solo entity_user */}
          <Route
            path="my-followups"
            element={
              <RoleBasedRoute
                allowedRoles={[ROLES.ENTITY_USER]}
                showAccessDenied
              >
                <MyFollowups />
              </RoleBasedRoute>
            }
          />

          {/* Perfil - Todos los roles autenticados */}
          <Route
            path="profile"
            element={<PlaceholderPage title="Mi Perfil" />}
          />
        </Route>

        {/* Ruta 404 */}
        <Route
          path="*"
          element={
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              minHeight: '100vh',
              textAlign: 'center',
              padding: '24px',
            }}>
              <h1 style={{ fontSize: '4rem', fontWeight: 700, color: '#800000', margin: 0 }}>
                404
              </h1>
              <p style={{ fontSize: '1.25rem', color: '#666', marginBottom: '24px' }}>
                Página no encontrada
              </p>
              <a
                href="/"
                style={{
                  padding: '12px 24px',
                  background: '#800000',
                  color: 'white',
                  borderRadius: '8px',
                  textDecoration: 'none',
                }}
              >
                Volver al inicio
              </a>
            </div>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}
