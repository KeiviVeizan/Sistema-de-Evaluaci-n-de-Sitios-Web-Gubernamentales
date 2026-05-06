import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import evaluationService from '../../services/evaluationService';
import styles from './AdminFollowups.module.css';
import { useTheme } from '../../contexts/ThemeContext';

function AdminFollowups() {
  const navigate = useNavigate();
  const { dark } = useTheme();
  const [evaluations, setEvaluations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [groupBy, setGroupBy] = useState('evaluator');

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
    if (dark) {
      if (score >= 80) return '#34d399';
      if (score >= 60) return '#fcd34d';
      return '#f87171';
    }
    if (score >= 80) return '#15803d';
    if (score >= 60) return '#b45309';
    return '#b91c1c';
  };

  const getScoreBg = (score) => {
    if (dark) {
      if (score >= 80) return 'rgba(5,150,105,0.15)';
      if (score >= 60) return 'rgba(146,64,14,0.2)';
      return 'rgba(153,27,27,0.2)';
    }
    if (score >= 80) return '#dcfce7';
    if (score >= 60) return '#fef3c7';
    return '#fee2e2';
  };

  const getStatusColor = (status) => {
    if (dark) {
      const colors = {
        pending:   { bg: 'rgba(146,64,14,0.2)',    color: '#fcd34d' },
        corrected: { bg: 'rgba(30,64,175,0.2)',     color: '#93c5fd' },
        validated: { bg: 'rgba(5,150,105,0.15)',    color: '#34d399' },
        rejected:  { bg: 'rgba(153,27,27,0.2)',     color: '#f87171' },
        cancelled: { bg: 'rgba(255,255,255,0.06)',  color: '#7b8496' },
      };
      return colors[status] || colors.pending;
    }
    const colors = {
      pending:   { bg: '#fef3c7', color: '#92400e' },
      corrected: { bg: '#dbeafe', color: '#1e40af' },
      validated: { bg: '#dcfce7', color: '#15803d' },
      rejected:  { bg: '#fee2e2', color: '#b91c1c' },
      cancelled: { bg: '#f3f4f6', color: '#6b7280' },
    };
    return colors[status] || colors.pending;
  };

  const getStatusLabel = (status) => {
    const labels = {
      pending:   'Pendiente',
      corrected: 'Corregido',
      validated: 'Validado',
      rejected:  'Rechazado',
      cancelled: 'Cancelado',
    };
    return labels[status] || status;
  };

  const evaluationsByEvaluator = evaluations.reduce((acc, evaluation) => {
    const evaluatorKey = evaluation.evaluator_id || 'sin_asignar';
    const evaluatorName = evaluation.evaluator_name || 'Sin asignar';
    if (!acc[evaluatorKey]) {
      acc[evaluatorKey] = {
        evaluatorId: evaluation.evaluator_id,
        evaluatorName,
        evaluatorEmail: evaluation.evaluator_email,
        evaluations: [],
      };
    }
    acc[evaluatorKey].evaluations.push(evaluation);
    return acc;
  }, {});

  const evaluatorGroups = Object.values(evaluationsByEvaluator);

  const renderEvalContent = (evaluation, showEvaluator = false) => {
    const pendingFollowups = evaluation.followups?.filter((f) => f.status === 'corrected').length || 0;
    const score = evaluation.overall_score ?? 0;

    return (
      <div className={styles.evalContent}>
        <div className={styles.evalLeft}>
          <div className={styles.evalTitleRow}>
            <h3 className={styles.evalTitle}>Evaluacion #{evaluation.id}</h3>
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
          <p className={styles.evalInst}>
            <strong>Institucion:</strong> {evaluation.institution_name || evaluation.website_url}
          </p>
          {showEvaluator && (
            <p className={styles.evalEvaluator}>
              <strong>Evaluador:</strong> {evaluation.evaluator_name}
            </p>
          )}
          {evaluation.created_at && (
            <p className={styles.evalDate}>
              {new Date(evaluation.created_at).toLocaleDateString('es-BO', {
                year: 'numeric', month: 'long', day: 'numeric',
              })}
            </p>
          )}
        </div>

        <div className={styles.evalRight}>
          {pendingFollowups > 0 && (
            <div className={styles.pendingBadge}>
              {pendingFollowups} correccion{pendingFollowups > 1 ? 'es' : ''} pendiente{pendingFollowups > 1 ? 's' : ''}
            </div>
          )}
          {evaluation.followups?.length > 0 && (
            <div className={styles.statusList}>
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
                <span className={styles.moreCount}>
                  +{evaluation.followups.length - 3} más
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className={styles.container}>
      <div style={{ marginBottom: '24px' }}>
        <h1 className={styles.pageTitle}>Todos los Seguimientos</h1>
        <p className={styles.pageSubtitle}>Vista general de todos los seguimientos por evaluador</p>
      </div>

      <div className={styles.toggleGroup}>
        <button
          className={groupBy === 'evaluator' ? styles.toggleBtnActive : styles.toggleBtn}
          onClick={() => setGroupBy('evaluator')}
        >
          Agrupar por Evaluador
        </button>
        <button
          className={groupBy === 'all' ? styles.toggleBtnActive : styles.toggleBtn}
          onClick={() => setGroupBy('all')}
        >
          Ver Todas
        </button>
      </div>

      {loading && (
        <div className={styles.loadingState}>Cargando seguimientos...</div>
      )}

      {error && (
        <div className={styles.errorState}>
          {error}
          <button className={styles.retryBtn} onClick={loadAllFollowups}>
            Reintentar
          </button>
        </div>
      )}

      {!loading && !error && evaluations.length === 0 && (
        <div className={styles.emptyState}>
          <p>No hay seguimientos registrados</p>
          <p>Los seguimientos apareceran aqui cuando los evaluadores los creen.</p>
        </div>
      )}

      {!loading && !error && evaluations.length > 0 && (
        <div>
          {groupBy === 'evaluator' ? (
            evaluatorGroups.map((group) => (
              <div key={group.evaluatorId || 'sin_asignar'} className={styles.groupCard}>
                <div className={styles.groupHeader}>
                  <h2 className={styles.groupName}>{group.evaluatorName}</h2>
                  {group.evaluatorEmail && (
                    <p className={styles.groupEmail}>{group.evaluatorEmail}</p>
                  )}
                  <p className={styles.groupCount}>
                    {group.evaluations.length} evaluacion{group.evaluations.length !== 1 ? 'es' : ''} con seguimientos
                  </p>
                </div>
                <div>
                  {group.evaluations.map((evaluation) => (
                    <div
                      key={evaluation.id}
                      className={styles.evalRow}
                      onClick={() => navigate(`/admin/evaluations/${evaluation.id}`)}
                    >
                      {renderEvalContent(evaluation)}
                    </div>
                  ))}
                </div>
              </div>
            ))
          ) : (
            evaluations.map((evaluation) => (
              <div
                key={evaluation.id}
                className={styles.evalCard}
                onClick={() => navigate(`/admin/evaluations/${evaluation.id}`)}
              >
                {renderEvalContent(evaluation, true)}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}

export default AdminFollowups;
