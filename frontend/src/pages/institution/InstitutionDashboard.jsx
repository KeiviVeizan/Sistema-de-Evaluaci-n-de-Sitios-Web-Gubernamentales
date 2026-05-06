import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer
} from 'recharts';
import {
  FileText, AlertCircle, TrendingUp,
  TrendingDown, Clock, CheckCircle
} from 'lucide-react';
import styles from './InstitutionDashboard.module.css';
import { useTheme } from '../../contexts/ThemeContext';
import api from '../../services/api';

const parseDate = (dateStr) => {
  let d = new Date(dateStr);
  if (!isNaN(d)) return d;
  const parts = String(dateStr).split('/');
  if (parts.length === 3) {
    d = new Date(`${parts[2]}-${parts[1]}-${parts[0]}`);
    if (!isNaN(d)) return d;
  }
  return null;
};

const toMonthKey = (d) =>
  `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;

const getWeekOfMonth = (d) => {
  const firstDay = new Date(d.getFullYear(), d.getMonth(), 1);
  return Math.ceil((d.getDate() + firstDay.getDay()) / 7);
};

const getAvailableMonths = (data) => {
  const now = new Date();
  const nowKey = toMonthKey(now);
  const map = { [nowKey]: now.toLocaleDateString('es-ES', { month: 'long', year: 'numeric' }) };
  data.forEach((item) => {
    const d = parseDate(item.date);
    if (!d) return;
    const key = toMonthKey(d);
    if (key > nowKey) return;
    if (!map[key]) map[key] = d.toLocaleDateString('es-ES', { month: 'long', year: 'numeric' });
  });
  return Object.entries(map).sort(([a], [b]) => b.localeCompare(a));
};

const getWeeksInMonth = (data, monthKey) => {
  const [year, month] = monthKey.split('-').map(Number);
  const weeks = new Set();
  data.forEach((item) => {
    const d = parseDate(item.date);
    if (!d || d.getFullYear() !== year || d.getMonth() + 1 !== month) return;
    weeks.add(getWeekOfMonth(d));
  });
  return Array.from(weeks).sort((a, b) => a - b);
};

const getChartData = (data, monthKey, week) => {
  const [year, month] = monthKey.split('-').map(Number);
  return data
    .filter((item) => {
      const d = parseDate(item.date);
      if (!d || d.getFullYear() !== year || d.getMonth() + 1 !== month) return false;
      if (week !== 'all' && getWeekOfMonth(d) !== week) return false;
      return true;
    })
    .map((item) => ({
      ...item,
      date: parseDate(item.date).toLocaleDateString('es-ES', { day: '2-digit', month: 'short' }),
    }));
};

function InstitutionDashboard() {
  const [stats, setStats] = useState(null);
  const [scoreEvolution, setScoreEvolution] = useState([]);
  const [pendingFollowups, setPendingFollowups] = useState([]);
  const [evaluationHistory, setEvaluationHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedMonth, setSelectedMonth] = useState(toMonthKey(new Date()));
  const [selectedWeek, setSelectedWeek] = useState(getWeekOfMonth(new Date()));
  const [historyMonth, setHistoryMonth] = useState(toMonthKey(new Date()));
  const [selectedFollowup, setSelectedFollowup] = useState(null);
  const navigate = useNavigate();
  const { dark } = useTheme();

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
    <main className={styles.dashboard}>
      {/* Encabezado de la institución */}
      <header className={styles.header}>
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
      </header>

      {/* Métricas principales */}
      <section className={styles.metricsGrid} aria-label="Resumen de métricas">
        <article className={styles.metricCard}>
          <div className={styles.metricIcon} style={{ background: '#800000' }}>
            <FileText color="white" size={24} />
          </div>
          <div className={styles.metricContent}>
            <h2>{stats?.total_evaluations || 0}</h2>
            <p>Evaluaciones Recibidas</p>
          </div>
        </article>

        <article className={styles.metricCard}>
          <div className={styles.metricIcon} style={{ background: '#ef4444' }}>
            <AlertCircle color="white" size={24} />
          </div>
          <div className={styles.metricContent}>
            <h2>{stats?.pending_followups || 0}</h2>
            <p>Seguimientos Pendientes</p>
          </div>
        </article>

        <article className={styles.metricCard}>
          <div className={styles.metricIcon} style={{ background: stats?.improvement >= 0 ? '#10b981' : '#ef4444' }}>
            {stats?.improvement >= 0 ?
              <TrendingUp color="white" size={24} /> :
              <TrendingDown color="white" size={24} />
            }
          </div>
          <div className={styles.metricContent}>
            <h2 style={{ color: stats?.improvement >= 0 ? '#10b981' : '#ef4444' }}>
              {stats?.improvement >= 0 ? '+' : ''}{stats?.improvement || 0}%
            </h2>
            <p>Progreso de Mejora</p>
          </div>
        </article>
      </section>

      <section className={styles.contentGrid} aria-label="Actividad reciente">
        {/* Gráfico de evolución */}
        <article className={styles.chartCard}>
          <header className={styles.chartHeader}>
            <h2>Evolución de Cumplimiento</h2>
            <div className={styles.chartFilters}>
              <select
                className={styles.monthSelect}
                value={selectedMonth}
                aria-label="Seleccionar mes"
                onChange={(e) => {
                  setSelectedMonth(e.target.value);
                  setSelectedWeek('all');
                }}
              >
                {getAvailableMonths(scoreEvolution).map(([key, label]) => (
                  <option key={key} value={key}>{label}</option>
                ))}
              </select>
              <div className={styles.chartToggle} role="group" aria-label="Filtrar por semana">
                <button
                  className={selectedWeek === 'all' ? styles.toggleActive : styles.toggleBtn}
                  onClick={() => setSelectedWeek('all')}
                >
                  Todo el mes
                </button>
                {getWeeksInMonth(scoreEvolution, selectedMonth).map((w) => (
                  <button
                    key={w}
                    className={selectedWeek === w ? styles.toggleActive : styles.toggleBtn}
                    onClick={() => setSelectedWeek(w)}
                  >
                    Sem. {w}
                  </button>
                ))}
              </div>
            </div>
          </header>
          {(() => {
            const chartData = getChartData(scoreEvolution, selectedMonth, selectedWeek);
            if (chartData.length === 0) {
              return (
                <div className={styles.emptyChart}>
                  <p>No se realizaron evaluaciones en este período</p>
                </div>
              );
            }
            return (
              <ResponsiveContainer width="100%" height={280}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke={dark ? '#1e2030' : '#e5e7eb'} />
                  <XAxis dataKey="date" stroke={dark ? '#3d4455' : '#6b7280'} tick={{ fontSize: 12, fill: dark ? '#7b8496' : '#6b7280' }} />
                  <YAxis stroke={dark ? '#3d4455' : '#6b7280'} domain={[0, 100]} tick={{ fontSize: 12, fill: dark ? '#7b8496' : '#6b7280' }} />
                  <Tooltip
                    contentStyle={{
                      background: dark ? '#1a1b2a' : 'white',
                      border: `1px solid ${dark ? 'rgba(255,255,255,0.08)' : '#e5e7eb'}`,
                      borderRadius: '10px',
                      color: dark ? '#f0f1f8' : '#374151',
                      boxShadow: dark ? '0 8px 32px rgba(0,0,0,0.5)' : '0 4px 16px rgba(0,0,0,0.1)',
                    }}
                    labelStyle={{ color: dark ? '#7b8496' : '#6b7280' }}
                    formatter={(value) => [`${value}%`, 'Score']}
                  />
                  <Line
                    type="monotone"
                    dataKey="score"
                    stroke={dark ? '#c44040' : '#800000'}
                    strokeWidth={3}
                    dot={{ fill: dark ? '#c44040' : '#800000', r: 5 }}
                    activeDot={{ r: 7, fill: '#f59e0b' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            );
          })()}
        </article>

        {/* Observaciones pendientes */}
        <article className={styles.followupsCard}>
          <header className={styles.followupsHeader}>
            <h2>Observaciones Pendientes</h2>
            <span className={styles.followupsBadge} aria-label={`${pendingFollowups.length} observaciones`}>
              {pendingFollowups.length}
            </span>
          </header>

          {pendingFollowups.length > 0 ? (
            <ul className={styles.followupsList}>
              {pendingFollowups.map(f => (
                <li
                  key={f.id}
                  className={styles.followupItem}
                  onClick={() => setSelectedFollowup(f)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => e.key === 'Enter' && setSelectedFollowup(f)}
                >
                  <div className={styles.followupIcon} aria-hidden="true">
                    <Clock size={16} color="#f59e0b" />
                  </div>
                  <div className={styles.followupInfo}>
                    <h3>{f.criterion || 'Observación'}</h3>
                    <p>{f.description}</p>
                    <time className={styles.followupDate} dateTime={f.created_at}>
                      {new Date(f.created_at).toLocaleDateString('es-ES')}
                    </time>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <div className={styles.emptyFollowups}>
              <CheckCircle size={40} color="#10b981" />
              <p>¡No tienes observaciones pendientes!</p>
            </div>
          )}
        </article>
      </section>

      {/* Historial de evaluaciones */}
      <section className={styles.historyCard} aria-label="Historial de evaluaciones">
        <header className={styles.historyHeader}>
          <h2>Historial de Evaluaciones</h2>
          {(() => {
            const now = new Date();
            const nowKey = toMonthKey(now);
            const months = { [nowKey]: now.toLocaleDateString('es-ES', { month: 'long', year: 'numeric' }) };
            evaluationHistory.forEach((ev) => {
              const d = parseDate(ev.evaluated_at);
              if (!d) return;
              const key = toMonthKey(d);
              if (key > nowKey) return;
              if (!months[key]) months[key] = d.toLocaleDateString('es-ES', { month: 'long', year: 'numeric' });
            });
            const options = Object.entries(months).sort(([a], [b]) => b.localeCompare(a));
            return (
              <select
                className={styles.monthSelect}
                value={historyMonth}
                aria-label="Seleccionar mes del historial"
                onChange={(e) => setHistoryMonth(e.target.value)}
              >
                {options.map(([key, label]) => (
                  <option key={key} value={key}>{label}</option>
                ))}
              </select>
            );
          })()}
        </header>
        {(() => {
          const [year, month] = historyMonth.split('-').map(Number);
          const filtered = evaluationHistory.filter((ev) => {
            const d = parseDate(ev.evaluated_at);
            return d && d.getFullYear() === year && d.getMonth() + 1 === month;
          });
          return filtered.length > 0 ? (
            <ol className={styles.historyList}>
              {filtered.map((ev, idx) => (
                <li key={ev.id} className={styles.historyItem}>
                  <div className={styles.historyNumber} aria-hidden="true">{filtered.length - idx}</div>
                  <div className={styles.historyInfo}>
                    <h3>Evaluación #{filtered.length - idx}</h3>
                    <p>
                      Evaluado por <strong>{ev.evaluator_name}</strong> el{' '}
                      <time dateTime={ev.evaluated_at}>
                        {new Date(ev.evaluated_at).toLocaleDateString('es-ES', {
                          day: 'numeric', month: 'long', year: 'numeric'
                        })}
                      </time>
                    </p>
                  </div>
                  <div
                    className={styles.historyScore}
                    style={{ background: `${getScoreColor(ev.score)}15`, color: getScoreColor(ev.score) }}
                  >
                    {ev.score}%
                  </div>
                </li>
              ))}
            </ol>
          ) : (
            <p className={styles.emptyState}>No se realizaron evaluaciones en este mes</p>
          );
        })()}
      </section>

      {/* Modal de observación */}
      {selectedFollowup && (
        <div
          className={styles.modalOverlay}
          role="dialog"
          aria-modal="true"
          aria-label="Detalle de observación"
          onClick={() => setSelectedFollowup(null)}
        >
          <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
            <header className={styles.modalHeader}>
              <div>
                <span className={styles.modalCode}>{selectedFollowup.criterion_code}</span>
                <h2 className={styles.modalTitle}>{selectedFollowup.criterion}</h2>
              </div>
              <button className={styles.modalClose} aria-label="Cerrar" onClick={() => setSelectedFollowup(null)}>✕</button>
            </header>

            <div className={styles.modalBody}>
              <div className={styles.modalField}>
                <span className={styles.modalLabel}>Observación</span>
                <p className={styles.modalText}>{selectedFollowup.description}</p>
              </div>
              <div className={styles.modalMeta}>
                <div className={styles.modalField}>
                  <span className={styles.modalLabel}>Evaluador</span>
                  <p className={styles.modalText}>{selectedFollowup.evaluator_name}</p>
                </div>
                <div className={styles.modalField}>
                  <span className={styles.modalLabel}>Fecha</span>
                  <time className={styles.modalText} dateTime={selectedFollowup.created_at}>
                    {new Date(selectedFollowup.created_at).toLocaleDateString('es-ES', {
                      day: 'numeric', month: 'long', year: 'numeric'
                    })}
                  </time>
                </div>
                {selectedFollowup.due_date && (
                  <div className={styles.modalField}>
                    <span className={styles.modalLabel}>Vencimiento</span>
                    <time className={styles.modalText} dateTime={selectedFollowup.due_date}>
                      {new Date(selectedFollowup.due_date).toLocaleDateString('es-ES', {
                        day: 'numeric', month: 'long', year: 'numeric'
                      })}
                    </time>
                  </div>
                )}
              </div>
            </div>

            <footer className={styles.modalFooter}>
              <button className={styles.modalCancel} onClick={() => setSelectedFollowup(null)}>
                Cerrar
              </button>
              <button
                className={styles.modalAction}
                onClick={() => navigate(`/admin/evaluations/${selectedFollowup.evaluation_id}`)}
              >
                Ver evaluación completa →
              </button>
            </footer>
          </div>
        </div>
      )}
    </main>
  );
}

export default InstitutionDashboard;
