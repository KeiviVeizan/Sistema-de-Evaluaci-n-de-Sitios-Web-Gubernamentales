/**
 * Vista de seguimientos para evaluadores.
 *
 * Muestra los seguimientos de todas las evaluaciones que el evaluador realizó,
 * agrupados por institución. Permite validar o rechazar correcciones reportadas.
 *
 * Flujo: pending → corrected (institución) → validated/rejected (evaluador)
 */

import { useState, useEffect } from 'react';
import evaluationService from '../../services/evaluationService';
import followupService from '../../services/followupService';

// ── Helpers de estilo ─────────────────────────────────────────────────────────

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

const STATUS_CONFIG = {
  pending:   { label: 'Pendiente de corrección', color: '#e67e22', bg: '#fef9f0' },
  corrected: { label: 'Esperando validación',    color: '#2980b9', bg: '#f0f7ff' },
  validated: { label: 'Corrección validada',     color: '#27ae60', bg: '#f0faf4' },
  rejected:  { label: 'Corrección rechazada',    color: '#c0392b', bg: '#fdf5f5' },
  cancelled: { label: 'Cancelado',               color: '#95a5a6', bg: '#f8f9fa' },
};

// ── Modal para validar o rechazar corrección ───────────────────────────────────

function ValidationModal({ followup, onValidate, onClose }) {
  const [action, setAction] = useState('approve'); // 'approve' o 'reject'
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
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.45)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, padding: '16px' }}>
      <div style={{ background: '#fff', borderRadius: '10px', padding: '24px', width: '100%', maxWidth: '500px', boxShadow: '0 8px 32px rgba(0,0,0,0.18)' }}>
        <h3 style={{ margin: '0 0 8px', color: '#1a3a5c', fontSize: '1rem', fontWeight: 700 }}>
          Validar Corrección
        </h3>
        <p style={{ margin: '0 0 16px', fontSize: '0.85rem', color: '#555' }}>
          <strong>{followup.criteria_id}</strong> — {followup.criteria_name}
        </p>

        {/* Acción: Aprobar o Rechazar */}
        <div style={{ marginBottom: '16px' }}>
          <label style={{ fontSize: '0.82rem', fontWeight: 600, color: '#1a3a5c', marginBottom: '8px', display: 'block' }}>
            Decisión
          </label>
          <div style={{ display: 'flex', gap: '12px' }}>
            <button
              onClick={() => setAction('approve')}
              style={{
                ...btnToggle,
                background: action === 'approve' ? '#27ae60' : 'transparent',
                color: action === 'approve' ? '#fff' : '#27ae60',
                borderColor: '#27ae60',
              }}
            >
              ✓ Aprobar corrección
            </button>
            <button
              onClick={() => setAction('reject')}
              style={{
                ...btnToggle,
                background: action === 'reject' ? '#c0392b' : 'transparent',
                color: action === 'reject' ? '#fff' : '#c0392b',
                borderColor: '#c0392b',
              }}
            >
              ✗ Rechazar corrección
            </button>
          </div>
        </div>

        {/* Notas/Comentarios */}
        <label style={{ fontSize: '0.82rem', fontWeight: 600, color: '#1a3a5c', marginBottom: '4px', display: 'block' }}>
          Comentarios {action === 'reject' && <span style={{ color: '#c0392b' }}>(obligatorio si rechaza)</span>}
        </label>
        <textarea
          value={notes}
          onChange={e => setNotes(e.target.value)}
          placeholder={action === 'approve' ? 'Comentarios adicionales (opcional)' : 'Explique el motivo del rechazo...'}
          rows={4}
          style={{ width: '100%', padding: '8px 10px', border: '1px solid #c0ccd8', borderRadius: '6px', fontSize: '0.88rem', boxSizing: 'border-box', resize: 'vertical', fontFamily: 'inherit', color: '#1a3a5c' }}
        />

        {error && <p style={{ color: '#c0392b', fontSize: '0.83rem', margin: '4px 0 0' }}>{error}</p>}

        <div style={{ display: 'flex', gap: '8px', marginTop: '16px', justifyContent: 'flex-end' }}>
          <button onClick={onClose} disabled={saving} style={btnSecondary}>Cancelar</button>
          <button
            onClick={handleSave}
            disabled={saving || (action === 'reject' && !notes.trim())}
            style={{
              ...btnPrimary,
              opacity: (saving || (action === 'reject' && !notes.trim())) ? 0.5 : 1,
              background: action === 'approve' ? '#27ae60' : '#c0392b',
            }}
          >
            {saving ? 'Guardando...' : (action === 'approve' ? 'Aprobar' : 'Rechazar')}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Componente principal ───────────────────────────────────────────────────────

