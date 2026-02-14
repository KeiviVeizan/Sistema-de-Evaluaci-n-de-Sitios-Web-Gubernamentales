import { useState, useEffect, useCallback } from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, BarChart, Bar, Cell
} from 'recharts';
import { Calendar, TrendingUp, Globe, FileText, AlertCircle, ChevronLeft, ChevronRight } from 'lucide-react';
import styles from './AdminDashboard.module.css';
import api from '../../services/api';

// Nombres de meses en español
const MONTHS = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
];

// Tooltip personalizado para el gráfico de área
function CustomTooltip({ active, payload, label }) {
  if (active && payload && payload.length) {
    return (
      <div className={styles.customTooltip}>
        <p className={styles.tooltipLabel}>{label}</p>
        <p className={styles.tooltipValue}>
          {payload[0].value} evaluación{payload[0].value !== 1 ? 'es' : ''}
        </p>
      </div>
    );
  }
  return null;
}

// Tarjeta de métrica individual
function MetricCard({ icon: Icon, label, value, color, suffix = '' }) {
  return (
    <div className={styles.metricCard}>
      <div className={styles.metricIcon} style={{ background: color }}>
        <Icon size={24} />
      </div>
      <div className={styles.metricContent}>
        <span className={styles.metricLabel}>{label}</span>
        <span className={styles.metricValue}>
          {value !== null && value !== undefined ? `${value}${suffix}` : '—'}
        </span>
      </div>
    </div>
  );
}

