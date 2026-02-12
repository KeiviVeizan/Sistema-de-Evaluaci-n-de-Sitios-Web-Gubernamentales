import api from './api';

const notificationService = {
  /**
   * Obtiene las notificaciones del usuario autenticado.
   * @param {{ unread_only?: boolean }} params
   */
  async getAll(params = {}) {
    const response = await api.get('/notifications', { params });
    return response.data;
  },

  /**
   * Obtiene el contador de notificaciones no leídas.
   * @returns {{ count: number }}
   */
  async getUnreadCount() {
    const response = await api.get('/notifications/unread-count');
    return response.data;
  },

  /**
   * Marca una notificación específica como leída.
   * @param {number} id
   */
  async markAsRead(id) {
    const response = await api.patch(`/notifications/${id}/read`);
    return response.data;
  },

  /**
   * Marca todas las notificaciones del usuario como leídas.
   */
  async markAllRead() {
    const response = await api.post('/notifications/mark-all-read');
    return response.data;
  },
};

export default notificationService;
