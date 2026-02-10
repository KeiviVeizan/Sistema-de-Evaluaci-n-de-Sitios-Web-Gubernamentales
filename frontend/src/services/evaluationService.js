import api from './api';

const evaluationService = {
  /**
   * Guarda una evaluación manual en la base de datos.
   *
   * @param {Object} data
   * @param {number} data.institution_id - ID de la institución evaluada
   * @param {Array<{criterion_id: string, status: string, observations?: string}>} data.criteria_results
   * @returns {Promise<{evaluation_id: number, institution_id: number, scores: Object, total_score: number, created_at: string}>}
   */
  async saveEvaluation({ institution_id, criteria_results, scores_override }) {
    const response = await api.post('/evaluation/save', {
      institution_id,
      criteria_results,
      scores_override,
    });
    return response.data;
  },

  /**
   * Obtiene la lista paginada de evaluaciones.
   *
   * @param {Object} options
   * @param {number} [options.page=1]
   * @param {number} [options.page_size=10]
   * @param {string} [options.status] - Filtrar por estado
   * @returns {Promise}
   */
  async list({ page = 1, page_size = 10, status } = {}) {
    const params = { page, page_size };
    if (status) params.status = status;
    const response = await api.get('/evaluation/list', { params });
    return response.data;
  },

  /**
   * Obtiene el detalle completo de una evaluación por ID.
   *
   * @param {number} id - ID de la evaluación
   * @returns {Promise}
   */
  async getById(id) {
    const response = await api.get(`/evaluation/${id}`);
    return response.data;
  },

  /**
   * Elimina una evaluación por ID.
   *
   * @param {number} id - ID de la evaluación
   * @returns {Promise}
   */
  async delete(id) {
    const response = await api.delete(`/evaluation/${id}`);
    return response.data;
  },
};

export default evaluationService;
