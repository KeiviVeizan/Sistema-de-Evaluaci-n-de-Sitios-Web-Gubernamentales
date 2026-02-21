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
  KeyRound,
} from 'lucide-react';
import anime from 'animejs';
import { useAuth } from '../../contexts/AuthContext';
import userService from '../../services/userService';
import api from '../../services/api';
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

// Modal de Creación/Edición de Usuario
function UserModal({ isOpen, onClose, user, onSave, currentUser }) {
  const isEditMode = !!user;
  const [formData, setFormData] = useState({
    full_name: '',
    username: '',
    email: '',
    password: '',
    role: 'evaluator',
    position: '',
    institution_id: '',
    is_active: true,
    new_password: '',
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [institutions, setInstitutions] = useState([]);
  const [loadingInstitutions, setLoadingInstitutions] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  // Reset state when modal opens
  useEffect(() => {
    if (isOpen) {
      setSaving(false);
      setError('');
      setShowPassword(false);
      if (user) {
        setFormData({
          full_name: user.full_name || '',
          username: user.username || '',
          email: user.email || '',
          password: '',
          role: user.role || 'evaluator',
          position: user.position || '',
          institution_id: user.institution_id || '',
          is_active: user.is_active ?? true,
          new_password: '',
        });
      } else {
        setFormData({
          full_name: '',
          username: '',
          email: '',
          password: '',
          role: 'evaluator',
          position: '',
          institution_id: '',
          is_active: true,
          new_password: '',
        });
      }
    }
  }, [isOpen, user]);

  // Cargar instituciones
  useEffect(() => {
    if (isOpen && institutions.length === 0) {
      setLoadingInstitutions(true);
      api.get('/admin/institutions-list')
        .then((res) => setInstitutions(res.data || []))
        .catch((err) => console.error('Error cargando instituciones:', err))
        .finally(() => setLoadingInstitutions(false));
    }
  }, [isOpen, institutions.length]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => {
      const updated = {
        ...prev,
        [name]: type === 'checkbox' ? checked : value,
      };
      if (name === 'role' && value !== 'entity_user') {
        updated.institution_id = '';
      }
      return updated;
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');

    if (formData.role === 'entity_user' && !formData.institution_id) {
      setError('Debe seleccionar una institución para usuarios de entidad');
      setSaving(false);
      return;
    }

    try {
      if (isEditMode) {
        // Editar: enviar solo campos relevantes
        const payload = {
          full_name: formData.full_name,
          username: formData.username,
          email: formData.email,
          role: formData.role,
          position: formData.position || null,
          institution_id: formData.institution_id ? parseInt(formData.institution_id) : null,
          is_active: formData.is_active,
        };
        if (formData.new_password) {
          payload.new_password = formData.new_password;
        }
        await onSave(payload);
      } else {
        // Crear: sin contraseña, se genera automáticamente en backend
        const payload = {
          full_name: formData.full_name,
          username: formData.username,
          email: formData.email,
          role: formData.role,
          position: formData.position || null,
          institution_id: formData.institution_id ? parseInt(formData.institution_id) : null,
        };
        await onSave(payload);
      }
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || `Error al ${isEditMode ? 'actualizar' : 'crear'} el usuario`);
      setSaving(false);
    }
  };

  if (!isOpen) return null;

  const canAssignHighRoles = currentUser?.role === 'superadmin';

  return (
    <div className={styles.modalOverlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.modalHeader}>
          <h2>{isEditMode ? 'Editar Usuario' : 'Nuevo Usuario Interno'}</h2>
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

              <div className={styles.formRow}>
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
                    placeholder="Ej: Juan Pérez"
                  />
                </div>

                <div className={styles.formGroup}>
                  <label htmlFor="username">Nombre de Usuario *</label>
                  <input
                    type="text"
                    id="username"
                    name="username"
                    value={formData.username}
                    onChange={handleChange}
                    required
                    className={styles.input}
                    disabled={saving}
                    placeholder="Ej: jperez"
                  />
                  {isEditMode && (
                    <p className={styles.fieldHint}>Este es el @{formData.username} que ves en la lista</p>
                  )}
                </div>
              </div>

              <div className={styles.formRow}>
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
                    placeholder="Ej: jperez@gmail.com"
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
                    {canAssignHighRoles && (
                      <>
                        <option value="superadmin">Superadmin</option>
                        <option value="secretary">Secretario</option>
                      </>
                    )}
                    <option value="evaluator">Evaluador</option>
                    <option value="entity_user">Usuario de Entidad</option>
                  </select>
                </div>
              </div>

              <div className={styles.formRow}>
                <div className={styles.formGroup}>
                  <label htmlFor="position">Cargo</label>
                  <input
                    type="text"
                    id="position"
                    name="position"
                    value={formData.position}
                    onChange={handleChange}
                    className={styles.input}
                    disabled={saving}
                    placeholder="Ej: Jefe de Sistemas"
                  />
                </div>

                {isEditMode && (
                  <div className={styles.formGroup}>
                    <label htmlFor="is_active">Estado</label>
                    <select
                      id="is_active"
                      name="is_active"
                      value={formData.is_active.toString()}
                      onChange={(e) => setFormData((prev) => ({ ...prev, is_active: e.target.value === 'true' }))}
                      className={styles.input}
                      disabled={saving}
                    >
                      <option value="true">Activo</option>
                      <option value="false">Inactivo</option>
                    </select>
                  </div>
                )}
              </div>

              {formData.role === 'entity_user' && (
                <div className={styles.formGroup}>
                  <label htmlFor="institution_id">
                    Institución {formData.role === 'entity_user' ? '*' : ''}
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
                      required={formData.role === 'entity_user'}
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
                </div>
              )}
            </div>

            {/* Sección de contraseña - solo en edición */}
            {isEditMode && (
              <div className={styles.formSection}>
                <h3 className={styles.formSectionTitle}>
                  <KeyRound size={16} />
                  Cambiar Contraseña
                </h3>

                <div className={styles.formGroup}>
                  <label htmlFor="new_password">Nueva Contraseña (dejar vacío para no cambiar)</label>
                  <div className={styles.passwordInputWrapper}>
                    <input
                      type={showPassword ? 'text' : 'password'}
                      id="new_password"
                      name="new_password"
                      value={formData.new_password}
                      onChange={handleChange}
                      className={styles.passwordField}
                      disabled={saving}
                      placeholder="Dejar vacío para mantener actual"
                      minLength={8}
                    />
                    <button
                      type="button"
                      className={styles.passwordToggle}
                      onClick={() => setShowPassword(!showPassword)}
                      tabIndex={-1}
                    >
                      {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Info: contraseña auto-generada en creación */}
            {!isEditMode && (
              <div className={styles.infoAlert}>
                <KeyRound size={16} />
                <span>Se generará una contraseña temporal automáticamente y se enviará al email del usuario.</span>
              </div>
            )}
          </div>

          <div className={styles.modalFooter}>
            <button type="button" onClick={onClose} className={styles.btnSecondary} disabled={saving}>
              Cancelar
            </button>
            <button type="submit" className={styles.btnPrimary} disabled={saving}>
              {saving ? (
                <>
                  <Loader size={18} className={styles.spinner} />
                  {isEditMode ? 'Guardando...' : 'Creando...'}
                </>
              ) : (
                <>
                  <Save size={18} />
                  {isEditMode ? 'Guardar Cambios' : 'Crear Usuario'}
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

const ROLE_FILTER_OPTIONS_ALL = [
  { value: 'all', label: 'Todos los roles' },
  { value: 'superadmin', label: 'Superadmin' },
  { value: 'secretary', label: 'Secretario' },
  { value: 'evaluator', label: 'Evaluador' },
  { value: 'entity_user', label: 'Usuario Entidad' },
];

const ROLE_FILTER_OPTIONS_SECRETARY = [
  { value: 'all', label: 'Todos los roles' },
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
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
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

  // Secretary solo ve evaluadores y entidades
  const visibleUsers = currentUser?.role === 'secretary'
    ? users.filter((u) => u.role === 'evaluator' || u.role === 'entity_user')
    : users;

  // Filtrado por rol en el cliente (búsqueda ya se delega al backend)
  const filteredUsers = roleFilter === 'all'
    ? visibleUsers
    : visibleUsers.filter((u) => u.role === roleFilter);

  const roleFilterOptions = currentUser?.role === 'secretary'
    ? ROLE_FILTER_OPTIONS_SECRETARY
    : ROLE_FILTER_OPTIONS_ALL;

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

  /**
   * Determina si el usuario actual puede editar al usuario objetivo.
   * - superadmin: puede editar a cualquiera
   * - secretary: solo puede editar evaluator y entity_user
   */
  const canEditUser = (targetUser) => {
    if (!currentUser) return false;
    if (currentUser.role === 'superadmin') return true;
    if (currentUser.role === 'secretary' && (targetUser.role === 'entity_user' || targetUser.role === 'evaluator')) return true;
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

  const handleCreateUser = async (formData) => {
    await userService.create(formData);
    setIsCreateModalOpen(false);
    await fetchUsers();
    setTimeout(() => {
      setToast({ message: 'Usuario creado exitosamente', type: 'success' });
    }, 100);
  };

  const handleSaveUser = async (formData) => {
    await userService.update(editingUser.id, formData);
    setIsEditModalOpen(false);
    await fetchUsers();
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
          onClick={() => setIsCreateModalOpen(true)}
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
            {roleFilterOptions.map((opt) => (
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
                          {canEditUser(user) && (
                            <button
                              onClick={() => handleEditUser(user)}
                              className={styles.actionBtn}
                              title="Editar usuario"
                            >
                              <Edit2 size={16} />
                            </button>
                          )}
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

      {/* Modal de creación */}
      {isCreateModalOpen && (
        <UserModal
          key="create-modal"
          isOpen={isCreateModalOpen}
          onClose={() => setIsCreateModalOpen(false)}
          user={null}
          onSave={handleCreateUser}
          currentUser={currentUser}
        />
      )}

      {/* Modal de edición */}
      {isEditModalOpen && (
        <UserModal
          key={editingUser?.id}
          isOpen={isEditModalOpen}
          onClose={() => setIsEditModalOpen(false)}
          user={editingUser}
          onSave={handleSaveUser}
          currentUser={currentUser}
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
