import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import evaluationService from '../../services/evaluationService';

function AdminFollowups() {
  const navigate = useNavigate();
  const [evaluations, setEvaluations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [groupBy, setGroupBy] = useState('evaluator'); // 'evaluator' o 'all'

  useEffect(() => {
    loadAllFollowups();
  }, []);

  const loadAllFollowups = async () => {
    try {
      setError(null);
      const data = await evaluationService.getAllFollowups();
      setEvaluations(data);
    } catch (err) {
      console.error('Error cargando seguimientos:', err);
      setError('No se pudieron cargar los seguimientos. Intente de nuevo.');
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

  const getStatusColor = (status) => {
    const colors = {
      pending: { bg: '#fef3c7', color: '#92400e' },
      corrected: { bg: '#dbeafe', color: '#1e40af' },
      validated: { bg: '#dcfce7', color: '#15803d' },
      rejected: { bg: '#fee2e2', color: '#b91c1c' },
      cancelled: { bg: '#f3f4f6', color: '#6b7280' },
    };
    return colors[status] || colors.pending;
  };

  const getStatusLabel = (status) => {
    const labels = {
      pending: 'Pendiente',
      corrected: 'Corregido',
      validated: 'Validado',
      rejected: 'Rechazado',
      cancelled: 'Cancelado',
    };
    return labels[status] || status;
  };

  // Agrupar evaluaciones por evaluador
  const evaluationsByEvaluator = evaluations.reduce((acc, evaluation) => {
    const evaluatorKey = evaluation.evaluator_id || 'sin_asignar';
    const evaluatorName = evaluation.evaluator_name || 'Sin asignar';

    if (!acc[evaluatorKey]) {
      acc[evaluatorKey] = {
        evaluatorId: evaluation.evaluator_id,
        evaluatorName: evaluatorName,
        evaluatorEmail: evaluation.evaluator_email,
        evaluations: [],
      };
    }

    acc[evaluatorKey].evaluations.push(evaluation);
    return acc;
  }, {});

  const evaluatorGroups = Object.values(evaluationsByEvaluator);

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700, margin: 0, color: '#111827' }}>
          Todos los Seguimientos
        </h1>
        <p style={{ color: '#6b7280', marginTop: '4px', marginBottom: 0 }}>
          Vista general de todos los seguimientos por evaluador
        </p>
      </div>

      {/* Toggle para agrupar o no */}
      <div style={{ marginBottom: '20px', display: 'flex', gap: '12px' }}>
        <button
          onClick={() => setGroupBy('evaluator')}
          style={{
            padding: '8px 16px',
            borderRadius: '6px',
            border: groupBy === 'evaluator' ? '2px solid #2563eb' : '1px solid #d1d5db',
            background: groupBy === 'evaluator' ? '#eff6ff' : '#ffffff',
            color: groupBy === 'evaluator' ? '#2563eb' : '#6b7280',
            fontWeight: groupBy === 'evaluator' ? 600 : 400,
            cursor: 'pointer',
            transition: 'all 0.2s',
          }}
        >
          Agrupar por Evaluador
        </button>
        <button
          onClick={() => setGroupBy('all')}
          style={{
            padding: '8px 16px',
            borderRadius: '6px',
            border: groupBy === 'all' ? '2px solid #2563eb' : '1px solid #d1d5db',
            background: groupBy === 'all' ? '#eff6ff' : '#ffffff',
            color: groupBy === 'all' ? '#2563eb' : '#6b7280',
            fontWeight: groupBy === 'all' ? 600 : 400,
            cursor: 'pointer',
            transition: 'all 0.2s',
          }}
        >
          Ver Todas
        </button>
      </div>

      {loading && (
        <div style={{ textAlign: 'center', padding: '48px', color: '#6b7280' }}>
          Cargando seguimientos...
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
            onClick={loadAllFollowups}
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
          <p style={{ margin: 0, fontSize: '1rem' }}>No hay seguimientos registrados</p>
          <p style={{ margin: '8px 0 0', fontSize: '0.875rem' }}>
            Los seguimientos apareceran aqui cuando los evaluadores los creen.
          </p>
        </div>
      )}

      {!loading && !error && evaluations.length > 0 && (
        <div>
          {groupBy === 'evaluator' ? (
            // Vista agrupada por evaluador
            evaluatorGroups.map((group) => (
              <div
                key={group.evaluatorId || 'sin_asignar'}
                style={{
                  marginBottom: '32px',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  overflow: 'hidden',
                  background: '#ffffff',
                }}
              >
                {/* Header del evaluador */}
                <div
                  style={{
                    background: '#f9fafb',
                    padding: '16px 20px',
                    borderBottom: '1px solid #e5e7eb',
                  }}
                >
                  <h2 style={{ margin: 0, fontSize: '1.125rem', fontWeight: 600, color: '#111827' }}>
                    {group.evaluatorName}
                  </h2>
                  {group.evaluatorEmail && (
                    <p style={{ margin: '4px 0 0', fontSize: '0.875rem', color: '#6b7280' }}>
                      {group.evaluatorEmail}
                    </p>
                  )}
                  <p style={{ margin: '4px 0 0', fontSize: '0.875rem', color: '#9ca3af' }}>
                    {group.evaluations.length} evaluacion{group.evaluations.length !== 1 ? 'es' : ''} con seguimientos
                  </p>
                </div>

                {/* Evaluaciones del evaluador */}
                <div>
                  {group.evaluations.map((evaluation) => {
                    const pendingFollowups =
                      evaluation.followups?.filter((f) => f.status === 'corrected').length || 0;
                    const score = evaluation.overall_score ?? 0;

                    return (
                      <div
                        key={evaluation.id}
                        onClick={() => navigate(`/admin/evaluations/${evaluation.id}`)}
                        style={{
                          borderBottom: '1px solid #f3f4f6',
                          padding: '16px 20px',
                          cursor: 'pointer',
                          background: '#ffffff',
                          transition: 'background 0.15s',
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.background = '#f9fafb';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.background = '#ffffff';
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
                              <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                                {evaluation.followups.slice(0, 3).map((followup) => {
                                  const statusStyle = getStatusColor(followup.status);
                                  return (
                                    <span
                                      key={followup.id}
                                      style={{
                                        background: statusStyle.bg,
                                        color: statusStyle.color,
                                        padding: '2px 8px',
                                        borderRadius: '10px',
                                        fontSize: '0.7rem',
                                        fontWeight: 500,
                                      }}
                                    >
                                      {getStatusLabel(followup.status)}
                                    </span>
                                  );
                                })}
                                {evaluation.followups.length > 3 && (
                                  <span style={{ fontSize: '0.7rem', color: '#9ca3af', alignSelf: 'center' }}>
                                    +{evaluation.followups.length - 3} más
                                  </span>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))
          ) : (
            // Vista sin agrupar (todas las evaluaciones)
            evaluations.map((evaluation) => {
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
                      <p style={{ margin: '0 0 2px', fontSize: '0.875rem', color: '#6b7280' }}>
                        <strong>Evaluador:</strong> {evaluation.evaluator_name}
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
                        <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                          {evaluation.followups.slice(0, 3).map((followup) => {
                            const statusStyle = getStatusColor(followup.status);
                            return (
                              <span
                                key={followup.id}
                                style={{
                                  background: statusStyle.bg,
                                  color: statusStyle.color,
                                  padding: '2px 8px',
                                  borderRadius: '10px',
                                  fontSize: '0.7rem',
                                  fontWeight: 500,
                                }}
                              >
                                {getStatusLabel(followup.status)}
                              </span>
                            );
                          })}
                          {evaluation.followups.length > 3 && (
                            <span style={{ fontSize: '0.7rem', color: '#9ca3af', alignSelf: 'center' }}>
                              +{evaluation.followups.length - 3} más
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      )}
    </div>
  );
}

export default AdminFollowups;
