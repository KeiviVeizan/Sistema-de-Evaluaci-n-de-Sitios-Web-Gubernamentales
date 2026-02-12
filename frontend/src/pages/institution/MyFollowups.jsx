/**
 * Vista de seguimientos para usuarios de institución (entity_user).
 *
 * Permite a la institución ver sus seguimientos pendientes y marcarlos
 * como corregidos. El admin/secretaría luego valida o rechaza cada corrección.
 *
 * Flujo: pending → corrected (institución) → validated/rejected (admin)
 */

import { useState, useEffect } from 'react';
import followupService from '../../services/followupService';

// ── Helpers de estilo ─────────────────────────────────────────────────────────

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

const STATUS_CONFIG = {
  pending:   { label: 'Pendiente de correccion', color: '#e67e22', bg: '#fef9f0' },
  corrected: { label: 'Esperando validacion',    color: '#2980b9', bg: '#f0f7ff' },
  validated: { label: 'Correccion validada',     color: '#27ae60', bg: '#f0faf4' },
  rejected:  { label: 'Correccion rechazada',    color: '#c0392b', bg: '#fdf5f5' },
  cancelled: { label: 'Cancelado',               color: '#95a5a6', bg: '#f8f9fa' },
};

// ── Modal para ingresar notas de corrección ────────────────────────────────────

