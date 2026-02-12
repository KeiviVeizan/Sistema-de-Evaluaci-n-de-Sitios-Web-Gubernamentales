import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Download, ArrowLeft, CheckCircle, XCircle, AlertCircle, MinusCircle, Calendar } from 'lucide-react';
import evaluationService from '../../services/evaluationService';
import followupService from '../../services/followupService';
import { useAuth } from '../../contexts/AuthContext';

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

const DIMENSION_LABELS = { accesibilidad: 'Accesibilidad', usabilidad: 'Usabilidad', semantica_tecnica: 'Semantica Tecnica', semantica_nlp: 'Semantica NLP', soberania: 'Soberania Digital' };
const FOLLOWUP_STATUS_LABELS = {
  pending:   { label: 'Pendiente',             color: '#e67e22' },
  corrected: { label: 'Corregido (pendiente)', color: '#2980b9' },
  validated: { label: 'Validado',              color: '#27ae60' },
  rejected:  { label: 'Rechazado',             color: '#c0392b' },
  cancelled: { label: 'Cancelado',             color: '#95a5a6' },
};

function scoreColor(pct) { if (pct >= 80) return '#27ae60'; if (pct >= 50) return '#e67e22'; return '#c0392b'; }

function StatusBadge({ status }) {
  const config = {
    pass:    { label: 'CUMPLE',    color: '#27ae60', Icon: CheckCircle  },
    fail:    { label: 'NO CUMPLE', color: '#c0392b', Icon: XCircle      },
    partial: { label: 'PARCIAL',   color: '#e67e22', Icon: AlertCircle  },
    na:      { label: 'N/A',       color: '#95a5a6', Icon: MinusCircle  },
  };
  const { label, color, Icon } = config[status] || config.na;
  return <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', color, fontWeight: 600, fontSize: '0.78rem' }}><Icon size={14} />{label}</span>;
}

