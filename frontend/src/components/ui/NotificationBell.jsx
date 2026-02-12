import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bell, Check, CheckCheck } from 'lucide-react';
import notificationService from '../../services/notificationService';
import styles from './NotificationBell.module.css';

/**
 * Campana de notificaciones in-app para evaluadores.
 *
 * - Muestra badge con conteo de no leídas
 * - Polling cada 30 segundos para actualizar el contador
 * - Al hacer clic despliega el panel con las últimas notificaciones
 * - Permite marcar como leídas individualmente o todas juntas
 * - Al hacer clic en una notificación navega al enlace asociado
 */
export default function NotificationBell() {
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifications, setNotifications] = useState([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const panelRef = useRef(null);
  const navigate = useNavigate();

  // Cargar contador de no leídas
  const fetchUnreadCount = useCallback(async () => {
    try {
      const data = await notificationService.getUnreadCount();
      setUnreadCount(data.count);
    } catch {
      // Silencioso — no bloquear la UI por errores de notificaciones
    }
  }, []);

  // Cargar lista de notificaciones al abrir el panel
  const fetchNotifications = useCallback(async () => {
    setLoading(true);
    try {
      const data = await notificationService.getAll();
      setNotifications(data);
    } catch {
      // Silencioso
    } finally {
      setLoading(false);
    }
  }, []);

  // Polling cada 30 segundos
  useEffect(() => {
    fetchUnreadCount();
    const interval = setInterval(fetchUnreadCount, 30_000);
    return () => clearInterval(interval);
  }, [fetchUnreadCount]);

  // Cerrar panel al hacer clic fuera
  useEffect(() => {
    if (!open) return;
    const handleOutsideClick = (e) => {
      if (panelRef.current && !panelRef.current.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handleOutsideClick);
    return () => document.removeEventListener('mousedown', handleOutsideClick);
  }, [open]);

  const handleToggle = () => {
    if (!open) {
      fetchNotifications();
    }
    setOpen((prev) => !prev);
  };

  const handleMarkRead = async (notif, e) => {
    e.stopPropagation();
    if (notif.read) return;
    try {
      await notificationService.markAsRead(notif.id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === notif.id ? { ...n, read: true } : n))
      );
      setUnreadCount((prev) => Math.max(0, prev - 1));
    } catch {
      // Silencioso
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await notificationService.markAllRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
      setUnreadCount(0);
    } catch {
      // Silencioso
    }
  };

  const handleNotificationClick = async (notif) => {
    if (!notif.read) {
      try {
        await notificationService.markAsRead(notif.id);
        setNotifications((prev) =>
          prev.map((n) => (n.id === notif.id ? { ...n, read: true } : n))
        );
        setUnreadCount((prev) => Math.max(0, prev - 1));
      } catch {
        // Silencioso
      }
    }
    if (notif.link) {
      setOpen(false);
      navigate(notif.link);
    }
  };

  const formatDate = (iso) => {
    if (!iso) return '';
    const d = new Date(iso);
    return d.toLocaleDateString('es-BO', {
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className={styles.wrapper} ref={panelRef}>
      {/* Botón campana */}
      <button
        className={styles.bellButton}
        onClick={handleToggle}
        aria-label={`Notificaciones${unreadCount > 0 ? ` (${unreadCount} sin leer)` : ''}`}
        title="Notificaciones"
      >
        <Bell size={20} />
        {unreadCount > 0 && (
          <span className={styles.badge}>
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {/* Panel desplegable */}
      {open && (
        <div className={styles.panel}>
          <div className={styles.panelHeader}>
            <span className={styles.panelTitle}>Notificaciones</span>
            {unreadCount > 0 && (
              <button
                className={styles.markAllBtn}
                onClick={handleMarkAllRead}
                title="Marcar todas como leídas"
              >
                <CheckCheck size={14} />
                <span>Todas leídas</span>
              </button>
            )}
          </div>

          <div className={styles.panelBody}>
            {loading ? (
              <div className={styles.empty}>Cargando...</div>
            ) : notifications.length === 0 ? (
              <div className={styles.empty}>No hay notificaciones</div>
            ) : (
              notifications.map((notif) => (
                <div
                  key={notif.id}
                  className={`${styles.notifItem} ${notif.read ? styles.read : styles.unread}`}
                  onClick={() => handleNotificationClick(notif)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => e.key === 'Enter' && handleNotificationClick(notif)}
                >
                  <div className={styles.notifContent}>
                    <p className={styles.notifTitle}>{notif.title}</p>
                    <p className={styles.notifMessage}>{notif.message}</p>
                    <p className={styles.notifDate}>{formatDate(notif.created_at)}</p>
                  </div>
                  {!notif.read && (
                    <button
                      className={styles.readBtn}
                      onClick={(e) => handleMarkRead(notif, e)}
                      title="Marcar como leída"
                    >
                      <Check size={14} />
                    </button>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
