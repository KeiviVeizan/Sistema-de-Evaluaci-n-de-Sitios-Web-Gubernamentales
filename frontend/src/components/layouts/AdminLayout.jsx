import { useState } from 'react';
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom';
import { useAuth, ROLES } from '../../contexts/AuthContext';
import {
  LayoutDashboard,
  Users,
  Building2,
  ClipboardCheck,
  BarChart3,
  Settings,
  LogOut,
  Menu,
  X,
  ChevronDown,
  User,
  Shield,
} from 'lucide-react';
import styles from './AdminLayout.module.css';

// Configuración de navegación por rol
const getNavItems = (role) => {
  const items = [
    {
      path: '/admin',
      icon: LayoutDashboard,
      label: 'Dashboard',
      roles: [ROLES.SUPERADMIN, ROLES.SECRETARY, ROLES.EVALUATOR, ROLES.ENTITY_USER],
      end: true,
    },
    {
      path: '/admin/evaluations',
      icon: ClipboardCheck,
      label: 'Evaluaciones',
      roles: [ROLES.SUPERADMIN, ROLES.SECRETARY, ROLES.EVALUATOR, ROLES.ENTITY_USER],
    },
    {
      path: '/admin/reports',
      icon: BarChart3,
      label: 'Reportes',
      roles: [ROLES.SUPERADMIN, ROLES.SECRETARY, ROLES.EVALUATOR, ROLES.ENTITY_USER],
    },
    {
      path: '/admin/institutions',
      icon: Building2,
      label: 'Instituciones',
      roles: [ROLES.SUPERADMIN, ROLES.SECRETARY],
    },
    {
      path: '/admin/users',
      icon: Users,
      label: 'Usuarios',
      roles: [ROLES.SUPERADMIN, ROLES.SECRETARY],
    },
    {
      path: '/admin/settings',
      icon: Settings,
      label: 'Configuración',
      roles: [ROLES.SUPERADMIN],
    },
  ];

  return items.filter(item => item.roles.includes(role));
};

// Mapeo de nombres de rol para mostrar
const ROLE_LABELS = {
  [ROLES.SUPERADMIN]: 'Super Administrador',
  [ROLES.SECRETARY]: 'Secretario',
  [ROLES.EVALUATOR]: 'Evaluador',
  [ROLES.ENTITY_USER]: 'Usuario de Entidad',
};

// Colores de badge por rol
const ROLE_COLORS = {
  [ROLES.SUPERADMIN]: styles.badgeSuperAdmin,
  [ROLES.SECRETARY]: styles.badgeSecretary,
  [ROLES.EVALUATOR]: styles.badgeEvaluator,
  [ROLES.ENTITY_USER]: styles.badgeEntityUser,
};

export default function AdminLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Páginas que deben ocupar todo el espacio sin padding
  const isFullPage = location.pathname.startsWith('/admin/evaluations') &&
    !location.pathname.match(/\/admin\/evaluations\/[^/]+$/);

  const navItems = getNavItems(user?.role);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const closeSidebar = () => setSidebarOpen(false);

  return (
    <div className={styles.layout}>
      {/* Overlay móvil */}
      {sidebarOpen && (
        <div className={styles.overlay} onClick={closeSidebar} />
      )}

      {/* Sidebar */}
      <aside className={`${styles.sidebar} ${sidebarOpen ? styles.sidebarOpen : ''}`}>
        <div className={styles.sidebarHeader}>
          <img src="/LOGO-AGETIC.png" alt="AGETIC" className={styles.logo} />
          <span className={styles.logoText}>GOB-BO</span>
          <button
            className={styles.closeSidebar}
            onClick={closeSidebar}
          >
            <X size={20} />
          </button>
        </div>

        <nav className={styles.nav}>
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.end}
              className={({ isActive }) =>
                `${styles.navItem} ${isActive ? styles.navItemActive : ''}`
              }
              onClick={closeSidebar}
            >
              <item.icon size={20} />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className={styles.sidebarFooter}>
          <div className={styles.userInfo}>
            <div className={styles.userAvatar}>
              <User size={20} />
            </div>
            <div className={styles.userDetails}>
              <span className={styles.userName}>
                {user?.name || 'Usuario'}
              </span>
              <span className={`${styles.roleBadge} ${ROLE_COLORS[user?.role] || ''}`}>
                {ROLE_LABELS[user?.role] || 'Sin rol'}
              </span>
            </div>
          </div>
        </div>
      </aside>

      {/* Contenido principal */}
      <div className={isFullPage ? styles.mainFull : styles.main}>
        {/* Header */}
        <header className={styles.header}>
          <button
            className={styles.menuButton}
            onClick={() => setSidebarOpen(true)}
          >
            <Menu size={24} />
          </button>

          <div className={styles.headerTitle}>
            Panel Administrativo
          </div>

          <div className={styles.headerActions}>
            <div className={styles.userMenu}>
              <button
                className={styles.userMenuButton}
                onClick={() => setUserMenuOpen(!userMenuOpen)}
              >
                <div className={styles.userMenuAvatar}>
                  <User size={18} />
                </div>
                <span className={styles.userMenuName}>
                  {user?.name || 'Usuario'}
                </span>
                <ChevronDown size={16} className={userMenuOpen ? styles.rotated : ''} />
              </button>

              {userMenuOpen && (
                <>
                  <div
                    className={styles.userMenuOverlay}
                    onClick={() => setUserMenuOpen(false)}
                  />
                  <div className={styles.userMenuDropdown}>
                    <div className={styles.userMenuHeader}>
                      <div className={styles.userMenuEmail}>
                        {user?.email}
                      </div>
                      <div className={`${styles.roleBadgeSmall} ${ROLE_COLORS[user?.role] || ''}`}>
                        <Shield size={12} />
                        {ROLE_LABELS[user?.role]}
                      </div>
                    </div>
                    <div className={styles.userMenuDivider} />
                    <NavLink
                      to="/admin/profile"
                      className={styles.userMenuItem}
                      onClick={() => setUserMenuOpen(false)}
                    >
                      <User size={16} />
                      Mi Perfil
                    </NavLink>
                    <button
                      onClick={handleLogout}
                      className={`${styles.userMenuItem} ${styles.logoutItem}`}
                    >
                      <LogOut size={16} />
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
