import { useState, useEffect, useCallback, useRef } from 'react';
import {
  User,
  Mail,
  Shield,
  ShieldAlert,
  Eye,
  EyeOff,
  Search,
  Plus,
  Edit2,
  Trash2,
  X,
  Loader,
  AlertCircle,
  CheckCircle,
  Building2,
  Save,
  Filter,
} from 'lucide-react';
import anime from 'animejs';
import { useAuth } from '../../contexts/AuthContext';
import userService from '../../services/userService';
import institutionService from '../../services/institutionService';
import styles from './Users.module.css';

// Componente Toast para notificaciones
function Toast({ message, type = 'success', onClose }) {
  useEffect(() => {
    const timer = setTimeout(onClose, 4000);
    return () => clearTimeout(timer);
  }, [onClose]);

  return (
    <div className={`${styles.toast} ${styles[`toast${type.charAt(0).toUpperCase() + type.slice(1)}`]}`}>
      {type === 'success' && <CheckCircle size={18} />}
      {type === 'error' && <AlertCircle size={18} />}
      <span>{message}</span>
      <button onClick={onClose} className={styles.toastClose}>
        <X size={16} />
      </button>
    </div>
  );
}

// Helper para obtener color del rol
function getRoleBadgeClass(role) {
  const roleMap = {
    superadmin: styles.roleSuperadmin,
    secretary: styles.roleSecretary,
    evaluator: styles.roleEvaluator,
    entity_user: styles.roleEntity,
  };
  return roleMap[role] || styles.roleDefault;
}

// Helper para obtener label del rol
function getRoleLabel(role) {
  const roleLabels = {
    superadmin: 'Superadmin',
    secretary: 'Secretario',
    evaluator: 'Evaluador',
    entity_user: 'Entidad',
  };
  return roleLabels[role] || role;
}