function FollowupModal({ nonCompliant, evaluationId, onSave, onClose }) {
  const [criteriaResultId, setCriteriaResultId] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [notes, setNotes] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const handleSave = async () => {
    if (!criteriaResultId) { setError('Seleccione un criterio'); return; }
    if (!dueDate)          { setError('Seleccione una fecha de vencimiento'); return; }
    const payload = { evaluation_id: evaluationId, criteria_result_id: Number(criteriaResultId), due_date: dueDate, notes };
    setSaving(true);
    setError('');
    try {
      await onSave(payload);
      onClose();
    } catch (err) {
      setError(err?.response?.data?.detail || 'Error al guardar el seguimiento');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={modalOverlay}>
      <div style={modalBox}>
        <h3 style={{ margin: '0 0 16px', color: '#1a3a5c', fontSize: '1rem', fontWeight: 700 }}>Programar Seguimiento</h3>
        <label style={labelStyle}>Criterio *</label>
        <select value={criteriaResultId} onChange={e => setCriteriaResultId(e.target.value)} style={inputStyle}>
          <option value="">Seleccionar criterio...</option>
          {nonCompliant.map(c => (
            <option key={c.id} value={c.id}>{c.criteria_id} - {c.criteria_name}</option>
          ))}
        </select>
        <label style={labelStyle}>Fecha de vencimiento *</label>
        <input type="date" value={dueDate} onChange={e => setDueDate(e.target.value)} style={inputStyle} min={new Date().toISOString().split('T')[0]} />
        <label style={labelStyle}>Notas</label>
        <textarea value={notes} onChange={e => setNotes(e.target.value)} placeholder="Observaciones o acciones requeridas..." rows={3} style={{ ...inputStyle, resize: 'vertical', fontFamily: 'inherit' }} />
        {error && <p style={{ color: '#c0392b', fontSize: '0.83rem', margin: '4px 0 0' }}>{error}</p>}
        <div style={{ display: 'flex', gap: '8px', marginTop: '16px', justifyContent: 'flex-end' }}>
          <button onClick={onClose} style={btnSecondary} disabled={saving}>Cancelar</button>
          <button onClick={handleSave} style={{ ...btnPrimary, opacity: saving ? 0.7 : 1 }} disabled={saving}>{saving ? 'Guardando...' : 'Guardar'}</button>
        </div>
      </div>
    </div>
  );
}

export default function EvaluationDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const isAdminOrSecretary = user?.role === 'admin' || user?.role === 'superadmin' || user?.role === 'secretary' || user?.role === 'evaluator';
  const [evaluation, setEvaluation] = useState(null);
  const [loading, setLoading]       = useState(true);
  const [downloading, setDownloading] = useState(false);
  const [toast, setToast]           = useState({ message: '', type: 'success' });
  const [followups, setFollowups]   = useState([]);
  const [showModal, setShowModal]   = useState(false);

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
    try { await evaluationService.downloadReport(id); showToast('Informe PDF descargado correctamente'); }
    catch { showToast('Error al generar el informe PDF', 'error'); }
    finally { setDownloading(false); }
  };

  const handleCreateFollowup = async (data) => {
    try {
      const created = await followupService.create(data);
      setFollowups(prev => [...prev, created]);
      showToast('Seguimiento programado correctamente');
    } catch (err) { throw err; }
  };

  const handleValidateFollowup = async (followupId, approved) => {
    try {
      const updated = await followupService.validate(followupId, { approved, notes: '' });
      setFollowups(prev => prev.map(f => f.id === followupId ? updated : f));
      showToast(approved ? 'Correccion validada correctamente' : 'Correccion rechazada');
    } catch { showToast('Error al validar el seguimiento', 'error'); }
  };

  const handleCancelFollowup = async (followupId) => {
    try {
      const updated = await followupService.cancel(followupId);
      setFollowups(prev => prev.map(f => f.id === followupId ? updated : f));
      showToast('Seguimiento cancelado');
    } catch { showToast('Error al cancelar el seguimiento', 'error'); }
  };

  if (loading) return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
      <div style={{ width: '40px', height: '40px', border: '4px solid #e0e0e0', borderTopColor: '#800000', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
      <style>{'@keyframes spin { to { transform: rotate(360deg); } }'}</style>
    </div>
  );

  if (!evaluation) return (
    <div style={{ textAlign: 'center', padding: '48px' }}>
      <p style={{ color: '#666' }}>No se encontro la evaluacion.</p>
      <button onClick={() => navigate(-1)} style={btnSecondary}><ArrowLeft size={16} /> Volver</button>
    </div>
  );

  const scores = evaluation.scores || {};
  const totalScore = typeof scores.total === 'number' ? scores.total : 0;
  const criteriaResults = evaluation.criteria_results || [];
  const failedCriteria  = criteriaResults.filter(c => c.status === 'fail');
  const partialCriteria = criteriaResults.filter(c => c.status === 'partial');
  const nonCompliant    = [...failedCriteria, ...partialCriteria];
  const passed  = criteriaResults.filter(c => c.status === 'pass').length;
  const failed  = failedCriteria.length;
  const partial = partialCriteria.length;
  const na      = criteriaResults.filter(c => c.status === 'na').length;
  const evalDate = evaluation.timestamp ? new Date(evaluation.timestamp).toLocaleString('es-BO') : '-';

  return (
    <div style={{ maxWidth: '960px', margin: '0 auto', padding: '24px 16px' }}>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px', flexWrap: 'wrap', gap: '12px' }}>
        <button onClick={() => navigate(-1)} style={btnSecondary}><ArrowLeft size={16} /> Volver</button>
        <button onClick={handleDownloadReport} disabled={downloading} style={{ ...btnPrimary, opacity: downloading ? 0.7 : 1, cursor: downloading ? 'not-allowed' : 'pointer' }}>
          {downloading ? (<><span style={spinnerStyle} />Generando PDF...</>) : (<><Download size={16} />Descargar Informe PDF</>)}
        </button>
      </div>

      <h1 style={{ fontSize: '1.4rem', fontWeight: 700, color: '#1a3a5c', marginBottom: '4px' }}>Detalle de Evaluacion #{id}</h1>
      <p style={{ color: '#666', fontSize: '0.9rem', marginBottom: '24px' }}>URL evaluada: <strong>{evaluation.url || '-'}</strong> &nbsp;&middot;&nbsp; Fecha: {evalDate}</p>

      <div style={{ background: '#f0f5fa', border: `2px solid ${scoreColor(totalScore)}`, borderRadius: '10px', padding: '16px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px', flexWrap: 'wrap', gap: '12px' }}>
        <span style={{ fontWeight: 600, color: '#1a3a5c', fontSize: '1rem' }}>Puntaje Total de Cumplimiento</span>
        <span style={{ fontSize: '2rem', fontWeight: 700, color: scoreColor(totalScore) }}>{totalScore.toFixed(1)}%</span>
      </div>

      <section style={sectionStyle}>
        <h2 style={sectionTitle}>Puntajes por Dimension</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(170px, 1fr))', gap: '12px' }}>
          {Object.entries(DIMENSION_LABELS).map(([key, label]) => {
            const raw = scores[key];
            const pct = typeof raw === 'object' ? (raw?.percentage ?? 0) : (typeof raw === 'number' ? raw : 0);
            return (
              <div key={key} style={{ background: '#fff', border: '1px solid #d0dce8', borderRadius: '8px', padding: '14px', textAlign: 'center' }}>
                <div style={{ fontSize: '0.75rem', color: '#555', marginBottom: '6px' }}>{label}</div>
                <div style={{ fontSize: '1.5rem', fontWeight: 700, color: scoreColor(pct) }}>{pct.toFixed(1)}%</div>
              </div>
            );
          })}
        </div>
      </section>

      <section style={sectionStyle}>
        <h2 style={sectionTitle}>Resumen de Criterios</h2>
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          {[
            { label: 'Total',     value: criteriaResults.length, color: '#2c5f8a' },
            { label: 'Cumple',    value: passed,  color: '#27ae60' },
            { label: 'No cumple', value: failed,  color: '#c0392b' },
            { label: 'Parcial',   value: partial, color: '#e67e22' },
            { label: 'N/A',       value: na,      color: '#95a5a6' },
          ].map(({ label, value, color }) => (
            <div key={label} style={{ background: '#fff', border: `1px solid ${color}`, borderRadius: '8px', padding: '10px 18px', textAlign: 'center', minWidth: '80px' }}>
              <div style={{ fontSize: '1.4rem', fontWeight: 700, color }}>{value}</div>
              <div style={{ fontSize: '0.75rem', color: '#555' }}>{label}</div>
            </div>
          ))}
        </div>
      </section>

      <section style={sectionStyle}>
        <h2 style={sectionTitle}>Criterios No Cumplidos / Parciales</h2>
        {nonCompliant.length === 0 ? (
          <p style={{ color: '#27ae60', fontWeight: 600 }}>Todos los criterios han sido cumplidos satisfactoriamente.</p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ background: '#2c5f8a', color: '#fff' }}>
                  <th style={th}>ID</th><th style={th}>Criterio</th><th style={th}>Dimension</th><th style={th}>Estado</th><th style={th}>Observaciones</th>
                </tr>
              </thead>
              <tbody>
                {nonCompliant.map((cr, i) => {
                  const obs = cr.details?.observations || cr.details?.message || cr.details?.error || '';
                  const obsText = Array.isArray(obs) ? obs.slice(0, 3).join('; ') : String(obs || '-');
                  const dimLabel = DIMENSION_LABELS[cr.dimension] || cr.dimension || '';
                  return (
                    <tr key={cr.criteria_id || i} style={{ background: i % 2 === 0 ? '#f0f5fa' : '#fff' }}>
                      <td style={td}><code style={{ fontSize: '0.78rem' }}>{cr.criteria_id}</code></td>
                      <td style={td}>{cr.criteria_name}</td>
                      <td style={td}>{dimLabel}</td>
                      <td style={{ ...td, textAlign: 'center' }}><StatusBadge status={cr.status} /></td>
                      <td style={{ ...td, color: '#555', fontStyle: 'italic', maxWidth: '220px' }}>{obsText.length > 150 ? obsText.slice(0, 150) + '...' : obsText}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section style={sectionStyle}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px', flexWrap: 'wrap', gap: '8px' }}>
          <h2 style={{ ...sectionTitle, marginBottom: 0 }}>Seguimientos Programados</h2>
          {isAdminOrSecretary && nonCompliant.length > 0 && (
            <button onClick={() => setShowModal(true)} style={{ ...btnPrimary, padding: '8px 14px', fontSize: '0.85rem' }}>
              <Calendar size={14} /> + Programar Seguimiento
            </button>
          )}
        </div>
        {followups.length === 0 ? (
          <p style={{ color: '#999', fontSize: '0.88rem' }}>No hay seguimientos programados para esta evaluacion.</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {followups.map(f => {
              const statusCfg = FOLLOWUP_STATUS_LABELS[f.status] || FOLLOWUP_STATUS_LABELS.pending;
              const overdue = f.status === 'pending' && new Date(f.due_date) < new Date();
              return (
                <div key={f.id} style={{ background: '#f8fafc', border: `1px solid ${overdue ? '#c0392b' : '#d0dce8'}`, borderRadius: '8px', padding: '12px 16px', display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '12px', flexWrap: 'wrap' }}>
                  <div style={{ flex: 1, minWidth: '200px' }}>
                    <div style={{ fontWeight: 600, fontSize: '0.88rem', color: '#1a3a5c' }}>
                      <code style={{ fontSize: '0.8rem', marginRight: '6px' }}>{f.criteria_id}</code>{f.criteria_name}
                    </div>
                    <div style={{ fontSize: '0.8rem', color: overdue ? '#c0392b' : '#666', marginTop: '4px' }}>
                      Vence: {new Date(f.due_date).toLocaleDateString('es-BO')}
                      {overdue && <span style={{ marginLeft: '6px', fontWeight: 600 }}> - VENCIDO</span>}
                    </div>
                    {f.notes && <div style={{ fontSize: '0.8rem', color: '#555', marginTop: '4px', fontStyle: 'italic' }}>{f.notes}</div>}
                    {f.status === 'corrected' && f.corrected_at && (
                      <div style={{ fontSize: '0.78rem', color: '#2980b9', marginTop: '4px' }}>
                        Institucion reporto correccion el {new Date(f.corrected_at).toLocaleDateString('es-BO')}
                      </div>
                    )}
                    {f.validation_notes && (
                      <div style={{ fontSize: '0.78rem', color: '#666', marginTop: '4px', fontStyle: 'italic' }}>
                        Nota validacion: {f.validation_notes}
                      </div>
                    )}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0, flexWrap: 'wrap' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: 700, color: statusCfg.color, background: `${statusCfg.color}18`, border: `1px solid ${statusCfg.color}`, borderRadius: '4px', padding: '2px 8px' }}>{statusCfg.label}</span>
                    {isAdminOrSecretary && f.status === 'pending' && (
                      <button onClick={() => handleCancelFollowup(f.id)} style={btnSmallGray}>Cancelar</button>
                    )}
                    {isAdminOrSecretary && f.status === 'corrected' && (
                      <>
                        <button onClick={() => handleValidateFollowup(f.id, true)} style={btnSmallGreen}>Validar</button>
                        <button onClick={() => handleValidateFollowup(f.id, false)} style={btnSmallRed}>Rechazar</button>
                      </>
                    )}
                    {isAdminOrSecretary && f.status === 'rejected' && (
                      <button onClick={() => handleCancelFollowup(f.id)} style={btnSmallGray}>Cancelar</button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>

      {showModal && (
        <FollowupModal nonCompliant={nonCompliant} evaluationId={Number(id)} onSave={handleCreateFollowup} onClose={() => setShowModal(false)} />
      )}
      <Toast message={toast.message} type={toast.type} onClose={() => setToast({ message: '' })} />
    </div>
  );
}

const btnPrimary = { display: 'inline-flex', alignItems: 'center', gap: '8px', background: '#800000', color: '#fff', border: 'none', borderRadius: '8px', padding: '10px 18px', fontWeight: 600, fontSize: '0.9rem', cursor: 'pointer' };
const btnSecondary = { display: 'inline-flex', alignItems: 'center', gap: '6px', background: 'transparent', color: '#2c5f8a', border: '1px solid #2c5f8a', borderRadius: '8px', padding: '8px 14px', fontWeight: 600, fontSize: '0.88rem', cursor: 'pointer' };
const btnSmallGreen = { background: 'transparent', color: '#27ae60', border: '1px solid #27ae60', borderRadius: '5px', padding: '3px 10px', fontSize: '0.78rem', fontWeight: 600, cursor: 'pointer' };
const btnSmallRed   = { background: 'transparent', color: '#c0392b', border: '1px solid #c0392b', borderRadius: '5px', padding: '3px 10px', fontSize: '0.78rem', fontWeight: 600, cursor: 'pointer' };
const btnSmallGray  = { background: 'transparent', color: '#95a5a6', border: '1px solid #95a5a6', borderRadius: '5px', padding: '3px 10px', fontSize: '0.78rem', fontWeight: 600, cursor: 'pointer' };
const spinnerStyle = { display: 'inline-block', width: '14px', height: '14px', border: '2px solid rgba(255,255,255,0.4)', borderTopColor: '#fff', borderRadius: '50%', animation: 'spin 0.7s linear infinite' };
const sectionStyle = { background: '#fff', border: '1px solid #d0dce8', borderRadius: '10px', padding: '20px', marginBottom: '20px' };
const sectionTitle = { fontSize: '1rem', fontWeight: 700, color: '#1a3a5c', marginBottom: '14px', marginTop: 0 };
const th = { padding: '10px 12px', textAlign: 'left', fontWeight: 600, fontSize: '0.82rem', whiteSpace: 'nowrap' };
const td = { padding: '8px 12px', borderBottom: '1px solid #e8edf2', verticalAlign: 'top' };
const modalOverlay = { position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.45)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, padding: '16px' };
const modalBox = { background: '#fff', borderRadius: '10px', padding: '24px', width: '100%', maxWidth: '460px', boxShadow: '0 8px 32px rgba(0,0,0,0.18)', display: 'flex', flexDirection: 'column' };
const labelStyle = { fontSize: '0.82rem', fontWeight: 600, color: '#1a3a5c', marginTop: '12px', marginBottom: '4px', display: 'block' };
const inputStyle = { width: '100%', padding: '8px 10px', border: '1px solid #c0ccd8', borderRadius: '6px', fontSize: '0.88rem', boxSizing: 'border-box', color: '#1a3a5c' };
