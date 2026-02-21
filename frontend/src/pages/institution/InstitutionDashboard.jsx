import { useState, useEffect } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer
} from 'recharts';
import {
  FileText, AlertCircle, TrendingUp,
  TrendingDown, Clock, CheckCircle
} from 'lucide-react';
import styles from './InstitutionDashboard.module.css';
import api from '../../services/api';

function InstitutionDashboard() {
  const [stats, setStats] = useState(null);
  const [scoreEvolution, setScoreEvolution] = useState([]);
  const [pendingFollowups, setPendingFollowups] = useState([]);
  const [evaluationHistory, setEvaluationHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const [statsRes, evolutionRes, followupsRes, historyRes] = await Promise.all([
        api.get('/entity/dashboard/stats'),
        api.get('/entity/dashboard/score-evolution'),
        api.get('/entity/dashboard/pending-followups'),
        api.get('/entity/dashboard/evaluation-history')
      ]);

      setStats(statsRes.data);
      setScoreEvolution(evolutionRes.data);
      setPendingFollowups(followupsRes.data);
      setEvaluationHistory(historyRes.data);
    } catch (error) {
      console.error('Error loading dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return '#10b981';
    if (score >= 60) return '#f59e0b';
    return '#ef4444';
  };

  if (loading) {
    return <div className={styles.loading}>Cargando panel...</div>;
  }

  return (
    <div className={styles.dashboard}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.headerInfo}>
          <h1>{stats?.institution_name || 'Mi Institución'}</h1>
          <p>Panel de seguimiento de evaluaciones</p>
        </div>
        <div className={styles.lastScore}>
          <div
            className={styles.scoreCircle}
            style={{ borderColor: getScoreColor(stats?.last_score || 0) }}
          >
            <span className={styles.scoreValue} style={{ color: getScoreColor(stats?.last_score || 0) }}>
              {stats?.last_score || 0}%
            </span>
            <span className={styles.scoreLabel}>Último Score</span>
          </div>
        </div>
      </div>

      {/* Métricas principales */}
      <div className={styles.metricsGrid}>
        <div className={styles.metricCard}>
          <div className={styles.metricIcon} style={{ background: '#800000' }}>
            <FileText color="white" size={24} />
          </div>
          <div className={styles.metricContent}>
            <h3>{stats?.total_evaluations || 0}</h3>
            <p>Evaluaciones Recibidas</p>
          </div>
        </div>

        <div className={styles.metricCard}>
          <div className={styles.metricIcon} style={{ background: '#ef4444' }}>
            <AlertCircle color="white" size={24} />
          </div>
          <div className={styles.metricContent}>
            <h3>{stats?.pending_followups || 0}</h3>
            <p>Seguimientos Pendientes</p>
          </div>
        </div>

        <div className={styles.metricCard}>
          <div className={styles.metricIcon} style={{ background: stats?.improvement >= 0 ? '#10b981' : '#ef4444' }}>
            {stats?.improvement >= 0 ?
              <TrendingUp color="white" size={24} /> :
              <TrendingDown color="white" size={24} />
            }
          </div>
          <div className={styles.metricContent}>
            <h3 style={{ color: stats?.improvement >= 0 ? '#10b981' : '#ef4444' }}>
              {stats?.improvement >= 0 ? '+' : ''}{stats?.improvement || 0}%
            </h3>
            <p>Progreso de Mejora</p>
          </div>
        </div>
      </div>

      <div className={styles.contentGrid}>
        {/* Gráfico de evolución */}
        <div className={styles.chartCard}>
          <h3>Evolución de Cumplimiento</h3>
          {scoreEvolution.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={scoreEvolution}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="date" stroke="#6b7280" tick={{ fontSize: 12 }} />
                <YAxis stroke="#6b7280" domain={[0, 100]} tick={{ fontSize: 12 }} />
                <Tooltip
                  contentStyle={{
                    background: 'white',
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px'
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="score"
                  stroke="#800000"
                  strokeWidth={3}
                  dot={{ fill: '#800000', r: 6 }}
                  activeDot={{ r: 8, fill: '#f59e0b' }}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className={styles.emptyChart}>
              <p>Aún no hay evaluaciones registradas</p>
            </div>
          )}
        </div>

        {/* Seguimientos pendientes */}
        <div className={styles.followupsCard}>
          <div className={styles.followupsHeader}>
            <h3>Observaciones Pendientes</h3>
            <span className={styles.followupsBadge}>{pendingFollowups.length}</span>
          </div>

          {pendingFollowups.length > 0 ? (
            <div className={styles.followupsList}>
              {pendingFollowups.map(f => (
                <div key={f.id} className={styles.followupItem}>
                  <div className={styles.followupIcon}>
                    <Clock size={16} color="#f59e0b" />
                  </div>
                  <div className={styles.followupInfo}>
                    <h4>{f.criterion || 'Observación'}</h4>
                    <p>{f.description}</p>
                    <span className={styles.followupDate}>
                      {new Date(f.created_at).toLocaleDateString('es-ES')}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className={styles.emptyFollowups}>
              <CheckCircle size={40} color="#10b981" />
              <p>¡No tienes observaciones pendientes!</p>
            </div>
          )}
        </div>
      </div>

      {/* Historial de evaluaciones */}
      <div className={styles.historyCard}>
        <h3>Historial de Evaluaciones</h3>
        {evaluationHistory.length > 0 ? (
          <div className={styles.historyList}>
            {evaluationHistory.map((ev, idx) => (
              <div key={ev.id} className={styles.historyItem}>
                <div className={styles.historyNumber}>{evaluationHistory.length - idx}</div>
                <div className={styles.historyInfo}>
                  <h4>Evaluación #{evaluationHistory.length - idx}</h4>
                  <p>
                    Evaluado por <strong>{ev.evaluator_name}</strong> el{' '}
                    {new Date(ev.evaluated_at).toLocaleDateString('es-ES', {
                      day: 'numeric',
                      month: 'long',
                      year: 'numeric'
                    })}
                  </p>
                </div>
                <div
                  className={styles.historyScore}
                  style={{
                    background: `${getScoreColor(ev.score)}15`,
                    color: getScoreColor(ev.score)
                  }}
                >
                  {ev.score}%
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className={styles.emptyState}>
            <p>No hay evaluaciones registradas aún</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default InstitutionDashboard;
