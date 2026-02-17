import { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer
} from 'recharts';
import {
  FileText, Building2, TrendingUp, AlertCircle,
  Award, TrendingDown, CheckCircle
} from 'lucide-react';
import styles from './EvaluatorDashboard.module.css';
import api from '../../services/api';

function EvaluatorDashboard() {
  const [stats, setStats] = useState(null);
  const [topInstitutions, setTopInstitutions] = useState([]);
  const [improvedInstitutions, setImprovedInstitutions] = useState([]);
  const [monthlyActivity, setMonthlyActivity] = useState([]);
  const [recentEvaluations, setRecentEvaluations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      setError(null);
      const [statsRes, topRes, improvedRes, activityRes, recentRes] = await Promise.allSettled([
        api.get('/evaluator/dashboard/stats'),
        api.get('/evaluator/dashboard/top-institutions'),
        api.get('/evaluator/dashboard/improved-institutions'),
        api.get('/evaluator/dashboard/monthly-activity'),
        api.get('/evaluator/dashboard/recent-evaluations')
      ]);

      const allFailed = [statsRes, topRes, improvedRes, activityRes, recentRes]
        .every(r => r.status === 'rejected');
      if (allFailed) {
        setError('No se pudieron cargar los datos del dashboard.');
        return;
      }

      if (statsRes.status === 'fulfilled') setStats(statsRes.value.data);
      if (topRes.status === 'fulfilled') setTopInstitutions(topRes.value.data);
      if (improvedRes.status === 'fulfilled') setImprovedInstitutions(improvedRes.value.data);
      if (activityRes.status === 'fulfilled') setMonthlyActivity(activityRes.value.data);
      if (recentRes.status === 'fulfilled') setRecentEvaluations(recentRes.value.data);

      const failed = [
        statsRes.status === 'rejected' && 'stats',
        topRes.status === 'rejected' && 'top-institutions',
        improvedRes.status === 'rejected' && 'improved-institutions',
        activityRes.status === 'rejected' && 'monthly-activity',
        recentRes.status === 'rejected' && 'recent-evaluations',
      ].filter(Boolean);
      if (failed.length > 0) {
        console.warn('Algunos endpoints fallaron:', failed);
      }
    } catch (err) {
      console.error('Error loading dashboard:', err);
      setError('No se pudieron cargar los datos del dashboard.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className={styles.loadingWrapper}>
        <div className={styles.loadingSpinner} />
        <p>Cargando dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.errorWrapper}>
        <AlertCircle size={48} color="#800000" />
        <p>{error}</p>
        <button className={styles.retryBtn} onClick={loadDashboard}>
          Reintentar
        </button>
      </div>
    );
  }

  return (
    <div className={styles.dashboard}>
      {/* Encabezado */}
      <div className={styles.header}>
        <div>
          <h1>Mi Dashboard</h1>
          <p>Resumen de tu actividad como evaluador</p>
        </div>
      </div>

      {/* Métricas principales */}
      <div className={styles.metricsGrid}>
        {/* Total evaluaciones */}
        <div className={styles.metricCard}>
          <div className={styles.metricIcon} style={{ background: '#800000' }}>
            <FileText color="white" size={24} />
          </div>
          <div className={styles.metricContent}>
            <h3>{stats.total_evaluations}</h3>
            <p>Total Evaluaciones</p>
            {stats.trend_percentage !== 0 && (
              <div className={`${styles.trend} ${stats.trend_percentage > 0 ? styles.trendUp : styles.trendDown}`}>
                {stats.trend_percentage > 0
                  ? <TrendingUp size={14} />
                  : <TrendingDown size={14} />}
                {Math.abs(stats.trend_percentage)}% vs mes anterior
              </div>
            )}
          </div>
        </div>

        {/* Instituciones evaluadas */}
        <div className={styles.metricCard}>
          <div className={styles.metricIcon} style={{ background: '#f59e0b' }}>
            <Building2 color="white" size={24} />
          </div>
          <div className={styles.metricContent}>
            <h3>{stats.unique_institutions}</h3>
            <p>Instituciones Evaluadas</p>
          </div>
        </div>

        {/* Promedio de cumplimiento */}
        <div className={styles.metricCard}>
          <div className={styles.metricIcon} style={{ background: '#10b981' }}>
            <Award color="white" size={24} />
          </div>
          <div className={styles.metricContent}>
            <h3>{stats.average_score}%</h3>
            <p>Promedio Cumplimiento</p>
          </div>
        </div>

        {/* Seguimientos pendientes */}
        <div className={styles.metricCard}>
          <div className={styles.metricIcon} style={{ background: '#ef4444' }}>
            <AlertCircle color="white" size={24} />
          </div>
          <div className={styles.metricContent}>
            <h3>{stats.pending_followups}</h3>
            <p>Seguimientos Pendientes</p>
          </div>
        </div>
      </div>

      {/* Gráfico + Rankings */}
      <div className={styles.contentGrid}>
        {/* Gráfico de actividad mensual */}
        <div className={styles.chartCard}>
          <h3>Actividad Mensual</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={monthlyActivity} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
              <XAxis dataKey="month" stroke="#6b7280" tick={{ fontSize: 13 }} />
              <YAxis stroke="#6b7280" tick={{ fontSize: 13 }} allowDecimals={false} />
              <Tooltip
                contentStyle={{
                  background: 'white',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  fontSize: '0.875rem'
                }}
                formatter={(value) => [value, 'Evaluaciones']}
              />
              <Bar dataKey="count" fill="#800000" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Rankings */}
        <div className={styles.rankingsCard}>
          {/* Top instituciones */}
          <h3>Top Instituciones</h3>
          <div className={styles.rankingsList}>
            {topInstitutions.length === 0 ? (
              <p className={styles.emptyState}>Sin datos aún</p>
            ) : (
              topInstitutions.map((inst, idx) => (
                <div key={idx} className={styles.rankingItem}>
                  <div className={styles.rankingBadge}>#{idx + 1}</div>
                  <div className={styles.rankingInfo}>
                    <span className={styles.rankingName}>{inst.name}</span>
                    <span className={styles.rankingScore}>{inst.score}%</span>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Instituciones que mejoraron */}
          <h3 className={styles.secondTitle}>Instituciones que Mejoraron</h3>
          <div className={styles.rankingsList}>
            {improvedInstitutions.length === 0 ? (
              <p className={styles.emptyState}>No hay datos de mejora aún</p>
            ) : (
              improvedInstitutions.map((inst, idx) => (
                <div key={idx} className={styles.rankingItem}>
                  <div className={styles.improvementIcon}>
                    <TrendingUp size={16} color="#10b981" />
                  </div>
                  <div className={styles.rankingInfo}>
                    <span className={styles.rankingName}>{inst.name}</span>
                    <span className={styles.improvement}>+{inst.improvement}%</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Evaluaciones recientes */}
      <div className={styles.recentCard}>
        <h3>Evaluaciones Recientes</h3>
        <div className={styles.evaluationsList}>
          {recentEvaluations.length === 0 ? (
            <p className={styles.emptyState}>No hay evaluaciones registradas aún</p>
          ) : (
            recentEvaluations.map(ev => (
              <div key={ev.id} className={styles.evaluationItem}>
                <div className={styles.evaluationIcon}>
                  <CheckCircle size={20} color="#10b981" />
                </div>
                <div className={styles.evaluationInfo}>
                  <h4>{ev.institution_name}</h4>
                  <p>
                    {ev.evaluated_at
                      ? new Date(ev.evaluated_at).toLocaleDateString('es-ES', {
                          day: 'numeric',
                          month: 'long',
                          year: 'numeric'
                        })
                      : 'Fecha desconocida'}
                  </p>
                </div>
                <div className={`${styles.evaluationScore} ${
                  ev.score >= 80 ? styles.scoreGood :
                  ev.score >= 60 ? styles.scoreWarning :
                  styles.scoreBad
                }`}>
                  {ev.score}%
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

export default EvaluatorDashboard;
