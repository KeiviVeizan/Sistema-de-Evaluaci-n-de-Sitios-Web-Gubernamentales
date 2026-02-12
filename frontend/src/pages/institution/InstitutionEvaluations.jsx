/**
 * Vista de evaluaciones para usuarios de institución (entity_user).
 *
 * Muestra todas las evaluaciones realizadas al sitio web de la institución
 * del usuario autenticado, con puntajes por dimensión y acceso al detalle.
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import evaluationService from '../../services/evaluationService';

// ── Helpers de estilo ─────────────────────────────────────────────────────────

const SCORE_COLOR = (score) => {
  if (score >= 70) return '#27ae60';
  if (score >= 50) return '#e67e22';
  return '#c0392b';
};

function ScoreBadge({ score }) {
  if (score == null) return <span style={{ color: '#999', fontSize: '0.85rem' }}>—</span>;
  const color = SCORE_COLOR(score);
  return (
    <span style={{
      fontWeight: 700,
      fontSize: '1rem',
      color,
    }}>
      {Number(score).toFixed(1)}%
    </span>
  );
}

function EvaluationCard({ evaluation, onViewDetail }) {
  const date = evaluation.started_at
    ? new Date(evaluation.started_at).toLocaleDateString('es-BO', {
        year: 'numeric', month: 'long', day: 'numeric',
      })
    : '—';

  const score = evaluation.score_total;
  const borderColor = score != null ? SCORE_COLOR(score) : '#c0ccd8';

  return (
    <div style={{
      background: '#fff',
      border: `1px solid ${borderColor}`,
      borderLeft: `4px solid ${borderColor}`,
      borderRadius: '8px',
      padding: '16px 20px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: '16px',
      flexWrap: 'wrap',
    }}>
      <div style={{ flex: 1, minWidth: '200px' }}>
        <div style={{ fontWeight: 700, fontSize: '0.95rem', color: '#1a3a5c', marginBottom: '4px' }}>
          Evaluación #{evaluation.id}
        </div>
        <div style={{ fontSize: '0.82rem', color: '#666' }}>
          {date}
        </div>
        {evaluation.website_url && (
          <div style={{ fontSize: '0.8rem', color: '#888', marginTop: '2px', wordBreak: 'break-all' }}>
            {evaluation.website_url}
          </div>
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '24px', flexWrap: 'wrap' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '0.72rem', color: '#888', marginBottom: '2px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            Puntaje Total
          </div>
          <ScoreBadge score={score} />
        </div>

        <button
          onClick={() => onViewDetail(evaluation.id)}
          style={btnPrimary}
        >
          Ver detalle
        </button>
      </div>
    </div>
  );
}

// ── Componente principal ───────────────────────────────────────────────────────

export default function InstitutionEvaluations() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [evaluations, setEvaluations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (user?.institution_id) {
      loadEvaluations();
    } else {
      setLoading(false);
      setError('Su usuario no tiene una institución asignada. Contacte al administrador.');
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.institution_id]);

  const loadEvaluations = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await evaluationService.getByInstitution(user.institution_id);
      setEvaluations(data);
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(detail || 'Error al cargar las evaluaciones. Intente nuevamente.');
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetail = (evaluationId) => {
    navigate(`/admin/evaluations/${evaluationId}`);
  };

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
        Mis Evaluaciones
      </h1>
      <p style={{ color: '#666', fontSize: '0.9rem', marginBottom: '24px' }}>
        Resultados de evaluaciones realizadas al sitio web de su institución.
      </p>

      {error && (
        <div style={{
          background: '#fdf5f5',
          border: '1px solid #e8c0c0',
          borderLeft: '4px solid #c0392b',
          borderRadius: '8px',
          padding: '14px 18px',
          color: '#c0392b',
          fontSize: '0.9rem',
          marginBottom: '20px',
        }}>
          {error}
        </div>
      )}

      {!error && evaluations.length === 0 && (
        <div style={{ textAlign: 'center', padding: '48px', color: '#999', fontSize: '0.9rem' }}>
          Su institución aún no tiene evaluaciones registradas.
        </div>
      )}

      {evaluations.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {evaluations.map(ev => (
            <EvaluationCard
              key={ev.id}
              evaluation={ev}
              onViewDetail={handleViewDetail}
            />
          ))}
        </div>
      )}
    </div>
  );
}

const btnPrimary = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: '6px',
  background: '#800000',
  color: '#fff',
  border: 'none',
  borderRadius: '6px',
  padding: '8px 16px',
  fontWeight: 600,
  fontSize: '0.85rem',
  cursor: 'pointer',
  whiteSpace: 'nowrap',
};
