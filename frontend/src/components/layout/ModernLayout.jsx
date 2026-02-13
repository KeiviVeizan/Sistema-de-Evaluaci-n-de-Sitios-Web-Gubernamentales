import { useState } from 'react';
import { Outlet, NavLink, useLocation } from 'react-router-dom';
import { useAuth, ROLES } from '../../contexts/AuthContext';
import {
  User,
  ChevronDown,
  Shield,
  LogOut,
  Menu,
} from 'lucide-react';
import ModernSidebar from './ModernSidebar';
import NotificationBell from '../ui/NotificationBell';
import styles from './ModernLayout.module.css';

// Mapeo de nombres de rol para mostrar
const ROLE_LABELS = {
  [ROLES.SUPERADMIN]: 'Super Administrador',
  [ROLES.SECRETARY]: 'Secretario',
  [ROLES.EVALUATOR]: 'Evaluador',
  [ROLES.ENTITY_USER]: 'Usuario de Entidad',
};

function ModernLayout() {
  const { user, logout } = useAuth();
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const location = useLocation();

  // Páginas que deben ocupar todo el espacio sin padding
  const isFullPage = location.pathname.startsWith('/admin/evaluations') &&
    !location.pathname.match(/\/admin\/evaluations\/[^/]+$/);

  return (
    <div className={`${styles.layout} ${sidebarCollapsed ? styles.sidebarCollapsed : ''}`}>
      {/* Sidebar moderno */}
      <ModernSidebar onCollapse={setSidebarCollapsed} />

      {/* Área principal */}
      <div className={styles.main}>
        {/* Topbar */}
        <header className={styles.topbar}>
          <div className={styles.topbarLeft}>
            <span className={styles.pageTitle}>
              Panel Administrativo
            </span>
          </div>

          <div className={styles.topbarRight}>
            {/* Notificaciones solo para evaluadores */}
            {user?.role === ROLES.EVALUATOR && <NotificationBell />}

            {/* Menú de usuario */}
            <div className={styles.userMenu}>
              <button
                className={styles.userMenuBtn}
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                aria-expanded={userMenuOpen}
                aria-label="Menú de usuario"
              >
                <div className={styles.userAvatar}>
                  {user?.name?.charAt(0).toUpperCase() || 'U'}
                </div>
                <span className={styles.userMenuName}>
                  {user?.name || 'Usuario'}
                </span>
                <ChevronDown
                  size={16}
                  className={`${styles.chevron} ${userMenuOpen ? styles.chevronOpen : ''}`}
                />
              </button>

              {userMenuOpen && (
                <>
                  <div
                    className={styles.menuOverlay}
                    onClick={() => setUserMenuOpen(false)}
                  />
                  <div className={styles.dropdown}>
                    <div className={styles.dropdownHeader}>
                      <div className={styles.dropdownName}>{user?.name}</div>
                      <div className={styles.dropdownEmail}>{user?.email}</div>
                      <div className={styles.roleBadge}>
                        <Shield size={11} />
                        {ROLE_LABELS[user?.role] || user?.role}
                      </div>
                    </div>

                    <div className={styles.dropdownDivider} />

                    <NavLink
                      to="/admin/profile"
                      className={styles.dropdownItem}
                      onClick={() => setUserMenuOpen(false)}
                    >
                      <User size={15} />
                      Mi Perfil
                    </NavLink>

                    <button
                      className={`${styles.dropdownItem} ${styles.dropdownLogout}`}
                      onClick={() => { setUserMenuOpen(false); logout(); }}
                    >
                      <LogOut size={15} />
                      Cerrar Sesión
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </header>

        {/* Contenido de la página */}
        <main className={isFullPage ? styles.contentFull : styles.content}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default ModernLayout;
