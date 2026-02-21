import { useState, useEffect, useCallback } from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer
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

// Retorna la fecha actual en zona horaria Bolivia (UTC-4) como 'YYYY-MM-DD'
function getBoliviaDate() {
  const now = new Date();
  // Bolivia = UTC-4: restar 4 horas al UTC para obtener la hora local boliviana
  const boliviaTime = new Date(now.getTime() - 4 * 60 * 60 * 1000);
  return boliviaTime.toISOString().split('T')[0];
}

export default function AdminDashboard() {
  const today = getBoliviaDate();

  const [selectedDate, setSelectedDate] = useState(today);
  const [currentYear, setCurrentYear] = useState(() => new Date(today + 'T12:00:00').getFullYear());
  const [currentMonth, setCurrentMonth] = useState(() => new Date(today + 'T12:00:00').getMonth() + 1);
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

      // Calcular rango de horas a mostrar: desde la primera hasta la última con actividad,
      // con margen de ±1 hora. Si no hay actividad, mostrar rango laboral 7-18.
      const hourlyRaw = hourlyResponse.data.hourly_activity;
      const activeHours = hourlyRaw.filter(h => h.count > 0).map(h => h.hour);
      let minHour = 7;
      let maxHour = 18;
      if (activeHours.length > 0) {
        minHour = Math.max(0, Math.min(...activeHours) - 1);
        maxHour = Math.min(23, Math.max(...activeHours) + 1);
      }
      const visibleHours = hourlyRaw.filter(h => h.hour >= minHour && h.hour <= maxHour);
      setHourlyActivity(visibleHours.map(h => ({
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
    const todayBolivia = new Date(getBoliviaDate() + 'T12:00:00');
    const nowYear = todayBolivia.getFullYear();
    const nowMonth = todayBolivia.getMonth() + 1;
    if (currentYear > nowYear || (currentYear === nowYear && currentMonth >= nowMonth)) {
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
    const todayBolivia = new Date(getBoliviaDate() + 'T12:00:00');
    const nowYear = todayBolivia.getFullYear();
    const nowMonth = todayBolivia.getMonth() + 1;
    return !(currentYear === nowYear && currentMonth >= nowMonth);
  };

  return (
    <div className={styles.dashboard}>
      {/* Encabezado */}
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Panel Administrativo</h1>
          <p className={styles.subtitle}>Monitoreo de evaluaciones y actividad del sistema</p>
        </div>
      </div>

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
          <div className={styles.evaluatorRows}>
            {dailyEvaluations.evaluations_by_evaluator.map((evaluator, idx) => (
              <div key={idx} className={styles.evaluatorRow}>
                {/* Columna izquierda: identidad del evaluador */}
                <div className={styles.evaluatorSidebar}>
                  <div className={styles.evaluatorAvatar}>
                    {evaluator.evaluator_name.charAt(0).toUpperCase()}
                  </div>
                  <div className={styles.evaluatorMeta}>
                    <span className={styles.evaluatorName}>{evaluator.evaluator_name}</span>
                    {evaluator.evaluator_email && (
                      <span className={styles.evaluatorEmail}>{evaluator.evaluator_email}</span>
                    )}
                    <span className={styles.evalCountBadge}>
                      {evaluator.evaluations.length} eval{evaluator.evaluations.length !== 1 ? 's' : '.'}
                    </span>
                  </div>
                </div>

                {/* Tarjetas horizontales de evaluaciones */}
                <div className={styles.evalCardsScroll}>
                  {evaluator.evaluations.map(ev => {
                    const scoreColor = ev.score === null ? '#9ca3af'
                      : ev.score >= 70 ? '#10b981'
                      : ev.score >= 40 ? '#f59e0b'
                      : '#ef4444';
                    const scoreGrad = ev.score === null ? 'rgba(156,163,175,0.08)'
                      : ev.score >= 70 ? 'rgba(16,185,129,0.07)'
                      : ev.score >= 40 ? 'rgba(245,158,11,0.07)'
                      : 'rgba(239,68,68,0.07)';
                    return (
                      <div
                        key={ev.id}
                        className={styles.evalCard}
                        style={{ '--score-color': scoreColor, '--score-grad': scoreGrad }}
                      >
                        {/* Franja de color superior */}
                        <div className={styles.evalCardAccent} style={{ background: scoreColor }} />

                        <div className={styles.evalCardBody}>
                          {/* Institución */}
                          <div className={styles.evalCardInst}>
                            <span className={styles.evalCardInstName}>{ev.institution_name}</span>
                            <span className={styles.evalCardDomain}>{ev.domain}</span>
                            {ev.website_url && ev.website_url !== 'N/A' && (
                              <span className={styles.evalCardUrl}>{ev.website_url}</span>
                            )}
                          </div>

                          {/* Score grande */}
                          <div className={styles.evalCardScore} style={{ color: scoreColor }}>
                            {ev.score !== null && ev.score !== undefined
                              ? `${ev.score}%`
                              : 'N/A'}
                          </div>
                        </div>

                        {/* Footer: estado + hora */}
                        <div className={styles.evalCardFooter}>
                          <span className={styles.statusBadge} data-status={ev.status}>
                            {ev.status === 'completed' ? 'Completada'
                             : ev.status === 'in_progress' ? 'En progreso'
                             : ev.status === 'pending' ? 'Pendiente'
                             : 'Fallida'}
                          </span>
                          {ev.hour !== undefined && (
                            <span className={styles.evalCardHour}>
                              {String(ev.hour).padStart(2, '0')}:00
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })}
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
