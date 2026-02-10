import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  Building2,
  ArrowLeft,
  ExternalLink,
  User,
  Mail,
  Briefcase,
  Calendar,
  FileText,
  Play,
  Loader,
  AlertCircle,
  CheckCircle,
  Clock,
  XCircle,
  TrendingUp,
  Eye,
  EyeOff,
  BarChart3,
  Edit2,
  X,
  Trash2,
  Check,
  Save,
  ShieldAlert,
} from 'lucide-react';
import institutionService from '../../services/institutionService';
import styles from './InstitutionDetail.module.css';

// Helper para formatear fechas
function formatDate(dateString) {
  if (!dateString) return '-';
  return new Date(dateString).toLocaleDateString('es-BO', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

// Helper para formatear fecha y hora
function formatDateTime(dateString) {
  if (!dateString) return '-';
  return new Date(dateString).toLocaleDateString('es-BO', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

// Componente para mostrar el estado de una evaluación
function EvaluationStatusBadge({ status }) {
  const config = {
    completed: { icon: CheckCircle, label: 'Completada', className: styles.statusCompleted },
    in_progress: { icon: Clock, label: 'En progreso', className: styles.statusInProgress },
    pending: { icon: Clock, label: 'Pendiente', className: styles.statusPending },
    failed: { icon: XCircle, label: 'Fallida', className: styles.statusFailed },
  };

  const { icon: Icon, label, className } = config[status] || config.pending;

  return (
    <span className={`${styles.statusBadge} ${className}`}>
      <Icon size={14} />
      {label}
    </span>
  );
}

// Componente para mostrar el puntaje
function ScoreDisplay({ score, label }) {
  const getScoreColor = (score) => {
    if (score >= 80) return styles.scoreHigh;
    if (score >= 60) return styles.scoreMedium;
    return styles.scoreLow;
  };

  return (
    <div className={styles.scoreItem}>
      <span className={styles.scoreLabel}>{label}</span>
      <span className={`${styles.scoreValue} ${score !== null ? getScoreColor(score) : ''}`}>
        {score !== null ? `${score.toFixed(1)}%` : '-'}
      </span>
    </div>
  );
}

// Componente Tarjeta del Responsable
function ResponsibleCard({ responsible, institution }) {
  if (!responsible) {
    return (
      <div className={styles.responsibleCard}>
        <div className={styles.responsibleEmpty}>
          <User size={24} />
          <span>Sin responsable asignado</span>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.responsibleCard}>
      <div className={styles.responsibleHeader}>
        <div className={styles.responsibleAvatar}>
          <User size={24} />
        </div>
        <div className={styles.responsibleInfo}>
          <h4>{responsible.full_name || 'Sin nombre'}</h4>
          <span className={`${styles.responsibleStatus} ${responsible.is_active ? styles.active : styles.inactive}`}>
            {responsible.is_active ? (
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
        </div>
      </div>
      <div className={styles.responsibleDetails}>
        {responsible?.position && (
          <div className={styles.responsibleDetail}>
            <Briefcase size={16} />
            <span>{responsible.position}</span>
          </div>
        )}
        <div className={styles.responsibleDetail}>
          <Mail size={16} />
          <a href={`mailto:${responsible.email}`}>{responsible.email}</a>
        </div>
      </div>
    </div>
  );
}

// Componente Estado Vacío de Evaluaciones
function EmptyEvaluations({ institutionId }) {
  return (
    <div className={styles.emptyState}>
      <div className={styles.emptyIcon}>
        <BarChart3 size={48} />
      </div>
      <h3>Aún no se realizaron evaluaciones</h3>
      <p>Esta institución no cuenta con un historial de evaluaciones. Realiza la primera evaluación para comenzar a obtener métricas de cumplimiento de estándares.</p>
      <Link to={`/admin/evaluations/new?institution=${institutionId}`} className={styles.btnPrimary}>
        <Play size={18} />
        Realizar Primera Evaluación
      </Link>
    </div>
  );
}

// Componente Lista de Evaluaciones
function EvaluationsList({ evaluations }) {
  return (
    <div className={styles.evaluationsList}>
      {evaluations.map((evaluation) => (
        <div key={evaluation.id} className={styles.evaluationItem}>
          <div className={styles.evaluationHeader}>
            <div className={styles.evaluationDate}>
              <Calendar size={16} />
              <span>{formatDateTime(evaluation.started_at)}</span>
            </div>
            <EvaluationStatusBadge status={evaluation.status} />
          </div>

          {evaluation.status === 'completed' && (
            <div className={styles.evaluationScores}>
              <div className={styles.scoreMain}>
                <TrendingUp size={20} />
                <span className={styles.scoreMainValue}>
                  {evaluation.score_total?.toFixed(1) || '-'}%
                </span>
                <span className={styles.scoreMainLabel}>Puntaje Global</span>
              </div>
              <div className={styles.scoresGrid}>
                <ScoreDisplay score={evaluation.score_digital_sovereignty} label="Soberanía Digital" />
                <ScoreDisplay score={evaluation.score_accessibility} label="Accesibilidad" />
                <ScoreDisplay score={evaluation.score_usability} label="Usabilidad" />
                <ScoreDisplay score={evaluation.score_semantic_web} label="Web Semántica" />
              </div>
            </div>
          )}

          <div className={styles.evaluationActions}>
            <Link to={`/admin/evaluations/${evaluation.id}`} className={styles.btnOutline}>
              <FileText size={16} />
              Ver Reporte
            </Link>
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Modal Confirmar Eliminar ──────────────────────────────────────────────────
function ConfirmDeleteModal({ isOpen, onClose, onConfirm, institutionName, deleting }) {
  if (!isOpen) return null;

  return (
    <div className={styles.modalOverlay} onClick={!deleting ? onClose : undefined}>
      <div className={styles.confirmModal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.confirmModalIcon}>
          <ShieldAlert size={32} />
        </div>
        <div className={styles.confirmModalContent}>
          <h2 className={styles.confirmModalTitle}>Eliminar Institución</h2>
          <p className={styles.confirmModalMessage}>
            ¿Está seguro de eliminar la institución{' '}
            <strong>"{institutionName}"</strong>?
          </p>
          <div className={styles.confirmModalWarning}>
            <p>Esta acción es <strong>irreversible</strong> y eliminará:</p>
            <ul>
              <li>Todos los datos de la institución</li>
              <li>Usuarios asociados</li>
              <li>Evaluaciones realizadas</li>
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

// Componente Modal de Edición
function EditModal({ isOpen, onClose, institution, responsible, onSave }) {
  const [formData, setFormData] = useState({
    name: '',
    domain: '',
    is_active: true,
    contact_name: '',
    contact_email: '',
    contact_position: '',
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  // Use isOpen as dependency to reset when opening
  useEffect(() => {
    if (isOpen && institution) {
      setFormData({
        name: institution.name || '',
        domain: institution.domain || '',
        is_active: institution.is_active ?? true,
        contact_name: responsible?.full_name || '',
        contact_email: responsible?.email || '',
        contact_position: responsible?.position || '',
      });
      setError('');
      setSaving(false);
    }
  }, [isOpen, institution, responsible]);

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
      setError(err.response?.data?.detail || 'Error al actualizar la institución');
      console.error(err);
      setSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className={styles.modalOverlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.modalHeader}>
          <h2>Editar Institución</h2>
          <button onClick={onClose} className={styles.closeBtn} disabled={saving}>
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className={styles.modalForm}>
          <div className={styles.modalBody}>
            {error && (
              <div className={styles.errorAlert}>
                <AlertCircle size={18} />
                <span>{error}</span>
              </div>
            )}

            <div className={styles.formSection}>
              <h3 className={styles.formSectionTitle}>
                <Building2 size={16} />
                Datos de la Institución
              </h3>

              <div className={styles.formGroup}>
                <label htmlFor="name">Nombre de la Entidad *</label>
                <input
                  type="text"
                  id="name"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  required
                  minLength={3}
                  maxLength={255}
                  placeholder="Ej: Ministerio de Educación"
                  className={styles.input}
                  disabled={saving}
                />
              </div>

              <div className={styles.formGroup}>
                <label htmlFor="domain">Dominio Web *</label>
                <input
                  type="text"
                  id="domain"
                  name="domain"
                  value={formData.domain}
                  onChange={handleChange}
                  required
                  minLength={5}
                  maxLength={255}
                  placeholder="ejemplo.gob.bo"
                  className={styles.input}
                  disabled={saving}
                />
              </div>

              <div className={styles.checkboxGroup}>
                <label className={styles.checkboxLabel}>
                  <input
                    type="checkbox"
                    name="is_active"
                    checked={formData.is_active}
                    onChange={handleChange}
                    className={styles.checkbox}
                    disabled={saving}
                  />
                  <span className={styles.checkboxText}>Entidad Activa</span>
                </label>
                <span className={styles.inputHint}>
                  Las entidades inactivas no podrán acceder al sistema
                </span>
              </div>
            </div>

            <div className={styles.formSection}>
              <h3 className={styles.formSectionTitle}>
                <User size={16} />
                Datos del Responsable
              </h3>

              <div className={styles.formGroup}>
                <label htmlFor="contact_name">Nombre Completo</label>
                <input
                  type="text"
                  id="contact_name"
                  name="contact_name"
                  value={formData.contact_name}
                  onChange={handleChange}
                  minLength={3}
                  maxLength={100}
                  placeholder="Ej: Juan Pérez Mamani"
                  className={styles.input}
                  disabled={saving}
                />
              </div>

              <div className={styles.formGroup}>
                <label htmlFor="contact_email">Email</label>
                <input
                  type="email"
                  id="contact_email"
                  name="contact_email"
                  value={formData.contact_email}
                  onChange={handleChange}
                  placeholder="ejemplo@institucion.gob.bo"
                  className={styles.input}
                  disabled={saving}
                />
              </div>

              <div className={styles.formGroup}>
                <label htmlFor="contact_position">Cargo</label>
                <input
                  type="text"
                  id="contact_position"
                  name="contact_position"
                  value={formData.contact_position}
                  onChange={handleChange}
                  maxLength={100}
                  placeholder="Ej: Director de Tecnología"
                  className={styles.input}
                  disabled={saving}
                />
              </div>
            </div>
          </div>

          <div className={styles.modalFooter}>
            <button
              type="button"
              onClick={onClose}
              className={styles.btnSecondary}
              disabled={saving}
            >
              Cancelar
            </button>
            <button
              type="submit"
              className={styles.btnPrimary}
              disabled={saving}
            >
              {saving ? (
                <>
                  <Loader size={18} className={styles.spinner} />
                  Guardando...
                </>
              ) : (
                <>
                  <Check size={18} />
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

// Componente Principal
export default function InstitutionDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [ashEffect, setAshEffect] = useState(false);
  const [toast, setToast] = useState(null);

  const handleDeleteFromPage = async () => {
    setDeleting(true);
    try {
      await institutionService.delete(id);
      setIsDeleteModalOpen(false);
      // Activar animación de cenizas en toda la página
      setAshEffect(true);
      // Navegar después de que termine la animación
      setTimeout(() => {
        navigate('/admin/institutions');
      }, 1400);
    } catch (err) {
      setIsDeleteModalOpen(false);
      setDeleting(false);
      setToast({ message: 'Error al eliminar: ' + (err.response?.data?.detail || err.message), type: 'error' });
    }
  };

  useEffect(() => {
    const fetchDetail = async () => {
      setLoading(true);
      setError('');
      try {
        const result = await institutionService.getById(id);
        setData(result);
      } catch (err) {
        if (err.response?.status === 404) {
          setError('Institución no encontrada');
        } else {
          setError('Error al cargar los datos de la institución');
        }
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchDetail();
  }, [id]);

  // Auto-ocultar toast
  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 4000);
      return () => clearTimeout(timer);
    }
  }, [toast]);

  const handleSaveEdit = async (formData) => {
    await institutionService.update(id, formData);
    // Recargar los datos después de actualizar
    const result = await institutionService.getById(id);
    setData(result);
  };

  const handleEditSuccess = async (formData) => {
    await handleSaveEdit(formData);
    setIsEditModalOpen(false);
    // Toast después de cerrar el modal para evitar conflictos
    setTimeout(() => {
      setToast({ message: 'Institución actualizada correctamente', type: 'success' });
    }, 100);
  };

  if (loading) {
    return (
      <div className={styles.container}>
        <div className={styles.loading}>
          <Loader size={32} className={styles.spinner} />
          <span>Cargando información...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.container}>
        <div className={styles.error}>
          <AlertCircle size={48} />
          <h2>{error}</h2>
          <button onClick={() => navigate('/admin/institutions')} className={styles.btnSecondary}>
            <ArrowLeft size={18} />
            Volver a Instituciones
          </button>
        </div>
      </div>
    );
  }

  // Verificar que data no sea null antes de destructurar
  if (!data) {
    return (
      <div className={styles.container}>
        <div className={styles.loading}>
          <Loader size={32} className={styles.spinner} />
          <span>Cargando información...</span>
        </div>
      </div>
    );
  }

  const { institution, responsible, evaluations } = data;

  return (
    <div className={`${styles.container} ${ashEffect ? styles.pageAsh : ''}`}>
      {/* Navegación */}
      <div className={styles.breadcrumb}>
        <button onClick={() => navigate('/admin/institutions')} className={styles.backBtn}>
          <ArrowLeft size={20} />
          <span>Volver a Entidades</span>
        </button>
      </div>

      {/* Header */}
      <div className={styles.header}>
        <div className={styles.headerIcon}>
          <Building2 size={40} />
        </div>
        <div className={styles.headerInfo}>
          <h1>{institution.name}</h1>
          <div className={styles.headerMeta}>
            <a
              href={`https://${institution.domain}`}
              target="_blank"
              rel="noopener noreferrer"
              className={styles.domainLink}
            >
              {institution.domain}
              <ExternalLink size={14} />
            </a>
            <span className={`${styles.statusBadge} ${institution.is_active ? styles.statusActive : styles.statusInactive}`}>
              {institution.is_active ? 'Activo' : 'Inactivo'}
            </span>
          </div>
          <p className={styles.createdAt}>
            <Calendar size={14} />
            Registrado el {formatDate(institution.created_at)}
          </p>
        </div>
        <div className={styles.headerActions}>
          <button
            onClick={() => setIsEditModalOpen(true)}
            className={styles.btnOutline}
          >
            <Edit2 size={18} />
            Editar
          </button>
          <button
            onClick={() => setIsDeleteModalOpen(true)}
            className={styles.btnDanger}
            disabled={deleting}
          >
            {deleting ? (
              <>
                <Loader size={18} className={styles.spinner} />
                Eliminando...
              </>
            ) : (
              <>
                <Trash2 size={18} />
                Eliminar
              </>
            )}
          </button>
          <button className={styles.btnPrimary} onClick={() => navigate(`/admin/evaluations/new?institution=${id}`)}>
            <Play size={18} />
            Nueva Evaluación
          </button>
        </div>
      </div>

      {/* Contenido Principal */}
      <div className={styles.content}>
        {/* Columna Izquierda - Información */}
        <div className={styles.sidebar}>
          {/* Responsable */}
          <div className={styles.section}>
            <h3 className={styles.sectionTitle}>
              <User size={18} />
              Responsable
            </h3>
            <ResponsibleCard responsible={responsible} institution={institution} />
          </div>

          {/* Información Adicional */}
          <div className={styles.section}>
            <h3 className={styles.sectionTitle}>
              <Building2 size={18} />
              Información
            </h3>
            <div className={styles.infoList}>
              <div className={styles.infoItem}>
                <span className={styles.infoLabel}>Dominio</span>
                <span className={styles.infoValue}>{institution.domain}</span>
              </div>
              <div className={styles.infoItem}>
                <span className={styles.infoLabel}>Estado</span>
                <span className={styles.infoValue}>
                  {institution.is_active ? 'Activo' : 'Inactivo'}
                </span>
              </div>
              <div className={styles.infoItem}>
                <span className={styles.infoLabel}>Total Evaluaciones</span>
                <span className={styles.infoValue}>{evaluations.length}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Columna Derecha - Evaluaciones */}
        <div className={styles.main}>
          <div className={styles.section}>
            <div className={styles.sectionHeader}>
              <h3 className={styles.sectionTitle}>
                <BarChart3 size={18} />
                Historial de Evaluaciones
              </h3>
              {evaluations.length > 0 && (
                <Link to={`/admin/evaluations/new?institution=${id}`} className={styles.btnOutline}>
                  <Play size={16} />
                  Nueva Evaluación
                </Link>
              )}
            </div>

            {evaluations.length === 0 ? (
              <EmptyEvaluations institutionId={id} />
            ) : (
              <EvaluationsList evaluations={evaluations} />
            )}
          </div>
        </div>
      </div>

      {/* Modal de Edición */}
      {isEditModalOpen && (
        <EditModal
          key={institution?.id + '-' + responsible?.id}
          isOpen={isEditModalOpen}
          onClose={() => setIsEditModalOpen(false)}
          institution={institution}
          responsible={responsible}
          onSave={handleEditSuccess}
        />
      )}

      {/* Modal Confirmar Eliminar */}
      <ConfirmDeleteModal
        isOpen={isDeleteModalOpen}
        onClose={() => !deleting && setIsDeleteModalOpen(false)}
        onConfirm={handleDeleteFromPage}
        institutionName={institution?.name}
        deleting={deleting}
      />

      {/* Toast de notificación */}
      {toast && (
        <div className={`${styles.toast} ${toast.type === 'success' ? styles.toastSuccess : styles.toastError}`}>
          {toast.type === 'success' ? <CheckCircle size={18} /> : <AlertCircle size={18} />}
          <span>{toast.message}</span>
          <button onClick={() => setToast(null)} className={styles.toastClose}>
            <X size={16} />
          </button>
        </div>
      )}
    </div>
  );
}
