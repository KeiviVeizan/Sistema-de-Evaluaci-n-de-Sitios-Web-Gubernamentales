import { useState } from 'react';
import { Outlet, NavLink, useLocation } from 'react-router-dom';
import { useAuth, ROLES, ROLE_LABELS } from '../../contexts/AuthContext';
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


function ModernLayout() {
  const { user, logout } = useAuth();
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const location = useLocation();

  // Páginas que deben ocupar todo el viewport (evaluación nueva)
  const isFullPage = location.pathname === '/admin/evaluations' ||
    location.pathname === '/admin/evaluations/new';

  return (
    <div className={`${styles.layout} ${sidebarCollapsed ? styles.sidebarCollapsed : ''}`}>
      {/* Logo flotante — solo visible en desktop */}
      <div className={styles.floatingLogo}>
        <img src="/LOGO-AGETIC.png" alt="AGETIC" />
      </div>

      {/* Sidebar moderno — recibe control de apertura móvil */}
      <ModernSidebar
        onCollapse={setSidebarCollapsed}
        mobileOpen={mobileSidebarOpen}
        onMobileClose={() => setMobileSidebarOpen(false)}
      />

      {/* Área principal */}
      <div className={`${styles.main} ${isFullPage ? styles.mainFullBleed : ''}`}>
        {/* Topbar */}
        <header className={`${styles.topbar} ${isFullPage ? styles.topbarFloat : ''}`}>
          <div className={styles.topbarLeft}>
            {/* Botón hamburger — solo visible en móvil */}
            <button
              className={styles.hamburger}
              onClick={() => setMobileSidebarOpen(true)}
              aria-label="Abrir menú"
            >
              <Menu size={22} />
            </button>

            {/* Logo — solo visible en móvil dentro del topbar */}
            <div className={styles.topbarLogo}>
              <img src="/LOGO-AGETIC.png" alt="AGETIC" />
            </div>

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
