import { useState, useEffect } from 'react';
import evaluationService from '../../services/evaluationService';
import followupService from '../../services/followupService';
import { useTheme } from '../../contexts/ThemeContext';
import styles from './EvaluatorFollowups.module.css';

// ── Toast ──────────────────────────────────────────────────────────────────────

function Toast({ message, type, onClose }) {
  if (!message) return null;
  const bg = type === 'error' ? '#c0392b' : '#27ae60';
  return (
    <div style={{ position: 'fixed', bottom: '24px', right: '24px', background: bg, color: '#fff', padding: '12px 20px', borderRadius: '8px', boxShadow: '0 4px 16px rgba(0,0,0,0.2)', zIndex: 9999, maxWidth: '400px', display: 'flex', alignItems: 'center', gap: '12px', fontSize: '0.9rem' }} role="alert">
      <span style={{ flex: 1 }}>{message}</span>
      <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: '#fff', cursor: 'pointer', fontSize: '1.2rem', lineHeight: 1, padding: 0 }} aria-label="Cerrar">×</button>
    </div>
  );
}

// ── ValidationModal ────────────────────────────────────────────────────────────

function ValidationModal({ followup, onValidate, onClose }) {
  const [action, setAction] = useState('approve');
  const [notes, setNotes] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const handleSave = async () => {
    setSaving(true);
    setError('');
    try {
      await onValidate(followup.id, action === 'approve', notes);
      onClose();
    } catch (err) {
      setError(err?.response?.data?.detail || 'Error al guardar');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className={styles.modalOverlay}>
      <div className={styles.modalBox}>
        <h3 className={styles.modalTitle}>Validar Corrección</h3>
        <p className={styles.modalSubtitle}>
          <strong>{followup.criteria_id}</strong> — {followup.criteria_name}
        </p>

        <label className={styles.modalLabel}>Decisión</label>
        <div className={styles.actionGroup}>
          <button
            className={styles.actionBtn}
            onClick={() => setAction('approve')}
            style={{
              background: action === 'approve' ? '#27ae60' : 'transparent',
              color: action === 'approve' ? '#fff' : '#27ae60',
              borderColor: '#27ae60',
            }}
          >
            ✓ Aprobar corrección
          </button>
          <button
            className={styles.actionBtn}
            onClick={() => setAction('reject')}
            style={{
              background: action === 'reject' ? '#c0392b' : 'transparent',
              color: action === 'reject' ? '#fff' : '#c0392b',
              borderColor: '#c0392b',
            }}
          >
            ✗ Rechazar corrección
          </button>
        </div>

        <label className={styles.modalLabel}>
          Comentarios{' '}
          {action === 'reject' && (
            <span className={styles.modalLabelNote}>(obligatorio si rechaza)</span>
          )}
        </label>
        <textarea
          value={notes}
          onChange={e => setNotes(e.target.value)}
          placeholder={action === 'approve' ? 'Comentarios adicionales (opcional)' : 'Explique el motivo del rechazo...'}
          rows={4}
          className={styles.modalTextarea}
        />

        {error && <p className={styles.modalError}>{error}</p>}

        <div className={styles.modalActions}>
          <button className={styles.btnModalCancel} onClick={onClose} disabled={saving}>
            Cancelar
          </button>
          <button
            className={styles.btnModalSave}
            onClick={handleSave}
            disabled={saving || (action === 'reject' && !notes.trim())}
            style={{ background: action === 'approve' ? '#27ae60' : '#c0392b' }}
          >
            {saving ? 'Guardando...' : (action === 'approve' ? 'Aprobar' : 'Rechazar')}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── EvaluatorFollowups ─────────────────────────────────────────────────────────

export default function EvaluatorFollowups() {
  const { dark } = useTheme();
  const [followupsByInstitution, setFollowupsByInstitution] = useState({});
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [modalFollowup, setModalFollowup] = useState(null);
  const [toast, setToast] = useState({ message: '', type: 'success' });

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast({ message: '', type: 'success' }), 5000);
  };

  useEffect(() => { loadFollowups(); }, []);

  const loadFollowups = async () => {
    try {
      setLoading(true);
      const myEvaluations = await evaluationService.getMyEvaluations();
      const myEvaluationIds = myEvaluations.map(ev => ev.id);

      if (myEvaluationIds.length === 0) {
        setFollowupsByInstitution({});
        setLoading(false);
        return;
      }

      const allFollowups = await followupService.getAll();
      const myFollowups = allFollowups.filter(f => myEvaluationIds.includes(f.evaluation_id));

      const grouped = {};
      for (const followup of myFollowups) {
        const evaluation = myEvaluations.find(ev => ev.id === followup.evaluation_id);
        const institutionName = evaluation?.institution_name || 'Institución desconocida';
        if (!grouped[institutionName]) grouped[institutionName] = [];
        grouped[institutionName].push(followup);
      }

      setFollowupsByInstitution(grouped);
    } catch {
      showToast('Error al cargar los seguimientos', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleValidate = async (followupId, approved, notes) => {
    await followupService.validate(followupId, { approved, notes });
    await loadFollowups();
    showToast(
      approved
        ? 'Corrección aprobada exitosamente'
        : 'Corrección rechazada. La institución deberá volver a corregir.',
    );
  };

  const STATUS_CONFIG = dark ? {
    pending:   { label: 'Pendiente de corrección', color: '#fcd34d', bg: 'rgba(217,119,6,0.12)' },
    corrected: { label: 'Esperando validación',    color: '#93c5fd', bg: 'rgba(41,128,185,0.1)' },
    validated: { label: 'Corrección validada',     color: '#4ade80', bg: 'rgba(39,174,96,0.08)' },
    rejected:  { label: 'Corrección rechazada',    color: '#f87171', bg: 'rgba(192,57,43,0.1)' },
    cancelled: { label: 'Cancelado',               color: '#7b8496', bg: 'rgba(255,255,255,0.04)' },
  } : {
    pending:   { label: 'Pendiente de corrección', color: '#e67e22', bg: '#fef9f0' },
    corrected: { label: 'Esperando validación',    color: '#2980b9', bg: '#f0f7ff' },
    validated: { label: 'Corrección validada',     color: '#27ae60', bg: '#f0faf4' },
    rejected:  { label: 'Corrección rechazada',    color: '#c0392b', bg: '#fdf5f5' },
    cancelled: { label: 'Cancelado',               color: '#95a5a6', bg: '#f8f9fa' },
  };

  const allFollowups = Object.values(followupsByInstitution).flat();
  const counts = allFollowups.reduce((acc, f) => {
    acc[f.status] = (acc[f.status] || 0) + 1;
    return acc;
  }, {});

  const filteredInstitutions = {};
  Object.entries(followupsByInstitution).forEach(([institution, followups]) => {
    const filtered = filter === 'all' ? followups : followups.filter(f => f.status === filter);
    if (filtered.length > 0) filteredInstitutions[institution] = filtered;
  });

  if (loading) {
    return (
      <div className={styles.spinnerWrapper}>
        <div className={styles.spinner} />
      </div>
    );
  }

  const filterTabs = [
    { key: 'all',       label: 'Todos',       color: '#2c5f8a' },
    { key: 'pending',   label: 'Pendientes',  color: dark ? '#fcd34d' : '#e67e22' },
    { key: 'corrected', label: 'Por validar', color: dark ? '#93c5fd' : '#2980b9' },
    { key: 'validated', label: 'Validados',   color: dark ? '#4ade80' : '#27ae60' },
    { key: 'rejected',  label: 'Rechazados',  color: dark ? '#f87171' : '#c0392b' },
  ];

  return (
    <div className={styles.container}>
      <h1 className={styles.pageTitle}>Mis Seguimientos</h1>
      <p className={styles.pageSubtitle}>
        Seguimientos de las evaluaciones que has realizado, agrupados por institución.
      </p>

      <div className={styles.filterRow}>
        {filterTabs.map(({ key, label, color }) => {
          const count = key === 'all' ? allFollowups.length : (counts[key] || 0);
          const active = filter === key;
          return (
            <button
              key={key}
              className={styles.filterBtn}
              onClick={() => setFilter(key)}
              style={{
                background: active ? color : 'transparent',
                color: active ? '#fff' : color,
                border: `1px solid ${color}`,
              }}
            >
              {label} ({count})
            </button>
          );
        })}
      </div>

      {Object.keys(filteredInstitutions).length === 0 ? (
        <div className={styles.emptyMsg}>
          {allFollowups.length === 0
            ? 'No tienes seguimientos asignados actualmente.'
            : 'No hay seguimientos con el filtro seleccionado.'}
        </div>
      ) : (
        <div className={styles.groupList}>
          {Object.entries(filteredInstitutions).map(([institutionName, followups]) => (
            <div key={institutionName} className={styles.groupCard}>
              <h2 className={styles.groupTitle}>
                <span style={{ fontSize: '1.3rem' }}>🏛️</span>
                {institutionName}
                <span className={styles.groupCount}>
                  {followups.length} seguimiento{followups.length > 1 ? 's' : ''}
                </span>
              </h2>

              <div className={styles.followupList}>
                {followups.map(f => {
                  const cfg = STATUS_CONFIG[f.status] || STATUS_CONFIG.pending;
                  const overdue = f.status === 'pending' && new Date(f.due_date) < new Date();

                  return (
                    <div
                      key={f.id}
                      className={styles.followupItem}
                      style={{
                        background: cfg.bg,
                        border: `1px solid ${overdue ? (dark ? '#f87171' : '#c0392b') : cfg.color}`,
                        borderLeft: `4px solid ${overdue ? (dark ? '#f87171' : '#c0392b') : cfg.color}`,
                      }}
                    >
                      <div className={styles.followupHeader}>
                        <div className={styles.followupInfo}>
                          <div className={styles.followupName}>
                            <code className={styles.critCode}>{f.criteria_id}</code>
                            {f.criteria_name}
                          </div>
                          <div className={overdue ? styles.followupDateOverdue : styles.followupDate}>
                            Vence: {new Date(f.due_date).toLocaleDateString('es-BO')}
                            {overdue && <span style={{ marginLeft: '8px' }}>VENCIDO</span>}
                          </div>
                        </div>
                        <span style={{
                          fontSize: '0.75rem',
                          fontWeight: 700,
                          color: cfg.color,
                          background: `${cfg.color}20`,
                          border: `1px solid ${cfg.color}`,
                          borderRadius: '4px',
                          padding: '3px 10px',
                          whiteSpace: 'nowrap',
                        }}>
                          {cfg.label}
                        </span>
                      </div>

                      {f.notes && (
                        <>
                          <hr className={styles.divider} />
                          <p className={styles.notesText}>Observaciones: {f.notes}</p>
                        </>
                      )}

                      {f.corrected_at && (
                        <div className={styles.correctedBox}>
                          ✓ Corrección reportada el {new Date(f.corrected_at).toLocaleDateString('es-BO')}
                        </div>
                      )}

                      {f.status === 'validated' && f.validation_notes && (
                        <div className={styles.validatedBox}>
                          <strong>Tu comentario:</strong> {f.validation_notes}
                        </div>
                      )}

                      {f.status === 'rejected' && f.validation_notes && (
                        <div className={styles.rejectedBox}>
                          <strong>Motivo del rechazo:</strong> {f.validation_notes}
                        </div>
                      )}

                      <div className={styles.actionRow}>
                        {f.status === 'corrected' && (
                          <button className={styles.btnValidate} onClick={() => setModalFollowup(f)}>
                            📋 Revisar y validar corrección
                          </button>
                        )}
                        {f.status === 'pending' && (
                          <p className={`${styles.statusMsg} ${styles.statusMsgPending}`}>
                            Esperando que la institución reporte la corrección.
                          </p>
                        )}
                        {f.status === 'validated' && (
                          <p className={`${styles.statusMsg} ${styles.statusMsgValidated}`}>
                            ✓ Corrección validada exitosamente.
                          </p>
                        )}
                        {f.status === 'rejected' && (
                          <p className={`${styles.statusMsg} ${styles.statusMsgRejected}`}>
                            La institución debe volver a corregir este criterio.
                          </p>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}

      {modalFollowup && (
        <ValidationModal
          followup={modalFollowup}
          onValidate={handleValidate}
          onClose={() => setModalFollowup(null)}
        />
      )}

      <Toast message={toast.message} type={toast.type} onClose={() => setToast({ message: '', type: 'success' })} />
    </div>
  );
}
