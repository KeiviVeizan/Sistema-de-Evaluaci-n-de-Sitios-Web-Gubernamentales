import { useAuth, ROLES } from '../../contexts/AuthContext';
import {
  ClipboardCheck,
  Building2,
  Users,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Clock,
} from 'lucide-react';
import styles from './Dashboard.module.css';

// Datos de ejemplo para el dashboard
const stats = {
  [ROLES.SUPERADMIN]: [
    { label: 'Total Evaluaciones', value: '1,234', icon: ClipboardCheck, color: 'primary' },
    { label: 'Instituciones', value: '156', icon: Building2, color: 'blue' },
    { label: 'Usuarios Activos', value: '89', icon: Users, color: 'green' },
    { label: 'Promedio General', value: '72%', icon: TrendingUp, color: 'yellow' },
  ],
  [ROLES.SECRETARY]: [
    { label: 'Evaluaciones Activas', value: '342', icon: ClipboardCheck, color: 'primary' },
    { label: 'Mi Institución', value: '45', icon: Building2, color: 'blue' },
    { label: 'Usuarios', value: '23', icon: Users, color: 'green' },
    { label: 'Promedio', value: '68%', icon: TrendingUp, color: 'yellow' },
  ],
  [ROLES.EVALUATOR]: [
    { label: 'Mis Evaluaciones', value: '28', icon: ClipboardCheck, color: 'primary' },
    { label: 'Pendientes', value: '5', icon: Clock, color: 'yellow' },
    { label: 'Completadas', value: '23', icon: CheckCircle, color: 'green' },
    { label: 'Con Alertas', value: '3', icon: AlertTriangle, color: 'red' },
  ],
  [ROLES.ENTITY_USER]: [
    { label: 'Evaluaciones Asignadas', value: '12', icon: ClipboardCheck, color: 'primary' },
    { label: 'Sitios Evaluados', value: '8', icon: Building2, color: 'blue' },
    { label: 'Promedio', value: '74%', icon: TrendingUp, color: 'green' },
    { label: 'Requieren Atención', value: '2', icon: AlertTriangle, color: 'yellow' },
  ],
};

const colorClasses = {
  primary: styles.cardPrimary,
  blue: styles.cardBlue,
  green: styles.cardGreen,
  yellow: styles.cardYellow,
  red: styles.cardRed,
};

export default function Dashboard() {
  const { user } = useAuth();
  const userStats = stats[user?.role] || stats[ROLES.ENTITY_USER];

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Buenos días';
    if (hour < 18) return 'Buenas tardes';
    return 'Buenas noches';
  };

  return (
    <div className={styles.dashboard}>
      <div className={styles.header}>
        <h1 className={styles.title}>
          {getGreeting()}, {user?.name?.split(' ')[0] || 'Usuario'}
        </h1>
        <p className={styles.subtitle}>
          Resumen de actividad del sistema de evaluación
        </p>
      </div>

      <div className={styles.statsGrid}>
        {userStats.map((stat, index) => (
          <div key={index} className={`${styles.statCard} ${colorClasses[stat.color]}`}>
            <div className={styles.statIcon}>
              <stat.icon size={24} />
            </div>
            <div className={styles.statInfo}>
              <span className={styles.statValue}>{stat.value}</span>
              <span className={styles.statLabel}>{stat.label}</span>
            </div>
          </div>
        ))}
      </div>

      <div className={styles.sectionsGrid}>
        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Actividad Reciente</h2>
          <div className={styles.activityList}>
            <div className={styles.activityItem}>
              <div className={`${styles.activityDot} ${styles.dotGreen}`} />
              <div className={styles.activityContent}>
                <span className={styles.activityText}>
                  Evaluación completada: www.agetic.gob.bo
                </span>
                <span className={styles.activityTime}>Hace 2 horas</span>
              </div>
            </div>
            <div className={styles.activityItem}>
              <div className={`${styles.activityDot} ${styles.dotYellow}`} />
              <div className={styles.activityContent}>
                <span className={styles.activityText}>
                  Evaluación en progreso: www.minedu.gob.bo
                </span>
                <span className={styles.activityTime}>Hace 4 horas</span>
              </div>
            </div>
            <div className={styles.activityItem}>
              <div className={`${styles.activityDot} ${styles.dotBlue}`} />
              <div className={styles.activityContent}>
                <span className={styles.activityText}>
                  Nueva institución registrada: Ministerio de Salud
                </span>
                <span className={styles.activityTime}>Ayer</span>
              </div>
            </div>
          </div>
        </section>

        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Acciones Rápidas</h2>
          <div className={styles.quickActions}>
            <button className={styles.quickAction}>
              <ClipboardCheck size={20} />
              Nueva Evaluación
            </button>
            <button className={styles.quickAction}>
              <TrendingUp size={20} />
              Ver Reportes
            </button>
          </div>
        </section>
      </div>
    </div>
  );
}
