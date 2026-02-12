import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import evaluationService from '../../services/evaluationService';

function MyEvaluations() {
  const navigate = useNavigate();
  const [evaluations, setEvaluations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadMyEvaluations();
  }, []);

  const loadMyEvaluations = async () => {
    try {
      setError(null);
      const data = await evaluationService.getMyEvaluations();
      setEvaluations(data);
    } catch (err) {
      console.error('Error cargando evaluaciones:', err);
      setError('No se pudieron cargar las evaluaciones. Intente de nuevo.');
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return '#15803d';
    if (score >= 60) return '#b45309';
    return '#b91c1c';
  };

  const getScoreBg = (score) => {
    if (score >= 80) return '#dcfce7';
    if (score >= 60) return '#fef3c7';
    return '#fee2e2';
  };

  return (
    <div style={{ padding: '24px', maxWidth: '900px', margin: '0 auto' }}>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700, margin: 0, color: '#111827' }}>
          Mis Evaluaciones
        </h1>
        <p style={{ color: '#6b7280', marginTop: '4px', marginBottom: 0 }}>
          Evaluaciones que has realizado y sus seguimientos
        </p>
      </div>

      {loading && (
        <div style={{ textAlign: 'center', padding: '48px', color: '#6b7280' }}>
          Cargando evaluaciones...
        </div>
      )}

      {error && (
        <div style={{
          background: '#fee2e2',
          color: '#b91c1c',
          padding: '12px 16px',
          borderRadius: '8px',
          marginBottom: '16px',
        }}>
          {error}
          <button
            onClick={loadMyEvaluations}
            style={{
              marginLeft: '12px',
              textDecoration: 'underline',
              background: 'none',
              border: 'none',
              color: '#b91c1c',
              cursor: 'pointer',
            }}
          >
            Reintentar
          </button>
        </div>
      )}

      {!loading && !error && evaluations.length === 0 && (
        <div style={{
          textAlign: 'center',
          padding: '48px',
          color: '#6b7280',
          background: '#f9fafb',
          borderRadius: '8px',
          border: '1px dashed #d1d5db',
        }}>
          <p style={{ margin: 0, fontSize: '1rem' }}>No has realizado evaluaciones todavia</p>
          <p style={{ margin: '8px 0 0', fontSize: '0.875rem' }}>
            Ve a <strong>Evaluaciones</strong> para realizar una nueva evaluacion.
          </p>
        </div>
      )}

      {!loading && !error && evaluations.length > 0 && (
        <div>
          {evaluations.map((evaluation) => {
            const pendingFollowups =
              evaluation.followups?.filter((f) => f.status === 'corrected').length || 0;
            const score = evaluation.overall_score ?? 0;

            return (
              <div
                key={evaluation.id}
                onClick={() => navigate(`/admin/evaluations/${evaluation.id}`)}
                style={{
                  border: '1px solid #e5e7eb',
                  padding: '16px 20px',
                  marginBottom: '12px',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  background: '#ffffff',
                  transition: 'box-shadow 0.15s',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.08)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.boxShadow = 'none';
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '16px' }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '6px' }}>
                      <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 600, color: '#111827' }}>
                        Evaluacion #{evaluation.id}
                      </h3>
                      <span style={{
                        background: getScoreBg(score),
                        color: getScoreColor(score),
                        padding: '2px 10px',
                        borderRadius: '12px',
                        fontSize: '0.8rem',
                        fontWeight: 600,
                      }}>
                        {score.toFixed(1)}%
                      </span>
                    </div>
                    <p style={{ margin: '0 0 2px', fontSize: '0.875rem', color: '#374151' }}>
                      <strong>Institucion:</strong> {evaluation.institution_name || evaluation.website_url}
                    </p>
                    {evaluation.created_at && (
                      <p style={{ margin: 0, fontSize: '0.8rem', color: '#9ca3af' }}>
                        {new Date(evaluation.created_at).toLocaleDateString('es-BO', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric',
                        })}
                      </p>
                    )}
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '8px' }}>
                    {pendingFollowups > 0 && (
                      <div style={{
                        background: '#fef3c7',
                        color: '#92400e',
                        padding: '6px 14px',
                        borderRadius: '20px',
                        fontWeight: 600,
                        fontSize: '0.8rem',
                        whiteSpace: 'nowrap',
                      }}>
                        {pendingFollowups} correccion{pendingFollowups > 1 ? 'es' : ''} pendiente{pendingFollowups > 1 ? 's' : ''}
                      </div>
                    )}
                    {evaluation.followups?.length > 0 && (
                      <span style={{ fontSize: '0.75rem', color: '#9ca3af' }}>
                        {evaluation.followups.length} seguimiento{evaluation.followups.length > 1 ? 's' : ''}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default MyEvaluations;
