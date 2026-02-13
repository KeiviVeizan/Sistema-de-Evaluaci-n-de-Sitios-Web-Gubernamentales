import { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { ROLES } from '../../contexts/AuthContext';
import {
  LayoutDashboard,
  Building2,
  Users,
  FileText,
  BarChart3,
  ClipboardList,
  CheckCircle2,
  Settings,
  LogOut,
  ChevronLeft,
  ChevronRight,
  X,
} from 'lucide-react';
import styles from './ModernSidebar.module.css';

const MENU_ITEMS = {
  [ROLES.SUPERADMIN]: [
    { path: '/admin/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/admin/institutions', icon: Building2, label: 'Instituciones' },
    { path: '/admin/users', icon: Users, label: 'Usuarios' },
    { path: '/admin/evaluations', icon: FileText, label: 'Evaluaciones' },
    { path: '/admin/reports', icon: BarChart3, label: 'Reportes' },
  ],
  [ROLES.SECRETARY]: [
    { path: '/admin/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/admin/institutions', icon: Building2, label: 'Instituciones' },
    { path: '/admin/users', icon: Users, label: 'Usuarios' },
    { path: '/admin/evaluations', icon: FileText, label: 'Evaluaciones' },
    { path: '/admin/reports', icon: BarChart3, label: 'Reportes' },
  ],
  [ROLES.EVALUATOR]: [
    { path: '/admin/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/admin/institutions', icon: Building2, label: 'Instituciones' },
    { path: '/admin/evaluator/my-evaluations', icon: ClipboardList, label: 'Mis Evaluaciones' },
  ],
  [ROLES.ENTITY_USER]: [
    { path: '/admin/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/admin/my-evaluations', icon: FileText, label: 'Mis Evaluaciones' },
    { path: '/admin/my-followups', icon: CheckCircle2, label: 'Seguimientos' },
  ],
};

/**
 * Props:
 *  - onCollapse(bool)   — notifica al layout cuando se colapsa en desktop
 *  - mobileOpen(bool)   — controlado desde el layout
 *  - onMobileClose()    — callback para cerrar desde dentro del sidebar
 */
function ModernSidebar({ onCollapse, mobileOpen = false, onMobileClose }) {
  const { user, logout } = useAuth();
  const [collapsed, setCollapsed] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < 768);
    check();
    window.addEventListener('resize', check);
    return () => window.removeEventListener('resize', check);
  }, []);

  const handleToggle = () => {
    const next = !collapsed;
    setCollapsed(next);
    if (onCollapse) onCollapse(next);
  };

  const handleNavClick = () => {
    if (isMobile && onMobileClose) onMobileClose();
  };

  const currentMenuItems = MENU_ITEMS[user?.role] || [];
  const showLabels = !collapsed || isMobile;

  return (
    <>
      {/* Overlay oscuro — solo en móvil cuando el menú está abierto */}
      {isMobile && mobileOpen && (
        <div
          className={styles.overlay}
          onClick={onMobileClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        className={[
          styles.sidebar,
          !isMobile && collapsed ? styles.collapsed : '',
          isMobile ? (mobileOpen ? styles.mobileOpen : styles.mobileHidden) : '',
        ]
          .filter(Boolean)
          .join(' ')}
        aria-label="Navegación principal"
      >
        {/* Header: toggle en desktop, X en móvil (esquina superior derecha) */}
        <div className={styles.header}>
          {!isMobile && (
            <button
              className={styles.toggleBtn}
              onClick={handleToggle}
              title={collapsed ? 'Expandir menú' : 'Contraer menú'}
              aria-label={collapsed ? 'Expandir menú' : 'Contraer menú'}
            >
              {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
            </button>
          )}

          {isMobile && (
            <button
              className={styles.closeBtn}
              onClick={onMobileClose}
              aria-label="Cerrar menú"
            >
              <X size={20} />
            </button>
          )}
        </div>

        {/* Separador decorativo */}
        <div className={styles.divider} />

        {/* Navegación principal */}
        <nav className={styles.nav} aria-label="Menú de navegación">
          {currentMenuItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={handleNavClick}
              className={({ isActive }) =>
                `${styles.navItem} ${isActive ? styles.active : ''}`
              }
              title={!isMobile && collapsed ? item.label : undefined}
            >
              <span className={styles.navIcon}>
                <item.icon size={22} />
              </span>
              {showLabels && (
                <span className={styles.navLabel}>{item.label}</span>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Footer: perfil y logout */}
        <div className={styles.footer}>
          <div className={styles.divider} />

          {showLabels && user && (
            <div className={styles.userInfo}>
              <div className={styles.userAvatar}>
                {user.name?.charAt(0).toUpperCase() || 'U'}
              </div>
              <div className={styles.userDetails}>
                <span className={styles.userName}>{user.name || 'Usuario'}</span>
                <span className={styles.userRole}>{user.role}</span>
              </div>
            </div>
          )}

          <NavLink
            to="/admin/profile"
            onClick={handleNavClick}
            className={({ isActive }) =>
              `${styles.navItem} ${isActive ? styles.active : ''}`
            }
            title={!isMobile && collapsed ? 'Mi Perfil' : undefined}
          >
            <span className={styles.navIcon}>
              <Settings size={22} />
            </span>
            {showLabels && <span className={styles.navLabel}>Mi Perfil</span>}
          </NavLink>

          <button
            className={`${styles.navItem} ${styles.logoutBtn}`}
            onClick={() => {
              handleNavClick();
              logout();
            }}
            title={!isMobile && collapsed ? 'Cerrar Sesión' : undefined}
          >
            <span className={styles.navIcon}>
              <LogOut size={22} />
            </span>
            {showLabels && <span className={styles.navLabel}>Cerrar Sesión</span>}
          </button>
        </div>
      </aside>
    </>
  );
}

export default ModernSidebar;