export default function AdminDashboard() {
  const today = new Date().toISOString().split('T')[0];

  const [selectedDate, setSelectedDate] = useState(today);
  const [currentYear, setCurrentYear] = useState(new Date().getFullYear());
  const [currentMonth, setCurrentMonth] = useState(new Date().getMonth() + 1);
  const [calendarDays, setCalendarDays] = useState([]);
  const [dailyEvaluations, setDailyEvaluations] = useState(null);
  const [hourlyActivity, setHourlyActivity] = useState([]);
  const [overview, setOverview] = useState(null);
  const [loadingDaily, setLoadingDaily] = useState(false);
  const [loadingCalendar, setLoadingCalendar] = useState(false);
  const [error, setError] = useState(null);

  const loadCalendar = useCallback(async (year, month) => {
    setLoadingCalendar(true);
    try {
      const response = await api.get(`/stats/monthly-calendar?year=${year}&month=${month}`);
      const daysInMonth = new Date(year, month, 0).getDate();
      const days = [];

      for (let i = 1; i <= daysInMonth; i++) {
        const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(i).padStart(2, '0')}`;
        const dayDate = new Date(`${dateStr}T12:00:00`); // Evitar problema de zona horaria
        days.push({
          day: i,
          date: dateStr,
          count: response.data.days[dateStr] || 0,
          dayName: dayDate.toLocaleDateString('es-ES', { weekday: 'short' }),
          isToday: dateStr === today,
          isFuture: dateStr > today,
        });
      }

      setCalendarDays(days);
    } catch (err) {
      console.error('Error cargando calendario:', err);
    } finally {
      setLoadingCalendar(false);
    }
  }, [today]);

  const loadDailyData = useCallback(async (date) => {
    setLoadingDaily(true);
    setError(null);
    try {
      const [evalResponse, hourlyResponse] = await Promise.all([
        api.get(`/stats/daily-evaluations?date=${date}`),
        api.get(`/stats/hourly-activity?date=${date}`)
      ]);

      setDailyEvaluations(evalResponse.data);

      // Solo mostrar horas con actividad ± contexto (7am - 10pm mínimo)
      const hourlyRaw = hourlyResponse.data.hourly_activity;
      const filtered = hourlyRaw.filter(h => h.hour >= 7 && h.hour <= 22);
      setHourlyActivity(filtered.map(h => ({
        hour: `${String(h.hour).padStart(2, '0')}:00`,
        evaluaciones: h.count
      })));
    } catch (err) {
      console.error('Error cargando datos diarios:', err);
      setError('No se pudieron cargar los datos del día seleccionado.');
    } finally {
      setLoadingDaily(false);
    }
  }, []);

  const loadOverview = useCallback(async () => {
    try {
      const response = await api.get('/stats/overview');
      setOverview(response.data);
    } catch (err) {
      console.error('Error cargando overview:', err);
    }
  }, []);

  useEffect(() => {
    loadOverview();
  }, [loadOverview]);

  useEffect(() => {
    loadCalendar(currentYear, currentMonth);
  }, [currentYear, currentMonth, loadCalendar]);

  useEffect(() => {
    if (selectedDate) {
      loadDailyData(selectedDate);
    }
  }, [selectedDate, loadDailyData]);

  const goToPrevMonth = () => {
    if (currentMonth === 1) {
      setCurrentMonth(12);
      setCurrentYear(y => y - 1);
    } else {
      setCurrentMonth(m => m - 1);
    }
  };

  const goToNextMonth = () => {
    const now = new Date();
    if (currentYear > now.getFullYear() || (currentYear === now.getFullYear() && currentMonth >= now.getMonth() + 1)) {
      return; // No navegar al futuro
    }
    if (currentMonth === 12) {
      setCurrentMonth(1);
      setCurrentYear(y => y + 1);
    } else {
      setCurrentMonth(m => m + 1);
    }
  };

  const formatSelectedDate = (dateStr) => {
    const d = new Date(`${dateStr}T12:00:00`);
    return d.toLocaleDateString('es-ES', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
  };

  const hasNextMonth = () => {
    const now = new Date();
    return !(currentYear === now.getFullYear() && currentMonth >= now.getMonth() + 1);
  };

  return (
    <div className={styles.dashboard}>
      {/* Encabezado */}
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Dashboard Administrativo</h1>
          <p className={styles.subtitle}>Monitoreo de evaluaciones y actividad del sistema</p>
        </div>
      </div>

      {/* Métricas rápidas */}
      {overview && (
        <div className={styles.metricsGrid}>
          <MetricCard
            icon={FileText}
            label="Evaluaciones Totales"
            value={overview.total_evaluations}
            color="#800000"
          />
          <MetricCard
            icon={Calendar}
            label="Este Mes"
            value={overview.evaluations_this_month}
            color="#f59e0b"
          />
          <MetricCard
            icon={TrendingUp}
            label="Promedio Cumplimiento"
            value={overview.average_score}
            color="#10b981"
            suffix="%"
          />
          <MetricCard
            icon={Globe}
            label="Sitios Web"
            value={overview.total_websites}
            color="#6366f1"
          />
          <MetricCard
            icon={AlertCircle}
            label="Seguimientos Pendientes"
            value={overview.pending_followups}
            color="#ef4444"
          />
        </div>
      )}

      {/* Selector de días del mes */}
      <div className={styles.calendarSection}>
        <div className={styles.calendarHeader}>
          <h2 className={styles.sectionTitle}>Estadísticas por Día</h2>
          <div className={styles.monthNav}>
            <button className={styles.navBtn} onClick={goToPrevMonth} title="Mes anterior">
              <ChevronLeft size={18} />
            </button>
            <span className={styles.monthLabel}>
              {MONTHS[currentMonth - 1]} {currentYear}
            </span>
            <button
              className={`${styles.navBtn} ${!hasNextMonth() ? styles.navBtnDisabled : ''}`}
              onClick={goToNextMonth}
              title="Mes siguiente"
              disabled={!hasNextMonth()}
            >
              <ChevronRight size={18} />
            </button>
          </div>
        </div>

        {loadingCalendar ? (
          <div className={styles.loadingRow}>
            <div className={styles.spinner} />
            <span>Cargando calendario...</span>
          </div>
        ) : (
          <div className={styles.daysScroll}>
            {calendarDays.map(day => (
              <button
                key={day.date}
                className={[
                  styles.dayButton,
                  selectedDate === day.date ? styles.active : '',
                  day.isToday ? styles.todayBtn : '',
                  day.isFuture ? styles.futureBtn : '',
                ].join(' ')}
                onClick={() => !day.isFuture && setSelectedDate(day.date)}
                disabled={day.isFuture}
                title={day.isFuture ? 'Día futuro' : `${day.count} evaluación(es)`}
              >
                <span className={styles.dayName}>{day.dayName}</span>
                <span className={styles.dayNumber}>{day.day}</span>
                {day.count > 0 && (
                  <span className={styles.dayBadge}>{day.count}</span>
                )}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Gráfico de actividad por hora */}
      <div className={styles.chartCard}>
        <h3 className={styles.chartTitle}>
          Actividad del{' '}
          <span className={styles.chartDateHighlight}>
            {formatSelectedDate(selectedDate)}
          </span>
        </h3>

        {loadingDaily ? (
          <div className={styles.chartLoading}>
            <div className={styles.spinner} />
            <span>Cargando actividad...</span>
          </div>
        ) : hourlyActivity.some(h => h.evaluaciones > 0) ? (
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={hourlyActivity} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="gradEval" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#800000" stopOpacity={0.7} />
                  <stop offset="95%" stopColor="#800000" stopOpacity={0.05} />
                </linearGradient>
                <linearGradient id="gradAmber" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0e6e6" vertical={false} />
              <XAxis
                dataKey="hour"
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
              <Tooltip content={<CustomTooltip />} />
              <Area
                type="monotone"
                dataKey="evaluaciones"
                stroke="#800000"
                strokeWidth={2.5}
                fillOpacity={1}
                fill="url(#gradEval)"
                dot={{ fill: '#800000', r: 4, strokeWidth: 0 }}
                activeDot={{ r: 6, fill: '#800000', stroke: '#fff', strokeWidth: 2 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className={styles.chartEmpty}>
            <FileText size={40} strokeWidth={1} />
            <p>Sin actividad registrada en este día</p>
          </div>
        )}
      </div>

      {/* Evaluaciones del día */}
      <div className={styles.evaluationsSection}>
        <div className={styles.evalHeader}>
          <h3 className={styles.sectionTitle}>
            Evaluaciones Realizadas
            {dailyEvaluations && (
              <span className={styles.evalCount}>{dailyEvaluations.total_evaluations}</span>
            )}
          </h3>
        </div>

        {error && (
          <div className={styles.errorState}>
            <AlertCircle size={20} />
            <span>{error}</span>
          </div>
        )}

        {loadingDaily ? (
          <div className={styles.loadingRow}>
            <div className={styles.spinner} />
            <span>Cargando evaluaciones...</span>
          </div>
        ) : dailyEvaluations && dailyEvaluations.total_evaluations > 0 ? (
          <div className={styles.evaluatorsList}>
            {dailyEvaluations.evaluations_by_evaluator.map((evaluator, idx) => (
              <div key={idx} className={styles.evaluatorCard}>
                <div className={styles.evaluatorHeader}>
                  <div className={styles.evaluatorAvatar}>
                    {evaluator.evaluator_name.charAt(0).toUpperCase()}
                  </div>
                  <div className={styles.evaluatorInfo}>
                    <h4 className={styles.evaluatorName}>{evaluator.evaluator_name}</h4>
                    {evaluator.evaluator_email && (
                      <p className={styles.evaluatorEmail}>{evaluator.evaluator_email}</p>
                    )}
                    <span className={styles.evalCountBadge}>
                      {evaluator.evaluations.length} evaluación{evaluator.evaluations.length !== 1 ? 'es' : ''}
                    </span>
                  </div>
                </div>

                <div className={styles.institutionsList}>
                  {evaluator.evaluations.map(ev => (
                    <div key={ev.id} className={styles.institutionItem}>
                      <div className={styles.instInfo}>
                        <span className={styles.instName}>{ev.institution_name}</span>
                        <span className={styles.instDomain}>{ev.domain}</span>
                      </div>
                      <div className={styles.instScore}>
                        {ev.score !== null && ev.score !== undefined ? (
                          <span
                            className={styles.score}
                            style={{
                              color: ev.score >= 70 ? '#10b981' : ev.score >= 40 ? '#f59e0b' : '#ef4444'
                            }}
                          >
                            {ev.score}%
                          </span>
                        ) : (
                          <span className={styles.scoreNA}>N/A</span>
                        )}
                        <span
                          className={styles.statusBadge}
                          data-status={ev.status}
                        >
                          {ev.status === 'completed' ? 'Completada' :
                           ev.status === 'in_progress' ? 'En progreso' :
                           ev.status === 'pending' ? 'Pendiente' : 'Fallida'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Mini barra de progreso del evaluador */}
                <div className={styles.evaluatorProgress}>
                  {evaluator.evaluations.map((ev, i) => (
                    <div
                      key={i}
                      className={styles.progressDot}
                      style={{
                        background: ev.score !== null
                          ? (ev.score >= 70 ? '#10b981' : ev.score >= 40 ? '#f59e0b' : '#ef4444')
                          : '#d1d5db'
                      }}
                      title={`${ev.institution_name}: ${ev.score !== null ? ev.score + '%' : 'N/A'}`}
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : !error && (
          <div className={styles.emptyState}>
            <Calendar size={48} strokeWidth={1} />
            <p>No hay evaluaciones registradas el {formatSelectedDate(selectedDate)}</p>
            <span>Selecciona otro día del calendario para ver su actividad</span>
          </div>
        )}
      </div>
    </div>
  );
}
