import { useState, useEffect, useCallback } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend, Cell,
  PieChart, Pie,
} from 'recharts';
import {
  Users, Building2, UserPlus, CheckCircle2,
  AlertCircle, Clock,
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import api from '../../services/api';
import styles from './SecretaryDashboard.module.css';

// Colores de la paleta
const COLORS = {
  wine: '#800000',
  wineLight: '#a33030',
  amber: '#f59e0b',
  emerald: '#10b981',
  indigo: '#6366f1',
  blue: '#3b82f6',
  purple: '#8b5cf6',
};

// Colores para el donut
const DONUT_COLORS = [COLORS.wine, COLORS.indigo];

// Gradientes para barras
const BAR_COLORS = [COLORS.wine, COLORS.indigo];

// Colores para barras de progreso de instituciones
const PROGRESS_COLORS = [
  COLORS.wine, COLORS.amber, COLORS.emerald,
  COLORS.indigo, COLORS.blue, COLORS.purple,
];

function MetricCard({ icon: Icon, label, value, color }) {
  return (
    <div className={styles.metricCard}>
      <div className={styles.metricIcon} style={{ background: color }}>
        <Icon size={24} />
      </div>
      <div className={styles.metricContent}>
        <span className={styles.metricLabel}>{label}</span>
        <span className={styles.metricValue}>
          {value !== null && value !== undefined ? value : '—'}
        </span>
      </div>
    </div>
  );
}

function ChartTooltip({ active, payload, label }) {
  if (active && payload && payload.length) {
    return (
      <div className={styles.customTooltip}>
        <p className={styles.tooltipLabel}>{label}</p>
        {payload.map((entry, idx) => (
          <div key={idx} className={styles.tooltipRow}>
            <span className={styles.tooltipDot} style={{ background: entry.color }} />
            <p className={styles.tooltipText}>
              {entry.name}: {entry.value}
            </p>
          </div>
        ))}
      </div>
    );
  }
  return null;
}

function formatDate(isoStr) {
  const d = new Date(isoStr);
  return d.toLocaleDateString('es-BO', { day: '2-digit', month: 'short' });
}

export default function SecretaryDashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [recentUsers, setRecentUsers] = useState([]);
  const [topInstitutions, setTopInstitutions] = useState([]);
  const [monthlyData, setMonthlyData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [statsRes, usersRes, instRes, monthlyRes] = await Promise.all([
        api.get('/secretary/dashboard/stats'),
        api.get('/secretary/dashboard/recent-users?limit=6'),
        api.get('/secretary/dashboard/top-institutions?limit=6'),
        api.get('/secretary/dashboard/monthly-registrations?months=6'),
      ]);
      setStats(statsRes.data);
      setRecentUsers(usersRes.data.users);
      setTopInstitutions(instRes.data.institutions);
      setMonthlyData(monthlyRes.data.monthly_data);
    } catch (err) {
      console.error('Error cargando dashboard secretaría:', err);
      setError('No se pudieron cargar los datos del panel.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  if (loading) {
    return (
      <div className={styles.dashboard}>
        <div className={styles.loadingState}>
          <div className={styles.spinner} />
          <span>Cargando panel...</span>
        </div>
      </div>
    );
  }

  // Datos para el donut
  const donutData = stats ? [
    { name: 'Evaluadores', value: stats.total_evaluators, color: DONUT_COLORS[0] },
    { name: 'Usuarios Entidad', value: stats.total_entity_users, color: DONUT_COLORS[1] },
  ] : [];

  return (
    <div className={styles.dashboard}>
      {/* Encabezado */}
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <h1 className={styles.title}>
            Bienvenido, {user?.full_name || user?.name || 'Secretario'}
          </h1>
          <p className={styles.subtitle}>
            Panel de gestión de usuarios e instituciones
          </p>
        </div>
      </div>

      {error && (
        <div className={styles.errorState}>
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      {/* Métricas rápidas */}
      {stats && (
        <div className={styles.metricsGrid}>
          <MetricCard
            icon={Users}
            label="Usuarios Gestionados"
            value={stats.total_managed_users}
            color={COLORS.wine}
          />
          <MetricCard
            icon={Building2}
            label="Instituciones"
            value={stats.total_institutions}
            color={COLORS.indigo}
          />
          <MetricCard
            icon={UserPlus}
            label="Nuevos este Mes"
            value={stats.new_users_this_month}
            color={COLORS.amber}
          />
          <MetricCard
            icon={CheckCircle2}
            label="Instituciones Activas"
            value={stats.active_institutions}
            color={COLORS.emerald}
          />
        </div>
      )}

      {/* Fila: Distribución + Usuarios recientes */}
      <div className={styles.twoColumns}>
        {/* Distribución de usuarios */}
        <div className={styles.card}>
          <div className={styles.cardHeader}>
            <h3 className={styles.cardTitle}>Distribución de Usuarios</h3>
          </div>
          {stats && stats.total_managed_users > 0 ? (
            <div className={styles.donutSection}>
              <div className={styles.donutWrapper}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={donutData}
                      cx="50%"
                      cy="50%"
                      innerRadius={55}
                      outerRadius={80}
                      paddingAngle={4}
                      dataKey="value"
                      stroke="none"
                    >
                      {donutData.map((entry, index) => (
                        <Cell key={index} fill={entry.color} />
                      ))}
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
                <div className={styles.donutCenter}>
                  <div className={styles.donutTotal}>{stats.total_managed_users}</div>
                  <div className={styles.donutTotalLabel}>Total</div>
                </div>
              </div>
              <div className={styles.donutLegend}>
                {donutData.map((item, idx) => (
                  <div key={idx} className={styles.legendItem}>
                    <span className={styles.legendDot} style={{ background: item.color }} />
                    <div className={styles.legendInfo}>
                      <span className={styles.legendLabel}>{item.name}</span>
                      <span className={styles.legendValue}>{item.value}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className={styles.emptyState}>
              <Users size={36} strokeWidth={1} />
              <p>Sin usuarios registrados</p>
            </div>
          )}
        </div>

        {/* Últimos usuarios registrados */}
        <div className={styles.card}>
          <div className={styles.cardHeader}>
            <h3 className={styles.cardTitle}>Usuarios Recientes</h3>
            {recentUsers.length > 0 && (
              <span className={styles.cardBadge}>Últimos {recentUsers.length}</span>
            )}
          </div>
          {recentUsers.length > 0 ? (
            <div className={styles.userList}>
              {recentUsers.map((u) => (
                <div key={u.id} className={styles.userItem}>
                  <div
                    className={styles.userAvatar}
                    style={{
                      background: u.role === 'evaluator'
                        ? `linear-gradient(135deg, ${COLORS.wine} 0%, ${COLORS.wineLight} 100%)`
                        : `linear-gradient(135deg, ${COLORS.indigo} 0%, ${COLORS.blue} 100%)`,
                    }}
                  >
                    {(u.full_name || 'U').charAt(0).toUpperCase()}
                  </div>
                  <div className={styles.userInfo}>
                    <span className={styles.userName}>{u.full_name}</span>
                    <span className={styles.userEmail}>
                      {u.institution_name || u.email}
                    </span>
                  </div>
                  <div className={styles.userMeta}>
                    <span className={styles.roleBadge} data-role={u.role}>
                      {u.role === 'evaluator' ? 'Evaluador' : 'Entidad'}
                    </span>
                    <span className={styles.userDate}>
                      <Clock size={10} style={{ marginRight: 3, verticalAlign: 'middle' }} />
                      {formatDate(u.created_at)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className={styles.emptyState}>
              <UserPlus size={36} strokeWidth={1} />
              <p>Sin usuarios recientes</p>
            </div>
          )}
        </div>
      </div>

      {/* Fila: Tendencia de registros + Instituciones top */}
      <div className={styles.twoColumns}>
        {/* Gráfico de registros mensuales */}
        <div className={styles.card}>
          <div className={styles.cardHeader}>
            <h3 className={styles.cardTitle}>Registros Mensuales</h3>
            <span className={styles.cardBadge}>Últimos 6 meses</span>
          </div>
          {monthlyData.some(m => m.total > 0) ? (
            <div className={styles.chartWrapper}>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart
                  data={monthlyData}
                  margin={{ top: 10, right: 10, left: -10, bottom: 0 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0e6e6" vertical={false} />
                  <XAxis
                    dataKey="month"
                    stroke="#9ca3af"
                    tick={{ fontSize: 12 }}
                    tickLine={false}
                    axisLine={{ stroke: '#e5e7eb' }}
                  />
                  <YAxis
                    stroke="#9ca3af"
                    tick={{ fontSize: 12 }}
                    tickLine={false}
                    axisLine={false}
                    allowDecimals={false}
                  />
                  <Tooltip content={<ChartTooltip />} />
                  <Legend
                    iconType="circle"
                    iconSize={8}
                    wrapperStyle={{ fontSize: '0.75rem', paddingTop: '0.5rem' }}
                  />
                  <Bar
                    dataKey="evaluators"
                    name="Evaluadores"
                    fill={BAR_COLORS[0]}
                    radius={[4, 4, 0, 0]}
                    barSize={20}
                  />
                  <Bar
                    dataKey="entity_users"
                    name="Usuarios Entidad"
                    fill={BAR_COLORS[1]}
                    radius={[4, 4, 0, 0]}
                    barSize={20}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className={styles.emptyState}>
              <UserPlus size={36} strokeWidth={1} />
              <p>Sin registros en los últimos meses</p>
            </div>
          )}
        </div>

        {/* Instituciones más evaluadas */}
        <div className={styles.card}>
          <div className={styles.cardHeader}>
            <h3 className={styles.cardTitle}>Instituciones Más Evaluadas</h3>
          </div>
          {topInstitutions.length > 0 && topInstitutions.some(i => i.evaluation_count > 0) ? (
            <div className={styles.institutionList}>
              {topInstitutions
                .filter(i => i.evaluation_count > 0)
                .map((inst, idx) => (
                <div key={inst.id} className={styles.institutionItem}>
                  <div className={styles.institutionHeader}>
                    <span className={styles.institutionName}>{inst.name}</span>
                    <span className={styles.institutionCount}>
                      {inst.evaluation_count} eval{inst.evaluation_count !== 1 ? 's' : '.'}
                    </span>
                  </div>
                  <div className={styles.progressBar}>
                    <div
                      className={styles.progressFill}
                      style={{
                        width: `${inst.percentage}%`,
                        background: PROGRESS_COLORS[idx % PROGRESS_COLORS.length],
                      }}
                    />
                  </div>
                  <span className={styles.institutionDomain}>{inst.domain}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className={styles.emptyState}>
              <Building2 size={36} strokeWidth={1} />
              <p>Sin evaluaciones registradas</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
