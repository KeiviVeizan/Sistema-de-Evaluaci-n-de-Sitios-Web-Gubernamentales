import { useState } from 'react';
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
  Shield,
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

function ModernSidebar({ onCollapse }) {
  const { user, logout } = useAuth();
  const [collapsed, setCollapsed] = useState(false);

  const handleToggle = () => {
    const next = !collapsed;
    setCollapsed(next);
    if (onCollapse) onCollapse(next);
  };

  const currentMenuItems = MENU_ITEMS[user?.role] || [];

  return (
    <aside
      className={`${styles.sidebar} ${collapsed ? styles.collapsed : ''}`}
      aria-label="Navegación principal"
    >
      {/* Header con logo y toggle */}
      <div className={styles.header}>
        <div className={styles.logo}>
          <Shield size={collapsed ? 28 : 36} className={styles.logoIcon} />
          {!collapsed && <span className={styles.logoText}>GOB.BO</span>}
        </div>
        <button
          className={styles.toggleBtn}
          onClick={handleToggle}
          title={collapsed ? 'Expandir menú' : 'Contraer menú'}
          aria-label={collapsed ? 'Expandir menú' : 'Contraer menú'}
        >
          {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
        </button>
      </div>

      {/* Separador decorativo */}
      <div className={styles.divider} />

      {/* Navegación principal */}
      <nav className={styles.nav} aria-label="Menú de navegación">
        {currentMenuItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `${styles.navItem} ${isActive ? styles.active : ''}`
            }
            title={collapsed ? item.label : undefined}
          >
            <span className={styles.navIcon}>
              <item.icon size={22} />
            </span>
            {!collapsed && <span className={styles.navLabel}>{item.label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Footer: perfil y logout */}
      <div className={styles.footer}>
        <div className={styles.divider} />

        {!collapsed && user && (
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
          className={({ isActive }) =>
            `${styles.navItem} ${isActive ? styles.active : ''}`
          }
          title={collapsed ? 'Mi Perfil' : undefined}
        >
          <span className={styles.navIcon}>
            <Settings size={22} />
          </span>
          {!collapsed && <span className={styles.navLabel}>Mi Perfil</span>}
        </NavLink>

        <button
          className={`${styles.navItem} ${styles.logoutBtn}`}
          onClick={logout}
          title={collapsed ? 'Cerrar Sesión' : undefined}
        >
          <span className={styles.navIcon}>
            <LogOut size={22} />
          </span>
          {!collapsed && <span className={styles.navLabel}>Cerrar Sesión</span>}
        </button>
      </div>
    </aside>
  );
}

export default ModernSidebar;
