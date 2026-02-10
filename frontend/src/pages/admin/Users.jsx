import { useState, useEffect, useCallback, useRef } from 'react';
import {
  User,
  Mail,
  Shield,
  Eye,
  EyeOff,
  Search,
  Plus,
  Edit2,
  X,
  Loader,
  AlertCircle,
  CheckCircle,
  Building2,
  Save,
} from 'lucide-react';
import anime from 'animejs';
import userService from '../../services/userService';
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

// Modal de Edición de Usuario
function UserModal({ isOpen, onClose, user, onSave }) {
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    role: 'evaluator',
    is_active: true,
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

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
          is_active: user.is_active ?? true,
        });
      }
    }
  }, [isOpen, user]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');

    try {
      await onSave(formData);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Error al actualizar el usuario');
      // Only keep saving=true if we are NOT closing (which implies error)
      // But if onSave fails, we must reset saving
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
                  {/* Entity user cannot be changed from here typically, but kept for admin */}
                </select>
              </div>

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

// Componente principal
export default function Users() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [toast, setToast] = useState(null);
  const [editingUser, setEditingUser] = useState(null);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
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
  useEffect(() => {
    if (!loading && users.length > 0 && tableRef.current) {
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
  }, [users, loading]);

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

      {/* Barra de búsqueda */}
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
        ) : users.length === 0 ? (
          <div className={styles.empty}>
            <User size={48} />
            <h3>
              {searchQuery
                ? 'No se encontraron usuarios'
                : 'No hay usuarios registrados'}
            </h3>
            <p>
              {searchQuery
                ? 'Intenta con otros criterios de búsqueda'
                : 'Crea el primer usuario para comenzar'}
            </p>
          </div>
        ) : (
          <>
            {/* Contador de resultados */}
            <div className={styles.resultsInfo}>
              <span>
                {users.length} {users.length === 1 ? 'usuario' : 'usuarios'}
                {searchQuery && ` que coinciden con "${searchQuery}"`}
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
                  {users.map((user) => (
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
                        <button
                          onClick={() => handleEditUser(user)}
                          className={styles.actionBtn}
                          title="Editar usuario"
                        >
                          <Edit2 size={16} />
                        </button>
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
    </div>
  );
}