// ── Modal Confirmar Eliminar ──────────────────────────────────────────────────
function ConfirmDeleteModal({ isOpen, onClose, onConfirm, userName, deleting }) {
  if (!isOpen) return null;

  return (
    <div className={styles.modalOverlay} onClick={!deleting ? onClose : undefined}>
      <div className={styles.confirmModal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.confirmModalIcon}>
          <ShieldAlert size={32} />
        </div>
        <div className={styles.confirmModalContent}>
          <h2 className={styles.confirmModalTitle}>Eliminar Usuario</h2>
          <p className={styles.confirmModalMessage}>
            ¿Está seguro de eliminar al usuario{' '}
            <strong>"{userName}"</strong>?
          </p>
          <div className={styles.confirmModalWarning}>
            <p>Esta acción es <strong>irreversible</strong> y eliminará:</p>
            <ul>
              <li>Todos los datos del usuario</li>
              <li>Sus accesos al sistema</li>
              <li>Sus evaluaciones asociadas</li>
            </ul>
          </div>
        </div>
        <div className={styles.confirmModalFooter}>
          <button
            className={styles.btnSecondary}
            onClick={onClose}
            disabled={deleting}
          >
            Cancelar
          </button>
          <button
            className={styles.btnDanger}
            onClick={onConfirm}
            disabled={deleting}
          >
            {deleting ? (
              <><Loader size={16} className={styles.spinner} /> Eliminando...</>
            ) : (
              <><Trash2 size={16} /> Eliminar</>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

// Modal de Edición de Usuario
function UserModal({ isOpen, onClose, user, onSave }) {
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    role: 'evaluator',
    institution_id: null,
    is_active: true,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [institutions, setInstitutions] = useState([]);
  const [loadingInstitutions, setLoadingInstitutions] = useState(false);

  // Reset state when modal opens
  useEffect(() => {
    if (isOpen) {
      setSaving(false);
      setError('');
      if (user) {
        setFormData({
          full_name: user.full_name || '',
          email: user.email || '',
          role: user.role || 'evaluator',
          institution_id: user.institution_id || null,
          is_active: user.is_active ?? true,
        });
      }
    }
  }, [isOpen, user]);

  // Cargar instituciones cuando el rol es entity_user
  useEffect(() => {
    if (formData.role === 'entity_user' && institutions.length === 0) {
      setLoadingInstitutions(true);
      institutionService.getAll({ limit: 500 })
        .then((data) => setInstitutions(data.items || []))
        .catch((err) => console.error('Error cargando instituciones:', err))
        .finally(() => setLoadingInstitutions(false));
    }
  }, [formData.role, institutions.length]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => {
      const updated = {
        ...prev,
        [name]: type === 'checkbox' ? checked : value,
      };
      // Si cambia el rol y NO es entity_user, limpiar institution_id
      if (name === 'role' && value !== 'entity_user') {
        updated.institution_id = null;
      }
      return updated;
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');

    // Validar que entity_user tenga institución seleccionada
    if (formData.role === 'entity_user' && !formData.institution_id) {
      setError('Debe seleccionar una institución para usuarios de entidad');
      setSaving(false);
      return;
    }

    try {
      await onSave(formData);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Error al actualizar el usuario');
      setSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className={styles.modalOverlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.modalHeader}>
          <h2>Editar Usuario</h2>
          <button onClick={onClose} className={styles.closeBtn} disabled={saving}>
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className={styles.modalBody}>
            {error && (
              <div className={styles.errorAlert}>
                <AlertCircle size={18} />
                <span>{error}</span>
              </div>
            )}

            <div className={styles.formSection}>
              <h3 className={styles.formSectionTitle}>
                <User size={16} />
                Información del Usuario
              </h3>

              <div className={styles.formGroup}>
                <label htmlFor="full_name">Nombre Completo *</label>
                <input
                  type="text"
                  id="full_name"
                  name="full_name"
                  value={formData.full_name}
                  onChange={handleChange}
                  required
                  className={styles.input}
                  disabled={saving}
                />
              </div>

              <div className={styles.formGroup}>
                <label htmlFor="email">Email *</label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  required
                  className={styles.input}
                  disabled={saving}
                />
              </div>

              <div className={styles.formGroup}>
                <label htmlFor="role">Rol *</label>
                <select
                  id="role"
                  name="role"
                  value={formData.role}
                  onChange={handleChange}
                  required
                  className={styles.input}
                  disabled={saving}
                >
                  <option value="superadmin">Superadmin</option>
                  <option value="secretary">Secretario</option>
                  <option value="evaluator">Evaluador</option>
                  <option value="entity_user">Usuario de Entidad</option>
                </select>
              </div>

              {formData.role === 'entity_user' && (
                <div className={styles.formGroup}>
                  <label htmlFor="institution_id">
                    Institución *
                  </label>
                  {loadingInstitutions ? (
                    <div className={styles.loadingInline}>
                      <Loader size={16} className={styles.spinner} />
                      <span>Cargando instituciones...</span>
                    </div>
                  ) : (
                    <select
                      id="institution_id"
                      name="institution_id"
                      value={formData.institution_id || ''}
                      onChange={handleChange}
                      required
                      className={styles.input}
                      disabled={saving}
                    >
                      <option value="">-- Seleccionar institución --</option>
                      {institutions.map((inst) => (
                        <option key={inst.id} value={inst.id}>
                          {inst.name}
                        </option>
                      ))}
                    </select>
                  )}
                  {!formData.institution_id && !loadingInstitutions && (
                    <p className={styles.fieldWarning}>
                      Debe seleccionar una institución para usuarios de entidad
                    </p>
                  )}
                </div>
              )}

              <div className={styles.formGroup}>
                <label className={styles.checkboxLabel}>
                  <input
                    type="checkbox"
                    name="is_active"
                    checked={formData.is_active}
                    onChange={handleChange}
                    className={styles.checkbox}
                    disabled={saving}
                  />
                  <span>Usuario Activo</span>
                </label>
              </div>
            </div>
          </div>

          <div className={styles.modalFooter}>
            <button type="button" onClick={onClose} className={styles.btnSecondary} disabled={saving}>
              Cancelar
            </button>
            <button type="submit" className={styles.btnPrimary} disabled={saving}>
              {saving ? (
                <>
                  <Loader size={18} className={styles.spinner} />
                  Guardando...
                </>
              ) : (
                <>
                  <Save size={18} />
                  Guardar Cambios
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

const ROLE_FILTER_OPTIONS = [
  { value: 'all', label: 'Todos los roles' },
  { value: 'superadmin', label: 'Superadmin' },
  { value: 'secretary', label: 'Secretario' },
  { value: 'evaluator', label: 'Evaluador' },
  { value: 'entity_user', label: 'Usuario Entidad' },
];

// Componente principal
export default function Users() {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState('all');
  const [toast, setToast] = useState(null);
  const [editingUser, setEditingUser] = useState(null);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null); // { id, username }
  const [deleting, setDeleting] = useState(false);
  const tableRef = useRef(null);

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await userService.getAll({ search: searchQuery });
      setUsers(data.items || []);
    } catch (err) {
      setError('Error al cargar los usuarios');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [searchQuery]);

  // Filtrado por rol en el cliente (búsqueda ya se delega al backend)
  const filteredUsers = roleFilter === 'all'
    ? users
    : users.filter((u) => u.role === roleFilter);

  /**
   * Determina si el usuario actual puede eliminar al usuario objetivo.
   * - superadmin: puede eliminar a cualquiera (excepto a sí mismo)
   * - secretary: solo puede eliminar entity_user
   */
  const canDeleteUser = (targetUser) => {
    if (!currentUser) return false;
    if (targetUser.id === currentUser.id) return false;
    if (currentUser.role === 'superadmin') return true;
    if (currentUser.role === 'secretary' && targetUser.role === 'entity_user') return true;
    return false;
  };

  const handleDeleteUser = (userId, username) => {
    setDeleteTarget({ id: userId, username });
  };

  const handleConfirmDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await userService.remove(deleteTarget.id);
      setToast({ message: `Usuario "${deleteTarget.username}" eliminado exitosamente`, type: 'success' });
      setDeleteTarget(null);
      fetchUsers();
    } catch (err) {
      setToast({
        message: err.response?.data?.detail || 'Error al eliminar usuario',
        type: 'error',
      });
    } finally {
      setDeleting(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  // Debounce para la búsqueda
  useEffect(() => {
    const timer = setTimeout(() => {
      fetchUsers();
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Animación stagger para las filas de la tabla
  // Depende de filteredUsers (no solo de users) para re-animarse al cambiar el filtro de rol
  useEffect(() => {
    if (!loading && filteredUsers.length > 0 && tableRef.current) {
      const rows = tableRef.current.querySelectorAll('tr');
      anime({
        targets: rows,
        opacity: [0, 1],
        translateX: [-10, 0],
        delay: anime.stagger(25, { start: 50 }),
        duration: 350,
        easing: 'easeOutCubic',
      });
    }
  }, [filteredUsers, loading]);

  const handleSearchChange = (e) => {
    setSearchQuery(e.target.value);
  };

  const handleEditUser = (user) => {
    setEditingUser(user);
    setIsEditModalOpen(true);
  };

  const handleSaveUser = async (formData) => {
    // This throws if update fails, creating error in modal
    await userService.update(editingUser.id, formData);

    // If successful:
    setIsEditModalOpen(false);

    // Refresh list
    await fetchUsers();

    // Show toast
    setTimeout(() => {
      setToast({ message: 'Usuario actualizado correctamente', type: 'success' });
    }, 100);
  };

  return (
    <div className={styles.container}>
      {/* Toast */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}

      {/* Header */}
      <div className={styles.header}>
        <div className={styles.headerInfo}>
          <h1>
            <User size={28} />
            Usuarios
          </h1>
          <p>Gestión de usuarios internos del sistema</p>
        </div>
        <button
          onClick={() => {/* TODO: Abrir modal de creación */ }}
          className={styles.btnPrimary}
        >
          <Plus size={18} />
          Nuevo Usuario Interno
        </button>
      </div>

      {/* Barra de búsqueda y filtros */}
      <div className={styles.toolbar}>
        <div className={styles.searchBox}>
          <Search size={20} className={styles.searchIcon} />
          <input
            type="text"
            placeholder="Buscar por nombre o email..."
            value={searchQuery}
            onChange={handleSearchChange}
            className={styles.searchInput}
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className={styles.searchClear}
            >
              <X size={16} />
            </button>
          )}
        </div>
        <div className={styles.filterGroup}>
          <Filter size={16} className={styles.filterIcon} />
          <select
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
            className={styles.filterSelect}
            aria-label="Filtrar por rol"
          >
            {ROLE_FILTER_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Contenido */}
      <div className={styles.content}>
        {loading ? (
          <div className={styles.loading}>
            <Loader size={32} className={styles.spinner} />
            <span>Cargando usuarios...</span>
          </div>
        ) : error ? (
          <div className={styles.error}>
            <AlertCircle size={24} />
            <span>{error}</span>
            <button onClick={fetchUsers} className={styles.btnSecondary}>
              Reintentar
            </button>
          </div>
        ) : filteredUsers.length === 0 ? (
          <div className={styles.empty}>
            <User size={48} />
            <h3>
              {searchQuery || roleFilter !== 'all'
                ? 'No se encontraron usuarios'
                : 'No hay usuarios registrados'}
            </h3>
            <p>
              {searchQuery || roleFilter !== 'all'
                ? 'Intenta con otros criterios de búsqueda o filtro'
                : 'Crea el primer usuario para comenzar'}
            </p>
          </div>
        ) : (
          <>
            {/* Contador de resultados */}
            <div className={styles.resultsInfo}>
              <span>
                {filteredUsers.length} {filteredUsers.length === 1 ? 'usuario' : 'usuarios'}
                {searchQuery && ` que coinciden con "${searchQuery}"`}
                {roleFilter !== 'all' && ` · filtrado por rol`}
              </span>
            </div>

            {/* Tabla moderna */}
            <div className={styles.tableContainer}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>Usuario</th>
                    <th>Email</th>
                    <th>Rol</th>
                    <th>Institución</th>
                    <th>Estado</th>
                    <th>Acciones</th>
                  </tr>
                </thead>
                <tbody ref={tableRef}>
                  {filteredUsers.map((user) => (
                    <tr key={user.id}>
                      <td data-label="Usuario">
                        <div className={styles.userCell}>
                          <div className={styles.userAvatar}>
                            <User size={18} />
                          </div>
                          <div className={styles.userInfo}>
                            <span className={styles.userName}>{user.full_name || 'Sin nombre'}</span>
                            <span className={styles.userUsername}>@{user.username}</span>
                          </div>
                        </div>
                      </td>
                      <td data-label="Email">
                        <a href={`mailto:${user.email}`} className={styles.emailLink}>
                          <Mail size={14} />
                          {user.email}
                        </a>
                      </td>
                      <td data-label="Rol">
                        <span className={`${styles.roleBadge} ${getRoleBadgeClass(user.role)}`}>
                          <Shield size={12} />
                          {getRoleLabel(user.role)}
                        </span>
                      </td>
                      <td data-label="Institución">
                        {user.institution_name ? (
                          <span className={styles.institutionName}>
                            <Building2 size={14} />
                            {user.institution_name}
                          </span>
                        ) : (
                          <span className={styles.noInstitution}>-</span>
                        )}
                      </td>
                      <td data-label="Estado">
                        <span className={`${styles.statusBadge} ${user.is_active ? styles.statusActive : styles.statusInactive}`}>
                          {user.is_active ? (
                            <>
                              <Eye size={12} />
                              Activo
                            </>
                          ) : (
                            <>
                              <EyeOff size={12} />
                              Inactivo
                            </>
                          )}
                        </span>
                      </td>
                      <td data-label="Acciones">
                        <div className={styles.actionsCell}>
                          <button
                            onClick={() => handleEditUser(user)}
                            className={styles.actionBtn}
                            title="Editar usuario"
                          >
                            <Edit2 size={16} />
                          </button>
                          {canDeleteUser(user) && (
                            <button
                              onClick={() => handleDeleteUser(user.id, user.username)}
                              className={`${styles.actionBtn} ${styles.actionBtnDanger}`}
                              title="Eliminar usuario"
                            >
                              <Trash2 size={16} />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>

      {/* Modal de edición */}
      {isEditModalOpen && (
        <UserModal
          key={editingUser?.id}
          isOpen={isEditModalOpen}
          onClose={() => setIsEditModalOpen(false)}
          user={editingUser}
          onSave={handleSaveUser}
        />
      )}

      {/* Modal confirmar eliminación */}
      <ConfirmDeleteModal
        isOpen={!!deleteTarget}
        onClose={() => !deleting && setDeleteTarget(null)}
        onConfirm={handleConfirmDelete}
        userName={deleteTarget?.username || ''}
        deleting={deleting}
      />
    </div>
  );
}
