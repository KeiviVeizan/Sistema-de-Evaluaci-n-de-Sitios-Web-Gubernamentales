import api from './api';

const followupService = {
  /**
   * Crea un seguimiento para un criterio no cumplido. Solo admin/secretaría.
   * @param {{ evaluation_id: number, criteria_result_id: number, due_date: string, notes?: string }} data
   */
  async create(data) {
    const response = await api.post('/followups', data);
    return response.data;
  },

  /**
   * Lista seguimientos con filtros opcionales.
   * Los entity_user solo ven los seguimientos de su institución (filtrado en backend).
   * @param {{ status?: string, evaluation_id?: number }} filters
   */
  async getAll(filters = {}) {
    const response = await api.get('/followups', { params: filters });
    return response.data;
  },

  /**
   * Institución marca un seguimiento como corregido.
   * Solo para usuarios con rol entity_user.
   * El estado debe ser 'pending' o 'rejected'.
   * @param {number} id
   * @param {{ notes?: string }} data
   */
  async markCorrected(id, data = {}) {
    const response = await api.patch(`/followups/${id}/mark-corrected`, data);
    return response.data;
  },

  /**
   * Admin/secretaría valida o rechaza una corrección reportada.
   * El estado debe ser 'corrected'.
   * @param {number} id
   * @param {{ approved: boolean, notes?: string }} data
   */
  async validate(id, data) {
    const response = await api.patch(`/followups/${id}/validate`, data);
    return response.data;
  },

  /**
   * Admin/secretaría cancela un seguimiento.
   * @param {number} id
   */
  async cancel(id) {
    const response = await api.patch(`/followups/${id}/cancel`);
    return response.data;
  },

  /**
   * Actualiza el estado y/o notas de un seguimiento (endpoint legacy, solo admin).
   * Usar markCorrected y validate para el flujo normal.
   * @param {number} id
   * @param {{ status: string, notes?: string }} data
   */
  async update(id, data) {
    const response = await api.patch(`/followups/${id}`, data);
    return response.data;
  },
};

export default followupService;
