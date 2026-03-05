import { useState, useEffect, useRef } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { ROLES, ROLE_LABELS } from '../../contexts/AuthContext';
import {
  LayoutDashboard,
  Building2,
  Users,
  FileText,
  BarChart3,
  CheckCircle2,
  Settings,
  LogOut,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  X,
  UserPlus,
  List,
  PlusCircle,
  FileEdit,
  Eye,
} from 'lucide-react';
import styles from './ModernSidebar.module.css';

// Estructura de menú con soporte para submenús
const MENU_STRUCTURE = {
  [ROLES.SUPERADMIN]: [
    {
      id: 'dashboard',
      path: '/admin/dashboard',
      icon: LayoutDashboard,
      label: 'Inicio',
    },
    {
      id: 'institutions',
      icon: Building2,
      label: 'Gestión de Instituciones',
      children: [
        {
          path: '/admin/institutions',
          icon: List,
          label: 'Lista de Instituciones',
        },
        {
          path: '/admin/institutions/new',
          icon: PlusCircle,
          label: 'Nueva Institución',
        },
      ],
    },
    {
      id: 'users',
      icon: Users,
      label: 'Gestión de Usuarios',
      children: [
        {
          path: '/admin/users',
          icon: List,
          label: 'Lista de Usuarios/ Editar Usuarios',
        },
        {
          path: '/admin/users/new',
          icon: UserPlus,
          label: 'Crear Nuevo Usuario',
        },
      ],
    },
    {
      id: 'evaluations',
      path: '/admin/evaluations',
      icon: FileEdit,
      label: 'Realizar Evaluación',
    },
    {
      id: 'followups',
      icon: CheckCircle2,
      label: 'Seguimientos',
      children: [
        {
          path: '/admin/followups',
          icon: Eye,
          label: 'Todos los Seguimientos',
        },
      ],
    },
    {
      id: 'reports',
      icon: BarChart3,
      label: 'Informes y Reportes',
      children: [
        {
          path: '/admin/reports',
          icon: FileText,
          label: 'Ver Reportes',
        },
      ],
    },
  ],
  [ROLES.SECRETARY]: [
    {
      id: 'dashboard',
      path: '/admin/dashboard',
      icon: LayoutDashboard,
      label: 'Inicio',
    },
    {
      id: 'institutions',
      icon: Building2,
      label: 'Gestión de Instituciones',
      children: [
        {
          path: '/admin/institutions',
          icon: List,
          label: 'Lista de Instituciones',
        },
        {
          path: '/admin/institutions/new',
          icon: PlusCircle,
          label: 'Nueva Institución',
        },
      ],
    },
    {
      id: 'users',
      icon: Users,
      label: 'Gestión de Usuarios',
      children: [
        {
          path: '/admin/users',
          icon: List,
          label: 'Lista de Usuarios',
        },
        {
          path: '/admin/users/new',
          icon: UserPlus,
          label: 'Crear Nuevo Usuario',
        },
      ],
    },
    {
      id: 'followups',
      icon: CheckCircle2,
      label: 'Seguimientos',
      children: [
        {
          path: '/admin/secretary/followups',
          icon: List,
          label: 'Mis Seguimientos',
        },
      ],
    },
  ],
  [ROLES.EVALUATOR]: [
    {
      id: 'dashboard',
      path: '/admin/dashboard',
      icon: LayoutDashboard,
      label: 'Inicio',
    },
    {
      id: 'institutions',
      path: '/admin/institutions',
      icon: Building2,
      label: 'Instituciones',
    },
    {
      id: 'my-evaluations',
      path: '/admin/evaluator/my-evaluations',
      icon: List,
      label: 'Mis Evaluaciones',
    },
    {
      id: 'evaluations',
      path: '/admin/evaluations',
      icon: FileEdit,
      label: 'Realizar Evaluación',
    },
    {
      id: 'followups',
      icon: CheckCircle2,
      label: 'Seguimientos',
      children: [
        {
          path: '/admin/evaluator/followups',
          icon: List,
          label: 'Mis Seguimientos',
        },
      ],
    },
  ],
  [ROLES.ENTITY_USER]: [
    {
      id: 'dashboard',
      path: '/admin/dashboard',
      icon: LayoutDashboard,
      label: 'Inicio',
    },
    {
      id: 'my-evaluations',
      path: '/admin/my-evaluations',
      icon: FileText,
      label: 'Mis Evaluaciones',
    },
    {
      id: 'followups',
      icon: CheckCircle2,
      label: 'Seguimientos',
      children: [
        {
          path: '/admin/my-followups',
          icon: List,
          label: 'Mis Seguimientos',
        },
      ],
    },
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
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [openMenus, setOpenMenus] = useState({});
  const [hoveredItem, setHoveredItem] = useState(null);
  const [tooltipPosition, setTooltipPosition] = useState({ top: 0 });
  const closeTimeoutRef = useRef(null);

  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < 768);
    check();
    window.addEventListener('resize', check);
    return () => window.removeEventListener('resize', check);
  }, []);

  // Auto-expandir menús basado en la ruta actual
  useEffect(() => {
    const currentMenuItems = MENU_STRUCTURE[user?.role] || [];
    const newOpenMenus = {};

    currentMenuItems.forEach((item) => {
      if (item.children) {
        const isActive = item.children.some(child =>
          location.pathname.startsWith(child.path)
        );
        if (isActive) {
          newOpenMenus[item.id] = true;
        }
      }
    });

    setOpenMenus(newOpenMenus);
  }, [location.pathname, user?.role]);

  const handleToggle = () => {
    const next = !collapsed;
    setCollapsed(next);
    if (onCollapse) onCollapse(next);
  };

  const handleNavClick = () => {
    if (isMobile && onMobileClose) onMobileClose();
  };

  const toggleSubmenu = (menuId) => {
    setOpenMenus(prev => ({
      ...prev,
      [menuId]: !prev[menuId]
    }));
  };

  const handleMouseEnter = (event, itemId) => {
    if (!collapsed || isMobile) return;

    // Cancelar cualquier timeout pendiente cuando el mouse entra
    if (closeTimeoutRef.current) {
      clearTimeout(closeTimeoutRef.current);
      closeTimeoutRef.current = null;
    }

    const rect = event.currentTarget.getBoundingClientRect();
    setTooltipPosition({ top: rect.top + rect.height / 2 });
    setHoveredItem(itemId);
  };

  const handleMouseLeave = () => {
    // Cancelar cualquier timeout anterior
    if (closeTimeoutRef.current) {
      clearTimeout(closeTimeoutRef.current);
    }
    // Delay generoso para permitir que el mouse se mueva al tooltip
    closeTimeoutRef.current = setTimeout(() => {
      setHoveredItem(null);
      closeTimeoutRef.current = null;
    }, 500);
  };

  const handleTooltipEnter = () => {
    // Cancelar el cierre del tooltip cuando el mouse entra
    if (closeTimeoutRef.current) {
      clearTimeout(closeTimeoutRef.current);
      closeTimeoutRef.current = null;
    }
  };

  const handleTooltipLeave = () => {
    // Cerrar inmediatamente cuando el mouse sale del tooltip
    if (closeTimeoutRef.current) {
      clearTimeout(closeTimeoutRef.current);
    }
    setHoveredItem(null);
  };

  // Obtener items del menú según el rol del usuario
  const currentMenuItems = MENU_STRUCTURE[user?.role] || [];

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
          {currentMenuItems.map((item) => {
            const hasChildren = item.children && item.children.length > 0;
            const isOpen = openMenus[item.id];
            const isActiveParent = hasChildren && item.children.some(child =>
              location.pathname.startsWith(child.path)
            );

            // Item sin hijos (link directo)
            if (!hasChildren) {
              return (
                <div
                  key={item.id}
                  className={styles.navItemWrapper}
                  onMouseEnter={(e) => handleMouseEnter(e, item.id)}
                  onMouseLeave={handleMouseLeave}
                >
                  <NavLink
                    to={item.path}
                    onClick={handleNavClick}
                    className={({ isActive }) =>
                      `${styles.navItem} ${isActive ? styles.active : ''}`
                    }
                  >
                    <span className={styles.navIcon}>
                      <item.icon size={22} />
                    </span>
                    {showLabels && (
                      <span className={styles.navLabel}>{item.label}</span>
                    )}
                  </NavLink>
                  {!isMobile && collapsed && hoveredItem === item.id && (
                    <div
                      className={styles.tooltip}
                      style={{ top: `${tooltipPosition.top}px` }}
                      onMouseEnter={handleTooltipEnter}
                      onMouseLeave={handleTooltipLeave}
                    >
                      {item.label}
                    </div>
                  )}
                </div>
              );
            }

            // Item con hijos (menú desplegable)
            return (
              <div
                key={item.id}
                className={styles.menuGroup}
                onMouseEnter={(e) => handleMouseEnter(e, item.id)}
                onMouseLeave={handleMouseLeave}
              >
                <button
                  className={`${styles.navItem} ${styles.parentItem} ${isActiveParent ? styles.active : ''}`}
                  onClick={() => toggleSubmenu(item.id)}
                >
                  <span className={styles.navIcon}>
                    <item.icon size={22} />
                  </span>
                  {showLabels && (
                    <>
                      <span className={styles.navLabel}>{item.label}</span>
                      <span className={styles.chevronIcon}>
                        {isOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                      </span>
                    </>
                  )}
                </button>

                {/* Submenú normal (expandido) */}
                {isOpen && showLabels && (
                  <div className={styles.submenu}>
                    {item.children.map((child) => (
                      <NavLink
                        key={child.path}
                        to={child.path}
                        onClick={handleNavClick}
                        className={({ isActive }) =>
                          `${styles.submenuItem} ${isActive ? styles.active : ''}`
                        }
                      >
                        <span className={styles.submenuIcon}>
                          <child.icon size={18} />
                        </span>
                        <span className={styles.submenuLabel}>{child.label}</span>
                      </NavLink>
                    ))}
                  </div>
                )}

                {/* Tooltip flotante con submenú (colapsado) */}
                {!isMobile && collapsed && hoveredItem === item.id && (
                  <div
                    className={styles.tooltipMenu}
                    style={{ top: `${tooltipPosition.top}px` }}
                    onMouseEnter={handleTooltipEnter}
                    onMouseLeave={handleTooltipLeave}
                  >
                    <div className={styles.tooltipMenuTitle}>{item.label}</div>
                    <div className={styles.tooltipMenuItems}>
                      {item.children.map((child) => (
                        <NavLink
                          key={child.path}
                          to={child.path}
                          onClick={handleNavClick}
                          className={({ isActive }) =>
                            `${styles.tooltipMenuItem} ${isActive ? styles.active : ''}`
                          }
                        >
                          <child.icon size={16} />
                          <span>{child.label}</span>
                        </NavLink>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </nav>

        {/* Footer: perfil y logout */}
        <div className={styles.footer}>
          <div className={styles.divider} />

          {showLabels && user && (
            <div className={styles.userInfo}>
              <div className={styles.userAvatar}>
                {user.full_name?.charAt(0).toUpperCase() || user.username?.charAt(0).toUpperCase() || 'U'}
              </div>
              <div className={styles.userDetails}>
                <span className={styles.userName}>{user.full_name || user.username || 'Usuario'}</span>
                <span className={styles.userRole}>{ROLE_LABELS[user.role] || user.role}</span>
              </div>
            </div>
          )}

          <div
            className={styles.navItemWrapper}
            onMouseEnter={(e) => handleMouseEnter(e, 'profile')}
            onMouseLeave={handleMouseLeave}
          >
            <NavLink
              to="/admin/profile"
              onClick={handleNavClick}
              className={({ isActive }) =>
                `${styles.navItem} ${isActive ? styles.active : ''}`
              }
            >
              <span className={styles.navIcon}>
                <Settings size={22} />
              </span>
              {showLabels && <span className={styles.navLabel}>Mi Perfil</span>}
            </NavLink>
            {!isMobile && collapsed && hoveredItem === 'profile' && (
              <div
                className={styles.tooltip}
                style={{ top: `${tooltipPosition.top}px` }}
                onMouseEnter={handleTooltipEnter}
                onMouseLeave={handleTooltipLeave}
              >
                Mi Perfil
              </div>
            )}
          </div>

          <div
            className={styles.navItemWrapper}
            onMouseEnter={(e) => handleMouseEnter(e, 'logout')}
            onMouseLeave={handleMouseLeave}
          >
            <button
              className={`${styles.navItem} ${styles.logoutBtn}`}
              onClick={() => {
                handleNavClick();
                logout();
              }}
            >
              <span className={styles.navIcon}>
                <LogOut size={22} />
              </span>
              {showLabels && <span className={styles.navLabel}>Cerrar Sesión</span>}
            </button>
            {!isMobile && collapsed && hoveredItem === 'logout' && (
              <div
                className={styles.tooltip}
                style={{ top: `${tooltipPosition.top}px` }}
                onMouseEnter={handleTooltipEnter}
                onMouseLeave={handleTooltipLeave}
              >
                Cerrar Sesión
              </div>
            )}
          </div>
        </div>
      </aside>
    </>
  );
}

export default ModernSidebar;
