import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import evaluationService from '../../services/evaluationService';
import { useTheme } from '../../contexts/ThemeContext';
import styles from './MyEvaluations.module.css';

function MyEvaluations() {
  const navigate = useNavigate();
  const { dark } = useTheme();
  const [evaluations, setEvaluations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => { loadMyEvaluations(); }, []);

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
    if (dark) {
      if (score >= 80) return '#4ade80';
      if (score >= 60) return '#fcd34d';
      return '#f87171';
    }
    if (score >= 80) return '#15803d';
    if (score >= 60) return '#b45309';
    return '#b91c1c';
  };

  const getScoreBg = (score) => {
    if (dark) {
      if (score >= 80) return 'rgba(22,163,74,0.18)';
      if (score >= 60) return 'rgba(217,119,6,0.18)';
      return 'rgba(220,38,38,0.18)';
    }
    if (score >= 80) return '#dcfce7';
    if (score >= 60) return '#fef3c7';
    return '#fee2e2';
  };

  return (
    <div className={styles.container}>
      <div style={{ marginBottom: '24px' }}>
        <h1 className={styles.pageTitle}>Mis Evaluaciones</h1>
        <p className={styles.pageSubtitle}>Evaluaciones que has realizado y sus seguimientos</p>
      </div>

      {loading && <div className={styles.loadingState}>Cargando evaluaciones...</div>}

      {error && (
        <div className={styles.errorState}>
          {error}
          <button className={styles.retryBtn} onClick={loadMyEvaluations}>Reintentar</button>
        </div>
      )}

      {!loading && !error && evaluations.length === 0 && (
        <div className={styles.emptyState}>
          <p style={{ margin: 0, fontSize: '1rem' }}>No has realizado evaluaciones todavia</p>
          <p className={styles.emptySubtitle}>
            Ve a <strong>Evaluaciones</strong> para realizar una nueva evaluacion.
          </p>
        </div>
      )}

      {!loading && !error && evaluations.length > 0 && (
        <div className={styles.evalList}>
          {evaluations.map((evaluation) => {
            const pendingFollowups =
              evaluation.followups?.filter(f => f.status === 'corrected').length || 0;
            const score = evaluation.overall_score ?? 0;

            return (
              <div
                key={evaluation.id}
                className={styles.evalCard}
                onClick={() => navigate(`/admin/evaluations/${evaluation.id}`)}
              >
                <div className={styles.evalCardInner}>
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
                      <span className={styles.followupCount}>
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
