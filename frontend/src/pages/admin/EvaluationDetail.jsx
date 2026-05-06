import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Download, ArrowLeft, Calendar } from 'lucide-react';
import evaluationService from '../../services/evaluationService';
import followupService from '../../services/followupService';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import ResultsDashboard from '../../components/home/ResultsDashboard';
import styles from './EvaluationDetail.module.css';

// ── Followup status config ─────────────────────────────────────────────────────

const FOLLOWUP_STATUS = (dark) => ({
  pending:   { label: 'Pendiente',             color: dark ? '#fcd34d' : '#e67e22' },
  corrected: { label: 'Corregido (pendiente)', color: dark ? '#93c5fd' : '#2980b9' },
  validated: { label: 'Validado',              color: dark ? '#34d399' : '#27ae60' },
  rejected:  { label: 'Rechazado',             color: dark ? '#f87171' : '#c0392b' },
  cancelled: { label: 'Cancelado',             color: dark ? '#7b8496' : '#95a5a6' },
});

// ── Toast ──────────────────────────────────────────────────────────────────────

function Toast({ message, type, onClose }) {
  if (!message) return null;
  const bg = type === 'error' ? '#c0392b' : '#27ae60';
  return (
    <div style={{ position: 'fixed', bottom: '24px', right: '24px', background: bg, color: '#fff', padding: '12px 20px', borderRadius: '8px', boxShadow: '0 4px 16px rgba(0,0,0,0.2)', zIndex: 9999, maxWidth: '400px', display: 'flex', alignItems: 'center', gap: '12px', fontSize: '0.9rem' }} role="alert">
      <span style={{ flex: 1 }}>{message}</span>
      <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: '#fff', cursor: 'pointer', fontSize: '1.2rem', lineHeight: 1, padding: 0 }} aria-label="Cerrar">x</button>
    </div>
  );
}

// ── FollowupModal ──────────────────────────────────────────────────────────────