function CorrectionModal({ followup, onSave, onClose }) {
  const [notes, setNotes] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const handleSave = async () => {
    setSaving(true);
    setError('');
    try {
      await onSave(followup.id, notes);
      onClose();
    } catch (err) {
      setError(err?.response?.data?.detail || 'Error al guardar');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.45)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, padding: '16px' }}>
      <div style={{ background: '#fff', borderRadius: '10px', padding: '24px', width: '100%', maxWidth: '460px', boxShadow: '0 8px 32px rgba(0,0,0,0.18)' }}>
        <h3 style={{ margin: '0 0 8px', color: '#1a3a5c', fontSize: '1rem', fontWeight: 700 }}>
          Reportar Correccion
        </h3>
        <p style={{ margin: '0 0 16px', fontSize: '0.85rem', color: '#555' }}>
          <strong>{followup.criteria_id}</strong> — {followup.criteria_name}
        </p>
        <label style={{ fontSize: '0.82rem', fontWeight: 600, color: '#1a3a5c', marginBottom: '4px', display: 'block' }}>
          Descripcion de la correccion realizada (opcional)
        </label>
        <textarea
          value={notes}
          onChange={e => setNotes(e.target.value)}
          placeholder="Describa brevemente la correccion aplicada..."
          rows={4}
          style={{ width: '100%', padding: '8px 10px', border: '1px solid #c0ccd8', borderRadius: '6px', fontSize: '0.88rem', boxSizing: 'border-box', resize: 'vertical', fontFamily: 'inherit', color: '#1a3a5c' }}
        />
        {error && <p style={{ color: '#c0392b', fontSize: '0.83rem', margin: '4px 0 0' }}>{error}</p>}
        <div style={{ display: 'flex', gap: '8px', marginTop: '16px', justifyContent: 'flex-end' }}>
          <button onClick={onClose} disabled={saving} style={btnSecondary}>Cancelar</button>
          <button onClick={handleSave} disabled={saving} style={{ ...btnPrimary, opacity: saving ? 0.7 : 1 }}>
            {saving ? 'Guardando...' : 'Confirmar Correccion'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Componente principal ───────────────────────────────────────────────────────

export default function MyFollowups() {
  const [followups, setFollowups] = useState([]);
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
      const data = await followupService.getAll();
      setFollowups(data);
    } catch {
      showToast('Error al cargar los seguimientos', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleMarkCorrected = async (followupId, notes) => {
    const updated = await followupService.markCorrected(followupId, { notes });
    setFollowups(prev => prev.map(f => f.id === followupId ? updated : f));
    showToast('Correccion reportada correctamente. El administrador revisara y validara.');
  };

  const filtered = filter === 'all'
    ? followups
    : followups.filter(f => f.status === filter);

  const counts = followups.reduce((acc, f) => {
    acc[f.status] = (acc[f.status] || 0) + 1;
    return acc;
  }, {});

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <div style={{ width: '40px', height: '40px', border: '4px solid #e0e0e0', borderTopColor: '#800000', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
        <style>{'@keyframes spin { to { transform: rotate(360deg); } }'}</style>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '860px', margin: '0 auto', padding: '24px 16px' }}>
      <h1 style={{ fontSize: '1.4rem', fontWeight: 700, color: '#1a3a5c', marginBottom: '4px' }}>
        Mis Seguimientos
      </h1>
      <p style={{ color: '#666', fontSize: '0.9rem', marginBottom: '24px' }}>
        Criterios que requieren correccion en el sitio web de su institucion.
      </p>

      {/* Resumen de estados */}
      <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginBottom: '20px' }}>
        {[
          { key: 'all',       label: 'Todos',     color: '#2c5f8a' },
          { key: 'pending',   label: 'Pendientes', color: '#e67e22' },
          { key: 'corrected', label: 'Reportados', color: '#2980b9' },
          { key: 'validated', label: 'Validados',  color: '#27ae60' },
          { key: 'rejected',  label: 'Rechazados', color: '#c0392b' },
        ].map(({ key, label, color }) => {
          const count = key === 'all' ? followups.length : (counts[key] || 0);
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

      {filtered.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '48px', color: '#999', fontSize: '0.9rem' }}>
          {followups.length === 0
            ? 'No tiene seguimientos asignados actualmente.'
            : 'No hay seguimientos con el filtro seleccionado.'}
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {filtered.map(f => {
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
                    Indicaciones: {f.notes}
                  </div>
                )}

                {/* Info de corrección reportada */}
                {f.corrected_at && (
                  <div style={{ fontSize: '0.8rem', color: '#2980b9', marginTop: '8px' }}>
                    Correccion reportada el {new Date(f.corrected_at).toLocaleDateString('es-BO')}
                  </div>
                )}

                {/* Nota de rechazo */}
                {f.status === 'rejected' && f.validation_notes && (
                  <div style={{ marginTop: '10px', padding: '8px 12px', background: '#fdf5f5', border: '1px solid #e8c0c0', borderRadius: '6px', fontSize: '0.82rem', color: '#c0392b' }}>
                    <strong>Motivo del rechazo:</strong> {f.validation_notes}
                  </div>
                )}

                {/* Nota de validacion */}
                {f.status === 'validated' && f.validation_notes && (
                  <div style={{ marginTop: '10px', padding: '8px 12px', background: '#f0faf4', border: '1px solid #a8dfc0', borderRadius: '6px', fontSize: '0.82rem', color: '#27ae60' }}>
                    <strong>Comentario del administrador:</strong> {f.validation_notes}
                  </div>
                )}

                {/* Acciones según estado */}
                <div style={{ marginTop: '12px' }}>
                  {(f.status === 'pending' || f.status === 'rejected') && (
                    <button
                      onClick={() => setModalFollowup(f)}
                      style={btnPrimary}
                    >
                      {f.status === 'rejected' ? 'Volver a reportar correccion' : 'Marcar como Corregido'}
                    </button>
                  )}

                  {f.status === 'corrected' && (
                    <p style={{ margin: 0, fontSize: '0.85rem', color: '#2980b9', fontStyle: 'italic' }}>
                      Su correccion fue reportada y esta esperando revision del administrador.
                    </p>
                  )}

                  {f.status === 'validated' && (
                    <p style={{ margin: 0, fontSize: '0.85rem', color: '#27ae60', fontWeight: 600 }}>
                      La correccion fue verificada y validada por el administrador.
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Modal de corrección */}
      {modalFollowup && (
        <CorrectionModal
          followup={modalFollowup}
          onSave={handleMarkCorrected}
          onClose={() => setModalFollowup(null)}
        />
      )}

      <Toast message={toast.message} type={toast.type} onClose={() => setToast({ message: '' })} />
    </div>
  );
}

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
