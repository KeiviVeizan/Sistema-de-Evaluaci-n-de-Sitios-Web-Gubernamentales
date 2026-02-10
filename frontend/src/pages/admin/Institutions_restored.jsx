import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Building2,
    Plus,
    ExternalLink,
    Copy,
    Check,
    X,
    Loader,
    AlertCircle,
    Eye,
    EyeOff,
    CheckCircle,
    User,
    Mail,
    Info,
    Search,
} from 'lucide-react';
import anime from 'animejs';
import institutionService from '../../services/institutionService';
import styles from './Institutions.module.css';

// Alfabeto para el filtro
const ALPHABET = 'ABCDEFGHIJKLMNÑOPQRSTUVWXYZ'.split('');

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

// Componente Tarjeta de Institución
function InstitutionCard({ institution, onClick }) {
    return (
        <div className={styles.card} onClick={onClick}>
            <div className={styles.cardIcon}>
                <Building2 size={32} />
            </div>
            <div className={styles.cardContent}>
                <h3 className={styles.cardTitle}>{institution.name}</h3>
                <a
                    href={`https://${institution.domain}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={styles.cardDomain}
                    onClick={(e) => e.stopPropagation()}
                >
                    {institution.domain}
                    <ExternalLink size={12} />
                </a>
                <div className={styles.cardMeta}>
                    <span className={`${styles.cardBadge} ${institution.is_active ? styles.badgeActive : styles.badgeInactive}`}>
                        {institution.is_active ? (
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
                    {institution.contact_name && (
                        <span className={styles.cardResponsible}>
                            <User size={12} />
                            {institution.contact_name}
                        </span>
                    )}
                </div>
            </div>
        </div>
    );
}

// Modal de credenciales generadas
function CredentialsModal({ credentials, onClose }) {
    const [copiedField, setCopiedField] = useState(null);

    const copyToClipboard = async (text, field) => {
        try {
            await navigator.clipboard.writeText(text);
            setCopiedField(field);
            setTimeout(() => setCopiedField(null), 2000);
        } catch (err) {
            console.error('Error al copiar:', err);
        }
    };

    return (
        <div className={styles.modalOverlay}>
            <div className={styles.modal}>
                <div className={styles.modalHeader}>
                    <div className={styles.modalHeaderIcon}>
                        <CheckCircle size={24} />
                    </div>
                    <h2>Institución Creada Exitosamente</h2>
                    <p>Guarda estas credenciales, no se mostrarán de nuevo</p>
                </div>

                <div className={styles.credentialsBox}>
                    <div className={styles.credentialItem}>
                        <label>Institución</label>
                        <div className={styles.credentialValue}>
                            <Building2 size={16} className={styles.credentialIcon} />
                            <span>{credentials.institution?.name}</span>
                        </div>
                    </div>

                    <div className={styles.credentialItem}>
                        <label>Responsable</label>
                        <div className={styles.credentialValue}>
                            <User size={16} className={styles.credentialIcon} />
                            <span>{credentials.initial_user?.full_name}</span>
                        </div>
                    </div>

                    <div className={styles.credentialsDivider}>
                        <span>Credenciales de Acceso</span>
                    </div>

                    <div className={styles.credentialItem}>
                        <label>Usuario (correo)</label>
                        <div className={styles.credentialValue}>
                            <Mail size={16} className={styles.credentialIcon} />
                            <span>{credentials.initial_user?.username}</span>
                            <button
                                onClick={() => copyToClipboard(credentials.initial_user?.username, 'username')}
                                className={styles.copyButton}
                                title="Copiar"
                            >
                                {copiedField === 'username' ? <Check size={16} /> : <Copy size={16} />}
                            </button>
                        </div>
                    </div>

                    <div className={styles.credentialItem}>
                        <label>Contraseña temporal</label>
                        <div className={styles.credentialValue}>
                            <code>{credentials.generated_password}</code>
                            <button
                                onClick={() => copyToClipboard(credentials.generated_password, 'password')}
                                className={styles.copyButton}
                                title="Copiar"
                            >
                                {copiedField === 'password' ? <Check size={16} /> : <Copy size={16} />}
                            </button>
                        </div>
                    </div>

                    <div className={styles.credentialsNote}>
                        <Info size={16} />
                        <span>El responsable deberá usar su correo electrónico como usuario para ingresar al sistema.</span>
                    </div>
                </div>

                <div className={styles.modalFooter}>
                    <button onClick={onClose} className={styles.btnPrimary}>
                        Entendido, cerrar
                    </button>
                </div>
            </div>
        </div>
    );
}

// Modal de creación de institución
function CreateModal({ onClose, onSuccess }) {
    const [formData, setFormData] = useState({
        name: '',
        domain: '',
        contact_name: '',
        contact_email: '',
        contact_position: '',
    });
    const [errors, setErrors] = useState({});
    const [isLoading, setIsLoading] = useState(false);
    const [apiError, setApiError] = useState('');

    const validateEmail = (email) => {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    };

    const validate = () => {
        const newErrors = {};

        if (!formData.name.trim()) {
            newErrors.name = 'El nombre es requerido';
        } else if (formData.name.length < 3) {
            newErrors.name = 'Mínimo 3 caracteres';
        }

        if (!formData.domain.trim()) {
            newErrors.domain = 'El dominio es requerido';
        } else if (!formData.domain.endsWith('.gob.bo')) {
            newErrors.domain = 'El dominio debe terminar en .gob.bo';
        }

        if (!formData.contact_name.trim()) {
            newErrors.contact_name = 'El nombre del responsable es requerido';
        } else if (formData.contact_name.length < 3) {
            newErrors.contact_name = 'Mínimo 3 caracteres';
        }

        if (!formData.contact_email.trim()) {
            newErrors.contact_email = 'El correo es requerido';
        } else if (!validateEmail(formData.contact_email)) {
            newErrors.contact_email = 'Ingrese un correo válido';
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setApiError('');

        if (!validate()) return;

        setIsLoading(true);
        try {
            const result = await institutionService.create(formData);
            onSuccess(result);
        } catch (err) {
            setApiError(err.response?.data?.detail || 'Error al crear la institución');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className={styles.modalOverlay}>
            <div className={styles.modalLarge}>
                <div className={styles.modalHeader}>
                    <h2>Nueva Institución</h2>
                    <button onClick={onClose} className={styles.modalClose}>
                        <X size={20} />
                    </button>
                </div>

                <form onSubmit={handleSubmit} className={styles.form}>
                    {apiError && (
                        <div className={styles.formError}>
                            <AlertCircle size={18} />
                            <span>{apiError}</span>
                        </div>
                    )}

                    <div className={styles.formSection}>
                        <h3 className={styles.formSectionTitle}>
                            <Building2 size={18} />
                            Datos de la Entidad
                        </h3>

                        <div className={styles.formGroup}>
                            <label htmlFor="name">Nombre de la Entidad *</label>
                            <input
                                type="text"
                                id="name"
                                value={formData.name}
                                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                placeholder="Ej: Aduana Nacional de Bolivia"
                                className={errors.name ? styles.inputError : ''}
                                disabled={isLoading}
                            />
                            {errors.name && <span className={styles.errorText}>{errors.name}</span>}
                        </div>

                        <div className={styles.formGroup}>
                            <label htmlFor="domain">Dominio / URL *</label>
                            <input
                                type="text"
                                id="domain"
                                value={formData.domain}
                                onChange={(e) => setFormData({ ...formData, domain: e.target.value.toLowerCase() })}
                                placeholder="Ej: aduana.gob.bo"
                                className={errors.domain ? styles.inputError : ''}
                                disabled={isLoading}
                            />
                            {errors.domain && <span className={styles.errorText}>{errors.domain}</span>}
                            <span className={styles.helpText}>Debe terminar en .gob.bo</span>
                        </div>
                    </div>

                    <div className={styles.formSection}>
                        <h3 className={styles.formSectionTitle}>
                            <User size={18} />
                            Datos del Responsable
                        </h3>

                        <div className={styles.formGroup}>
                            <label htmlFor="contact_name">Nombre Completo *</label>
                            <input
                                type="text"
                                id="contact_name"
                                value={formData.contact_name}
                                onChange={(e) => setFormData({ ...formData, contact_name: e.target.value })}
                                placeholder="Ej: Juan Pérez Mamani"
                                className={errors.contact_name ? styles.inputError : ''}
                                disabled={isLoading}
                            />
                            {errors.contact_name && <span className={styles.errorText}>{errors.contact_name}</span>}
                        </div>

                        <div className={styles.formGroup}>
                            <label htmlFor="contact_position">Cargo</label>
                            <input
                                type="text"
                                id="contact_position"
                                value={formData.contact_position}
                                onChange={(e) => setFormData({ ...formData, contact_position: e.target.value })}
                                placeholder="Ej: Director de Sistemas"
                                disabled={isLoading}
                            />
                            <span className={styles.helpText}>Opcional</span>
                        </div>

                        <div className={styles.formGroup}>
                            <label htmlFor="contact_email">Correo Institucional *</label>
                            <input
                                type="email"
                                id="contact_email"
                                value={formData.contact_email}
                                onChange={(e) => setFormData({ ...formData, contact_email: e.target.value.toLowerCase() })}
                                placeholder="Ej: juan.perez@aduana.gob.bo"
                                className={errors.contact_email ? styles.inputError : ''}
                                disabled={isLoading}
                            />
                            {errors.contact_email && <span className={styles.errorText}>{errors.contact_email}</span>}
                        </div>

                        <div className={styles.formNote}>
                            <Info size={16} />
                            <span>Este correo será el <strong>usuario de acceso</strong> al sistema. La contraseña se generará automáticamente.</span>
                        </div>
                    </div>

                    <div className={styles.modalActions}>
                        <button
                            type="button"
                            onClick={onClose}
                            className={styles.btnSecondary}
                            disabled={isLoading}
                        >
                            Cancelar
                        </button>
                        <button
                            type="submit"
                            className={styles.btnPrimary}
                            disabled={isLoading}
                        >
                            {isLoading ? (
                                <>
                                    <Loader size={18} className={styles.spinner} />
                                    Creando...
                                </>
                            ) : (
                                <>
                                    <Plus size={18} />
                                    Crear Institución
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
export default function Institutions() {
    const navigate = useNavigate();
    const gridRef = useRef(null);
    const [institutions, setInstitutions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedLetter, setSelectedLetter] = useState('');
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [credentials, setCredentials] = useState(null);
    const [toast, setToast] = useState(null);

    const fetchInstitutions = useCallback(async () => {
        setLoading(true);
        setError('');
        try {
            const data = await institutionService.getAll({
                search: searchQuery,
                letter: selectedLetter,
            });
            setInstitutions(data.items || []);
        } catch (err) {
            setError('Error al cargar las instituciones');
            console.error(err);
        } finally {
            setLoading(false);
        }
    }, [searchQuery, selectedLetter]);

    useEffect(() => {
        fetchInstitutions();
    }, [fetchInstitutions]);

    // Debounce para la búsqueda
    useEffect(() => {
        const timer = setTimeout(() => {
            fetchInstitutions();
        }, 300);
        return () => clearTimeout(timer);
    }, [searchQuery]);

    // Animación futurista stagger para las tarjetas
    useEffect(() => {
        if (!loading && institutions.length > 0 && gridRef.current) {
            const cards = gridRef.current.querySelectorAll(`.${styles.card}`);

            anime({
                targets: cards,
                opacity: [0, 1],
                translateY: [20, 0],
                delay: anime.stagger(30, { start: 100 }),
                duration: 400,
                easing: 'easeOutCubic',
            });
        }
    }, [institutions, loading]);

    const handleCreateSuccess = (result) => {
        setShowCreateModal(false);
        setCredentials(result);
        fetchInstitutions();
    };

    const handleCloseCredentials = () => {
        setCredentials(null);
        setToast({ message: 'Institución creada correctamente', type: 'success' });
    };

    const handleCardClick = (institution) => {
        navigate(`/admin/institutions/${institution.id}`);
    };

    const handleLetterClick = (letter) => {
        setSelectedLetter(selectedLetter === letter ? '' : letter);
        setSearchQuery('');
    };

    const handleSearchChange = (e) => {
        setSearchQuery(e.target.value);
        setSelectedLetter('');
    };

    // Agrupar instituciones por letra inicial para mostrar contador
    const letterCounts = useMemo(() => {
        const counts = {};
        institutions.forEach((inst) => {
            const firstLetter = inst.name.charAt(0).toUpperCase();
            counts[firstLetter] = (counts[firstLetter] || 0) + 1;
        });
        return counts;
    }, [institutions]);

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
                        <Building2 size={28} />
                        Entidades
                    </h1>
                    <p>Instituciones gubernamentales registradas en el sistema</p>
                </div>
                <button
                    onClick={() => setShowCreateModal(true)}
                    className={styles.btnPrimary}
                >
                    <Plus size={18} />
                    Nueva Institución
                </button>
            </div>

            {/* Filtros */}
            <div className={styles.filters}>
                {/* Barra de búsqueda */}
                <div className={styles.searchBox}>
                    <Search size={20} className={styles.searchIcon} />
                    <input
                        type="text"
                        placeholder="Buscar institución..."
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

                {/* Filtro alfabético */}
                <div className={styles.alphabetFilter}>
                    {ALPHABET.map((letter) => (
                        <button
                            key={letter}
                            onClick={() => handleLetterClick(letter)}
                            className={`${styles.letterBtn} ${selectedLetter === letter ? styles.letterActive : ''}`}
                        >
                            {letter}
                        </button>
                    ))}
                </div>
            </div>

            {/* Contenido */}
            <div className={styles.content}>
                {loading ? (
                    <div className={styles.loading}>
                        <Loader size={32} className={styles.spinner} />
                        <span>Cargando instituciones...</span>
                    </div>
                ) : error ? (
                    <div className={styles.error}>
                        <AlertCircle size={24} />
                        <span>{error}</span>
                        <button onClick={fetchInstitutions} className={styles.btnSecondary}>
                            Reintentar
                        </button>
                    </div>
                ) : institutions.length === 0 ? (
                    <div className={styles.empty}>
                        <Building2 size={48} />
                        <h3>
                            {searchQuery || selectedLetter
                                ? 'No se encontraron instituciones'
                                : 'No hay instituciones registradas'}
                        </h3>
                        <p>
                            {searchQuery || selectedLetter
                                ? 'Intenta con otros criterios de búsqueda'
                                : 'Crea la primera institución para comenzar'}
                        </p>
                        {!searchQuery && !selectedLetter && (
                            <button
                                onClick={() => setShowCreateModal(true)}
                                className={styles.btnPrimary}
                            >
                                <Plus size={18} />
                                Crear Primera Institución
                            </button>
                        )}
                    </div>
                ) : (
                    <>
                        {/* Contador de resultados */}
                        <div className={styles.resultsInfo}>
                            <span>
                                {institutions.length} {institutions.length === 1 ? 'institución' : 'instituciones'}
                                {selectedLetter && ` que comienzan con "${selectedLetter}"`}
                                {searchQuery && ` que coinciden con "${searchQuery}"`}
                            </span>
                        </div>

                        {/* Grid de tarjetas */}
                        <div className={styles.grid} ref={gridRef}>
                            {institutions.map((inst) => (
                                <InstitutionCard
                                    key={inst.id}
                                    institution={inst}
                                    onClick={() => handleCardClick(inst)}
                                />
                            ))}
                        </div>
                    </>
                )}
            </div>

            {/* Modal de creación */}
            {showCreateModal && (
                <CreateModal
                    onClose={() => setShowCreateModal(false)}
                    onSuccess={handleCreateSuccess}
                />
            )}

            {/* Modal de credenciales */}
            {credentials && (
                <CredentialsModal
                    credentials={credentials}
                    onClose={handleCloseCredentials}
                />
            )}
        </div>
    );
}
