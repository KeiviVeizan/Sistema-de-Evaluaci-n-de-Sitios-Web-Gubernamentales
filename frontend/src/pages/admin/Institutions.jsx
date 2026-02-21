import { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Building2,
  Search,
  Plus,
  X,
  Loader,
  AlertCircle,
  CheckCircle,
  ExternalLink,
  User,
  Save,
  Copy,
  Lock,
} from 'lucide-react';
import institutionService from '../../services/institutionService';
import styles from './Institutions.module.css';

// ── Toast ────────────────────────────────────────────────────────────────────
function Toast({ message, type = 'success', onClose }) {
  useEffect(() => {
    const timer = setTimeout(onClose, 5000);
    return () => clearTimeout(timer);
  }, [onClose]);

  return (
    <div className={`${styles.toast} ${styles[`toast${type.charAt(0).toUpperCase() + type.slice(1)}`]} `}>
      {type === 'success' ? <CheckCircle size={18} /> : <AlertCircle size={18} />}
      <span>{message}</span>
      <button onClick={onClose} className={styles.toastClose}><X size={16} /></button>
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

// ── Modal Crear Institución ──────────────────────────────────────────────────
function CreateInstitutionModal({ isOpen, onClose, onSave }) {
  const [formData, setFormData] = useState({
    name: '',
    domain: '',
    contact_name: '',
    contact_email: '',
    contact_position: '',
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen) {
      setFormData({ name: '', domain: '', contact_name: '', contact_email: '' });
      setError('');
      setSaving(false);
    }
  }, [isOpen]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      await onSave(formData);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al crear la institución');
      setSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className={styles.modalOverlay} onClick={onClose}>
      <div className={styles.modalLarge} onClick={(e) => e.stopPropagation()}>
        <div className={styles.modalHeader}>
          <h2>Nueva Institución</h2>
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
                  type="text" id="name" name="name"
                  value={formData.name} onChange={handleChange}
                  required minLength={3} maxLength={255}
                  className={styles.input} disabled={saving}
                  placeholder="Ej: Ministerio de Economía"
                />
              </div>
              <div className={styles.formGroup}>
                <label htmlFor="domain">Dominio Web *</label>
                <input
                  type="text" id="domain" name="domain"
                  value={formData.domain} onChange={handleChange}
                  required minLength={5} maxLength={255}
                  className={styles.input} disabled={saving}
                  placeholder="ejemplo.gob.bo"
                />
                <span className={styles.inputHint}>Debe terminar en .gob.bo</span>
              </div>
            </div>
            <div className={styles.formSection}>
              <h3 className={styles.formSectionTitle}>
                <User size={16} />
                Responsable / Encargado
              </h3>
              <div className={styles.formGroup}>
                <label htmlFor="contact_name">Nombre Completo *</label>
                <input
                  type="text" id="contact_name" name="contact_name"
                  value={formData.contact_name} onChange={handleChange}
                  required minLength={3} maxLength={100}
                  className={styles.input} disabled={saving}
                  placeholder="Ej: Juan Pérez Mamani"
                />
              </div>
              <div className={styles.formGroup}>
                <label htmlFor="contact_email">Correo Institucional *</label>
                <input
                  type="email" id="contact_email" name="contact_email"
                  value={formData.contact_email} onChange={handleChange}
                  required
                  className={styles.input} disabled={saving}
                  placeholder="responsable@entidad.gob.bo"
                />
                <span className={styles.inputHint}>Se usará como usuario de acceso para el responsable</span>
              </div>
              <div className={styles.formGroup}>
                <label htmlFor="contact_position">Cargo</label>
                <input
                  type="text" id="contact_position" name="contact_position"
                  value={formData.contact_position || ''} onChange={handleChange}
                  maxLength={100}
                  className={styles.input} disabled={saving}
                  placeholder="Ej: Director de Tecnología"
                />
              </div>
            </div>
          </div>
          <div className={styles.modalFooter}>
            <button type="button" onClick={onClose} className={styles.btnSecondary} disabled={saving}>
              Cancelar
            </button>
            <button type="submit" className={styles.btnPrimary} disabled={saving}>
              {saving ? (
                <><Loader size={18} className={styles.spinner} />Registrando...</>
              ) : (
                <><Save size={18} />Registrar Institución</>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ── Modal Credenciales ───────────────────────────────────────────────────────
function CredentialsModal({ isOpen, onClose, data }) {
  const [copied, setCopied] = useState('');

  const handleCopy = (text, field) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(field);
      setTimeout(() => setCopied(''), 2000);
    });
  };

  if (!isOpen || !data) return null;

  return (
    <div className={styles.modalOverlay}>
      <div className={styles.modal} style={{ maxWidth: 480 }}>
        <div className={styles.modalHeader}>
          <h2>Institución Registrada</h2>
        </div>
        <div className={styles.modalBody}>
          <div className={styles.credentialsAlert}>
            <Lock size={20} />
            <p><strong>Guarda estas credenciales.</strong> La contraseña generada solo se muestra una vez y no podrá recuperarse.</p>
          </div>
          <div className={styles.credentialItem}>
            <span className={styles.credentialLabel}>Institución</span>
            <span className={styles.credentialValue}>{data.institution?.name}</span>
          </div>
          <div className={styles.credentialItem}>
            <span className={styles.credentialLabel}>Usuario (email)</span>
            <div className={styles.credentialRow}>
              <span className={styles.credentialValue}>{data.initial_user?.email}</span>
              <button onClick={() => handleCopy(data.initial_user?.email, 'email')} className={styles.copyBtn} title="Copiar">
                {copied === 'email' ? <CheckCircle size={15} /> : <Copy size={15} />}
              </button>
            </div>
          </div>
          <div className={styles.credentialItem}>
            <span className={styles.credentialLabel}>Contraseña Temporal</span>
            <div className={styles.credentialRow}>
              <code className={styles.credentialPassword}>{data.generated_password}</code>
              <button onClick={() => handleCopy(data.generated_password, 'password')} className={styles.copyBtn} title="Copiar">
                {copied === 'password' ? <CheckCircle size={15} /> : <Copy size={15} />}
              </button>
            </div>
          </div>
        </div>
        <div className={styles.modalFooter}>
          <button onClick={onClose} className={styles.btnPrimary}>Entendido</button>
        </div>
      </div>
    </div>
  );
}

// ── Tarjeta de Institución ───────────────────────────────────────────────────
function InstitutionCard({ institution }) {
  const navigate = useNavigate();

  const handleCardClick = (e) => {
    if (e.target.tagName !== 'A' && e.target.tagName !== 'BUTTON' && !e.target.closest('a') && !e.target.closest('button')) {
      navigate(`/admin/institutions/${institution.id}`);
    }
  };

  return (
    <div className={styles.card} onClick={handleCardClick}>
      <div className={styles.cardIcon}>
        <Building2 size={32} />
      </div>
      <div className={styles.cardBody}>
        <h3 className={styles.cardName}>{institution.name}</h3>
        <a
          href={`https://${institution.domain}`}
          target="_blank"
          rel="noopener noreferrer"
          className={styles.cardDomain}
          onClick={(e) => e.stopPropagation()}
        >
          {institution.domain}
          <ExternalLink size={13} />
        </a>
        <span className={`${styles.statusBadge} ${institution.is_active ? styles.statusActive : styles.statusInactive}`}>
          {institution.is_active ? 'Activa' : 'Inactiva'}
        </span>
      </div>
    </div>
  );
}


// ── Alfabeto ─────────────────────────────────────────────────────────────────
const ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');

// ── Componente Principal ─────────────────────────────────────────────────────
export default function Institutions() {
  const [institutions, setInstitutions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [activeLetter, setActiveLetter] = useState('');
  const [toast, setToast] = useState(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [credentialsData, setCredentialsData] = useState(null);

  const fetchInstitutions = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await institutionService.getAll({});
      const sorted = (data.items || []).sort((a, b) =>
        a.name.localeCompare(b.name, 'es', { sensitivity: 'base' })
      );
      setInstitutions(sorted);
    } catch (err) {
      setError('Error al cargar las instituciones');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchInstitutions();
  }, [fetchInstitutions]);

  const handleLetterClick = (letter) => {
    setActiveLetter((prev) => (prev === letter ? '' : letter));
    setSearchQuery('');
  };

  const handleSearchChange = (e) => {
    setSearchQuery(e.target.value);
    setActiveLetter('');
  };

  const handleCreateInstitution = async (formData) => {
    const result = await institutionService.create(formData);
    setIsCreateModalOpen(false);
    await fetchInstitutions();
    setCredentialsData(result);
  };

  // Filtro local (inmediato, sin llamadas extra al servidor)
  const displayed = institutions.filter((inst) => {
    if (searchQuery) {
      return inst.name.toLowerCase().includes(searchQuery.toLowerCase());
    }
    if (activeLetter) {
      return inst.name.toUpperCase().startsWith(activeLetter);
    }
    return true;
  });

  return (
    <div className={styles.container}>
      {toast && (
        <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />
      )}

      {/* Header */}
      <div className={styles.header}>
        <div className={styles.headerInfo}>
          <h1><Building2 size={28} />Entidades</h1>
          <p>Gestión de instituciones gubernamentales registradas</p>
        </div>
        <button onClick={() => setIsCreateModalOpen(true)} className={styles.btnPrimary}>
          <Plus size={18} />
          Registrar Entidad
        </button>
      </div>

      {/* Buscador */}
      <div className={styles.searchBox}>
        <Search size={20} className={styles.searchIcon} />
        <input
          type="text"
          placeholder="Buscar por nombre..."
          value={searchQuery}
          onChange={handleSearchChange}
          className={styles.searchInput}
        />
        {searchQuery && (
          <button onClick={() => setSearchQuery('')} className={styles.searchClear}>
            <X size={16} />
          </button>
        )}
      </div>

      {/* Filtro alfabético */}
      <div className={styles.alphabetBar}>
        {ALPHABET.map((letter) => (
          <button
            key={letter}
            className={`${styles.letterBtn} ${activeLetter === letter ? styles.letterActive : ''}`}
            onClick={() => handleLetterClick(letter)}
          >
            {letter}
          </button>
        ))}
      </div>

      {/* Contenido */}
      {loading ? (
        <div className={styles.stateBox}>
          <Loader size={32} className={styles.spinner} />
          <span>Cargando instituciones...</span>
        </div>
      ) : error ? (
        <div className={`${styles.stateBox} ${styles.stateError}`}>
          <AlertCircle size={24} />
          <span>{error}</span>
          <button onClick={fetchInstitutions} className={styles.btnSecondary}>Reintentar</button>
        </div>
      ) : displayed.length === 0 ? (
        <div className={styles.stateBox}>
          <Building2 size={48} style={{ opacity: 0.3 }} />
          <h3>
            {searchQuery || activeLetter ? 'Sin resultados' : 'No hay instituciones registradas'}
          </h3>
          <p>
            {searchQuery
              ? `No se encontraron instituciones para "${searchQuery}"`
              : activeLetter
                ? `No hay instituciones que comiencen con "${activeLetter}"`
                : 'Registra la primera institución para comenzar'}
          </p>
          {!searchQuery && !activeLetter && (
            <button onClick={() => setIsCreateModalOpen(true)} className={styles.btnPrimary}>
              <Plus size={18} />Registrar Primera Entidad
            </button>
          )}
        </div>
      ) : (
        <>
          <p className={styles.resultsInfo}>
            {displayed.length} {displayed.length === 1 ? 'institución' : 'instituciones'}
            {searchQuery && ` para "${searchQuery}"`}
            {activeLetter && ` con letra "${activeLetter}"`}
          </p>
          <div className={styles.grid}>
            {displayed.map((institution) => (
              <InstitutionCard
                key={institution.id}
                institution={institution}
              />
            ))}
          </div>
        </>
      )}

      <CreateInstitutionModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSave={handleCreateInstitution}
      />

      <CredentialsModal
        isOpen={!!credentialsData}
        onClose={() => {
          setCredentialsData(null);
          setToast({ message: 'Institución registrada correctamente', type: 'success' });
        }}
        data={credentialsData}
      />
    </div>
  );
}