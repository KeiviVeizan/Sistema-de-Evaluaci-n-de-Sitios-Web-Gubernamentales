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

  /**
   * Obtiene las evaluaciones de una institución específica.
   * Solo accesible para el entity_user de esa institución (y admins).
   *
   * @param {number} institutionId - ID de la institución
   * @returns {Promise<Array>}
   */
  async getByInstitution(institutionId) {
    const response = await api.get(`/evaluation/by-institution/${institutionId}`);
    return response.data;
  },

  /**
   * Descarga el informe PDF de una evaluación.
   * Crea un enlace temporal y dispara la descarga en el navegador.
   *
   * @param {number} evaluationId - ID de la evaluación
   * @returns {Promise<void>}
   */
  async downloadReport(evaluationId) {
    const response = await api.get(`/evaluation/${evaluationId}/report`, {
      responseType: 'blob',
    });

    const blob = new Blob([response.data], { type: 'application/pdf' });
    const url = URL.createObjectURL(blob);

    const fecha = new Date().toISOString().split('T')[0];
    const filename = `informe_evaluacion_${evaluationId}_${fecha}.pdf`;

    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();

    // Limpiar el objeto URL y el enlace temporal
    link.remove();
    URL.revokeObjectURL(url);
  },
};

export default evaluationService;
