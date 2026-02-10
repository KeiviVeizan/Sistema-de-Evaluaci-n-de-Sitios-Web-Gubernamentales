import api from './api';

const institutionService = {
  /**
   * Obtener lista de instituciones con filtros
   * @param {Object} options - Opciones de filtrado
   * @param {string} options.search - Búsqueda por nombre
   * @param {string} options.letter - Filtrar por letra inicial
   * @param {number} options.skip - Registros a saltar
   * @param {number} options.limit - Cantidad de registros
   * @returns {Promise} Lista de instituciones con total
   */
  async getAll({ search = '', letter = '', skip = 0, limit = 500 } = {}) {
    const params = { skip, limit };
    if (search) params.search = search;
    if (letter) params.letter = letter;

    const response = await api.get('/admin/institutions', { params });
    return response.data;
  },

  /**
   * Obtener detalle de una institución por ID
   * Incluye: datos de la institución, responsable y evaluaciones
   * @param {number} id - ID de la institución
   * @returns {Promise} Detalle completo de la institución
   */
  async getById(id) {
    const response = await api.get(`/admin/institutions/${id}`);
    return response.data;
  },

  /**
   * Crear una nueva institución
   * @param {Object} data - { name, domain, contact_name, contact_email, contact_position }
   * @returns {Promise} Institución creada con credenciales del usuario inicial
   */
  async create(data) {
    const response = await api.post('/admin/institutions', data);
    return response.data;
  },

  /**
   * Actualizar una institución
   * @param {number} id - ID de la institución
   * @param {Object} data - Datos a actualizar
   * @returns {Promise} Institución actualizada
   */
  async update(id, data) {
    const response = await api.put(`/admin/institutions/${id}`, data);
    return response.data;
  },

  /**
   * Activar/Desactivar una institución
   * @param {number} id - ID de la institución
   * @param {boolean} isActive - Estado deseado
   * @returns {Promise}
   */
  async toggleStatus(id, isActive) {
    const response = await api.patch(`/admin/institutions/${id}/status`, {
      is_active: isActive
    });
    return response.data;
  },

  /**
   * Eliminar una institución
   * @param {number} id - ID de la institución
   * @returns {Promise}
   */
  async delete(id) {
    const response = await api.delete(`/admin/institutions/${id}`);
    return response.data;
  },
};

export default institutionService;