function FollowupModal({ nonCompliant, evaluationId, onSave, onClose }) {
  const { dark } = useTheme();
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [dueDate, setDueDate] = useState('');
  const [notes, setNotes] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const toggleCriteria = (id) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleAll = () => {
    if (selectedIds.size === nonCompliant.length) setSelectedIds(new Set());
    else setSelectedIds(new Set(nonCompliant.map(c => c.id)));
  };

  const handleSave = async () => {
    if (selectedIds.size === 0) { setError('Seleccione al menos un criterio'); return; }
    if (!dueDate) { setError('Seleccione una fecha de vencimiento'); return; }
    const payload = {
      evaluation_id: evaluationId,
      criteria_result_ids: Array.from(selectedIds).map(Number),
      due_date: dueDate,
      notes,
    };
    setSaving(true);
    setError('');
    try {
      await onSave(payload);
      onClose();
    } catch (err) {
      setError(err?.response?.data?.detail || 'Error al guardar los seguimientos');
    } finally {
      setSaving(false);
    }
  };

  const allSelected = selectedIds.size === nonCompliant.length;

  return (
    <div className={styles.modalOverlay}>
      <div className={styles.modalBox}>
        <h3 className={styles.modalTitle}>Programar Seguimiento</h3>

        <label className={styles.modalLabel}>
          Criterios a corregir *{' '}
          <span style={{ fontWeight: 400, color: dark ? '#3d4455' : '#888', fontSize: '0.8rem' }}>
            ({selectedIds.size} seleccionado{selectedIds.size !== 1 ? 's' : ''})
          </span>
        </label>

        <div className={styles.criteriaList}>
          <label className={styles.criteriaSelectAll}>
            <input type="checkbox" checked={allSelected} onChange={toggleAll} style={{ accentColor: '#800000' }} />
            Seleccionar todos
          </label>
          {nonCompliant.map(c => (
            <label
              key={c.id}
              className={styles.criteriaItem}
              style={{ background: selectedIds.has(c.id) ? (dark ? 'rgba(196,64,64,0.1)' : '#fdf2f2') : 'transparent' }}
            >
              <input type="checkbox" checked={selectedIds.has(c.id)} onChange={() => toggleCriteria(c.id)} style={{ accentColor: '#800000' }} />
              <code className={styles.criteriaCode}>{c.criteria_id}</code>
              <span className={styles.criteriaName}>{c.criteria_name}</span>
              <span className={c.status === 'fail' ? styles.criteriaStatusFail : styles.criteriaStatusPartial}>
                {c.status === 'fail' ? 'Fallido' : 'Parcial'}
              </span>
            </label>
          ))}
        </div>

        <label className={styles.modalLabel}>Fecha de vencimiento *</label>
        <input
          type="date"
          value={dueDate}
          onChange={e => setDueDate(e.target.value)}
          className={styles.modalInput}
          min={new Date().toISOString().split('T')[0]}
        />

        <label className={styles.modalLabel}>Notas</label>
        <textarea
          value={notes}
          onChange={e => setNotes(e.target.value)}
          placeholder="Observaciones o acciones requeridas..."
          rows={3}
          className={styles.modalInput}
          style={{ resize: 'vertical', fontFamily: 'inherit' }}
        />

        {error && <p className={styles.modalError}>{error}</p>}

        <div className={styles.modalActions}>
          <button className={styles.btnModalCancel} onClick={onClose} disabled={saving}>Cancelar</button>
          <button className={styles.btnModalSave} onClick={handleSave} disabled={saving}>
            {saving ? 'Guardando...' : `Guardar${selectedIds.size > 1 ? ` (${selectedIds.size})` : ''}`}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── EvaluationDetail ───────────────────────────────────────────────────────────

export default function EvaluationDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { dark } = useTheme();
  const { user, hasPermission } = useAuth();
  const canManageFollowups = hasPermission('followups_manage');
  const isAdminOrSecretary = user?.role === 'admin' || user?.role === 'superadmin' || user?.role === 'secretary';

  const [evaluation, setEvaluation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);
  const [toast, setToast] = useState({ message: '', type: 'success' });
  const [followups, setFollowups] = useState([]);
  const [showModal, setShowModal] = useState(false);

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast({ message: '', type: 'success' }), 5000);
  };

  useEffect(() => {
    const fetchEvaluation = async () => {
      try {
        setLoading(true);
        const data = await evaluationService.getById(id);
        setEvaluation(data);
      } catch {
        showToast('Error cargando la evaluacion', 'error');
      } finally {
        setLoading(false);
      }
    };
    fetchEvaluation();
  }, [id]);

  useEffect(() => {
    if (id) followupService.getAll({ evaluation_id: id }).then(data => setFollowups(data)).catch(() => {});
  }, [id]);

  const handleDownloadReport = async () => {
    setDownloading(true);
    try {
      await evaluationService.downloadReport(id);
      showToast('Informe PDF descargado correctamente');
    } catch {
      showToast('Error al generar el informe PDF', 'error');
    } finally {
      setDownloading(false);
    }
  };

  const handleCreateFollowup = async (data) => {
    const createdList = await followupService.createBulk(data);
    setFollowups(prev => [...prev, ...createdList]);
    const count = createdList.length;
    showToast(`${count} seguimiento${count !== 1 ? 's' : ''} programado${count !== 1 ? 's' : ''} correctamente`);
  };

  const handleValidateFollowup = async (followupId, approved) => {
    try {
      const updated = await followupService.validate(followupId, { approved, notes: '' });
      setFollowups(prev => prev.map(f => f.id === followupId ? updated : f));
      showToast(approved ? 'Correccion validada correctamente' : 'Correccion rechazada');
    } catch {
      showToast('Error al validar el seguimiento', 'error');
    }
  };

  const handleCancelFollowup = async (followupId) => {
    try {
      const updated = await followupService.cancel(followupId);
      setFollowups(prev => prev.map(f => f.id === followupId ? updated : f));
      showToast('Seguimiento cancelado');
    } catch {
      showToast('Error al cancelar el seguimiento', 'error');
    }
  };

  if (loading) {
    return (
      <div className={styles.loadingWrapper}>
        <div className={styles.spinner} />
      </div>
    );
  }

  if (!evaluation) {
    return (
      <div className={styles.notFound}>
        <p className={styles.notFoundText}>No se encontro la evaluacion.</p>
        <button className={styles.btnBack} onClick={() => navigate(-1)}>
          <ArrowLeft size={16} /> Volver
        </button>
      </div>
    );
  }

  const criteriaResults = evaluation.criteria_results || [];
  const nonCompliant = [
    ...criteriaResults.filter(c => c.status === 'fail'),
    ...criteriaResults.filter(c => c.status === 'partial'),
  ];
  const evalDate = evaluation.timestamp
    ? new Date(evaluation.timestamp).toLocaleString('es-BO')
    : '-';

  const statusMap = FOLLOWUP_STATUS(dark);

  return (
    <div className={styles.container}>
      <div className={styles.topBar}>
        <button className={styles.btnBack} onClick={() => navigate(-1)}>
          <ArrowLeft size={16} /> Volver
        </button>
        <button className={styles.btnDownload} onClick={handleDownloadReport} disabled={downloading}>
          {downloading
            ? <><span className={styles.btnSpinner} /> Generando PDF...</>
            : <><Download size={16} /> Descargar Informe PDF</>
          }
        </button>
      </div>

      <h1 className={styles.pageTitle}>Detalle de Evaluacion #{id}</h1>
      <p className={styles.pageMeta}>
        URL evaluada: <strong>{evaluation.url || '-'}</strong> &nbsp;&middot;&nbsp; Fecha: {evalDate}
      </p>

      <ResultsDashboard data={evaluation} hideHeader />

      <section className={styles.section}>
        <div className={styles.sectionHeader}>
          <h2 className={styles.sectionTitle}>Seguimientos Programados</h2>
          {canManageFollowups && nonCompliant.length > 0 && (
            <button className={styles.btnSchedule} onClick={() => setShowModal(true)}>
              <Calendar size={14} /> + Programar Seguimiento
            </button>
          )}
        </div>

        {followups.length === 0 ? (
          <p className={styles.followupEmpty}>No hay seguimientos programados para esta evaluacion.</p>
        ) : (
          <div className={styles.followupList}>
            {followups.map(f => {
              const statusCfg = statusMap[f.status] || statusMap.pending;
              const overdue = f.status === 'pending' && new Date(f.due_date) < new Date();
              return (
                <div
                  key={f.id}
                  className={styles.followupItem}
                  style={{ border: `1px solid ${overdue ? (dark ? '#f87171' : '#c0392b') : (dark ? 'rgba(255,255,255,0.07)' : '#d0dce8')}` }}
                >
                  <div className={styles.followupLeft}>
                    <div className={styles.followupName}>
                      <code className={styles.followupCode}>{f.criteria_id}</code>
                      {f.criteria_name}
                    </div>
                    <div className={overdue ? styles.followupDateOverdue : styles.followupDate}>
                      Vence: {new Date(f.due_date).toLocaleDateString('es-BO')}
                      {overdue && <span style={{ marginLeft: '6px', fontWeight: 600 }}> - VENCIDO</span>}
                    </div>
                    {f.notes && <div className={styles.followupNotes}>{f.notes}</div>}
                    {f.status === 'corrected' && f.corrected_at && (
                      <div className={styles.followupCorrected}>
                        Institucion reporto correccion el {new Date(f.corrected_at).toLocaleDateString('es-BO')}
                      </div>
                    )}
                    {f.validation_notes && (
                      <div className={styles.followupValidationNotes}>Nota validacion: {f.validation_notes}</div>
                    )}
                  </div>

                  <div className={styles.followupRight}>
                    <span style={{
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      color: statusCfg.color,
                      background: `${statusCfg.color}18`,
                      border: `1px solid ${statusCfg.color}`,
                      borderRadius: '4px',
                      padding: '2px 8px',
                    }}>
                      {statusCfg.label}
                    </span>
                    {isAdminOrSecretary && f.status === 'pending' && (
                      <button className={styles.btnSmallGray} onClick={() => handleCancelFollowup(f.id)}>Cancelar</button>
                    )}
                    {canManageFollowups && f.status === 'corrected' && (
                      <>
                        <button className={styles.btnSmallGreen} onClick={() => handleValidateFollowup(f.id, true)}>Validar</button>
                        <button className={styles.btnSmallRed} onClick={() => handleValidateFollowup(f.id, false)}>Rechazar</button>
                      </>
                    )}
                    {isAdminOrSecretary && f.status === 'rejected' && (
                      <button className={styles.btnSmallGray} onClick={() => handleCancelFollowup(f.id)}>Cancelar</button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>

      {showModal && (
        <FollowupModal
          nonCompliant={nonCompliant}
          evaluationId={Number(id)}
          onSave={handleCreateFollowup}
          onClose={() => setShowModal(false)}
        />
      )}
      <Toast message={toast.message} type={toast.type} onClose={() => setToast({ message: '' })} />
    </div>
  );
}