export default function EvaluatorFollowups() {
  const [followupsByInstitution, setFollowupsByInstitution] = useState({});
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [modalFollowup, setModalFollowup] = useState(null);
  const [toast, setToast] = useState({ message: '', type: 'success' });

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast({ message: '', type: 'success' }), 5000);
  };

  useEffect(() => {
    loadFollowups();
  }, []);

  const loadFollowups = async () => {
    try {
      setLoading(true);

      // 1. Obtener mis evaluaciones
      const myEvaluations = await evaluationService.getMyEvaluations();
      const myEvaluationIds = myEvaluations.map(ev => ev.id);

      if (myEvaluationIds.length === 0) {
        setFollowupsByInstitution({});
        setLoading(false);
        return;
      }

      // 2. Obtener todos los seguimientos
      const allFollowups = await followupService.getAll();

      // 3. Filtrar solo los seguimientos de mis evaluaciones
      const myFollowups = allFollowups.filter(f =>
        myEvaluationIds.includes(f.evaluation_id)
      );

      // 4. Agrupar por institución
      const grouped = {};
      for (const followup of myFollowups) {
        const evaluation = myEvaluations.find(ev => ev.id === followup.evaluation_id);
        const institutionName = evaluation?.institution_name || 'Institución desconocida';

        if (!grouped[institutionName]) {
          grouped[institutionName] = [];
        }
        grouped[institutionName].push(followup);
      }

      setFollowupsByInstitution(grouped);
    } catch (error) {
      console.error('Error cargando seguimientos:', error);
      showToast('Error al cargar los seguimientos', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleValidate = async (followupId, approved, notes) => {
    try {
      await followupService.validate(followupId, { approved, notes });
      await loadFollowups(); // Recargar datos
      showToast(
        approved
          ? 'Corrección aprobada exitosamente'
          : 'Corrección rechazada. La institución deberá volver a corregir.',
        'success'
      );
    } catch (error) {
      throw error; // Propagar el error al modal
    }
  };

  // Calcular contadores totales
  const allFollowups = Object.values(followupsByInstitution).flat();
  const counts = allFollowups.reduce((acc, f) => {
    acc[f.status] = (acc[f.status] || 0) + 1;
    return acc;
  }, {});

  // Filtrar instituciones basado en el filtro de estado
  const filteredInstitutions = {};
  Object.entries(followupsByInstitution).forEach(([institution, followups]) => {
    const filtered = filter === 'all'
      ? followups
      : followups.filter(f => f.status === filter);

    if (filtered.length > 0) {
      filteredInstitutions[institution] = filtered;
    }
  });

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <div style={{ width: '40px', height: '40px', border: '4px solid #e0e0e0', borderTopColor: '#800000', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
        <style>{'@keyframes spin { to { transform: rotate(360deg); } }'}</style>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '920px', margin: '0 auto', padding: '24px 16px' }}>
      <h1 style={{ fontSize: '1.4rem', fontWeight: 700, color: '#1a3a5c', marginBottom: '4px' }}>
        Mis Seguimientos
      </h1>
      <p style={{ color: '#666', fontSize: '0.9rem', marginBottom: '24px' }}>
        Seguimientos de las evaluaciones que has realizado, agrupados por institución.
      </p>

      {/* Resumen de estados */}
      <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginBottom: '20px' }}>
        {[
          { key: 'all',       label: 'Todos',              color: '#2c5f8a' },
          { key: 'pending',   label: 'Pendientes',         color: '#e67e22' },
          { key: 'corrected', label: 'Por validar',        color: '#2980b9' },
          { key: 'validated', label: 'Validados',          color: '#27ae60' },
          { key: 'rejected',  label: 'Rechazados',         color: '#c0392b' },
        ].map(({ key, label, color }) => {
          const count = key === 'all' ? allFollowups.length : (counts[key] || 0);
          const active = filter === key;
          return (
            <button
              key={key}
              onClick={() => setFilter(key)}
              style={{
                background: active ? color : 'transparent',
                color: active ? '#fff' : color,
                border: `1px solid ${color}`,
                borderRadius: '20px',
                padding: '4px 14px',
                fontSize: '0.82rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              {label} ({count})
            </button>
          );
        })}
      </div>

      {Object.keys(filteredInstitutions).length === 0 ? (
        <div style={{ textAlign: 'center', padding: '48px', color: '#999', fontSize: '0.9rem' }}>
          {allFollowups.length === 0
            ? 'No tienes seguimientos asignados actualmente.'
            : 'No hay seguimientos con el filtro seleccionado.'}
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {Object.entries(filteredInstitutions).map(([institutionName, followups]) => (
            <div key={institutionName} style={{ background: '#fff', border: '1px solid #e0e0e0', borderRadius: '10px', padding: '20px', boxShadow: '0 2px 8px rgba(0,0,0,0.05)' }}>
              {/* Título de institución */}
              <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#1a3a5c', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '1.3rem' }}>🏛️</span>
                {institutionName}
                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#666', background: '#f0f0f0', padding: '2px 8px', borderRadius: '12px' }}>
                  {followups.length} seguimiento{followups.length > 1 ? 's' : ''}
                </span>
              </h2>

              {/* Lista de seguimientos */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {followups.map(f => {
                  const cfg = STATUS_CONFIG[f.status] || STATUS_CONFIG.pending;
                  const overdue = f.status === 'pending' && new Date(f.due_date) < new Date();

                  return (
                    <div
                      key={f.id}
                      style={{
                        background: cfg.bg,
                        border: `1px solid ${overdue ? '#c0392b' : cfg.color}`,
                        borderLeft: `4px solid ${overdue ? '#c0392b' : cfg.color}`,
                        borderRadius: '8px',
                        padding: '16px',
                      }}
                    >
                      {/* Cabecera */}
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '12px', flexWrap: 'wrap' }}>
                        <div style={{ flex: 1 }}>
                          <div style={{ fontWeight: 700, fontSize: '0.9rem', color: '#1a3a5c' }}>
                            <code style={{ fontSize: '0.82rem', marginRight: '6px', background: '#e8edf2', padding: '1px 5px', borderRadius: '3px' }}>
                              {f.criteria_id}
                            </code>
                            {f.criteria_name}
                          </div>
                          <div style={{ fontSize: '0.8rem', color: overdue ? '#c0392b' : '#666', marginTop: '6px' }}>
                            Vence: {new Date(f.due_date).toLocaleDateString('es-BO')}
                            {overdue && (
                              <span style={{ marginLeft: '8px', fontWeight: 700, color: '#c0392b' }}>VENCIDO</span>
                            )}
                          </div>
                        </div>
                        {/* Badge de estado */}
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

                      {/* Notas del seguimiento */}
                      {f.notes && (
                        <div style={{ fontSize: '0.82rem', color: '#444', marginTop: '10px', fontStyle: 'italic', borderTop: '1px solid #e0e0e0', paddingTop: '8px' }}>
                          Observaciones: {f.notes}
                        </div>
                      )}

                      {/* Info de corrección reportada */}
                      {f.corrected_at && (
                        <div style={{ fontSize: '0.8rem', color: '#2980b9', marginTop: '8px', background: '#f0f7ff', padding: '8px', borderRadius: '4px' }}>
                          ✓ Corrección reportada el {new Date(f.corrected_at).toLocaleDateString('es-BO')}
                        </div>
                      )}

                      {/* Nota de validación */}
                      {f.status === 'validated' && f.validation_notes && (
                        <div style={{ marginTop: '10px', padding: '8px 12px', background: '#f0faf4', border: '1px solid #a8dfc0', borderRadius: '6px', fontSize: '0.82rem', color: '#27ae60' }}>
                          <strong>Tu comentario:</strong> {f.validation_notes}
                        </div>
                      )}

                      {/* Nota de rechazo */}
                      {f.status === 'rejected' && f.validation_notes && (
                        <div style={{ marginTop: '10px', padding: '8px 12px', background: '#fdf5f5', border: '1px solid #e8c0c0', borderRadius: '6px', fontSize: '0.82rem', color: '#c0392b' }}>
                          <strong>Motivo del rechazo:</strong> {f.validation_notes}
                        </div>
                      )}

                      {/* Acciones según estado */}
                      <div style={{ marginTop: '12px' }}>
                        {f.status === 'corrected' && (
                          <button
                            onClick={() => setModalFollowup(f)}
                            style={btnValidate}
                          >
                            📋 Revisar y validar corrección
                          </button>
                        )}

                        {f.status === 'pending' && (
                          <p style={{ margin: 0, fontSize: '0.85rem', color: '#e67e22', fontStyle: 'italic' }}>
                            Esperando que la institución reporte la corrección.
                          </p>
                        )}

                        {f.status === 'validated' && (
                          <p style={{ margin: 0, fontSize: '0.85rem', color: '#27ae60', fontWeight: 600 }}>
                            ✓ Corrección validada exitosamente.
                          </p>
                        )}

                        {f.status === 'rejected' && (
                          <p style={{ margin: 0, fontSize: '0.85rem', color: '#c0392b', fontStyle: 'italic' }}>
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

      {/* Modal de validación */}
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

// ── Estilos ────────────────────────────────────────────────────────────────────

const btnPrimary = {
  display: 'inline-flex', alignItems: 'center', gap: '6px',
  background: '#800000', color: '#fff', border: 'none',
  borderRadius: '6px', padding: '8px 16px',
  fontWeight: 600, fontSize: '0.85rem', cursor: 'pointer',
};

const btnSecondary = {
  display: 'inline-flex', alignItems: 'center', gap: '6px',
  background: 'transparent', color: '#2c5f8a', border: '1px solid #2c5f8a',
  borderRadius: '6px', padding: '7px 14px',
  fontWeight: 600, fontSize: '0.85rem', cursor: 'pointer',
};

const btnValidate = {
  display: 'inline-flex', alignItems: 'center', gap: '6px',
  background: '#2980b9', color: '#fff', border: 'none',
  borderRadius: '6px', padding: '8px 16px',
  fontWeight: 600, fontSize: '0.85rem', cursor: 'pointer',
};

const btnToggle = {
  flex: 1,
  padding: '10px 16px',
  border: '2px solid',
  borderRadius: '6px',
  fontSize: '0.85rem',
  fontWeight: 600,
  cursor: 'pointer',
  transition: 'all 0.2s',
};
