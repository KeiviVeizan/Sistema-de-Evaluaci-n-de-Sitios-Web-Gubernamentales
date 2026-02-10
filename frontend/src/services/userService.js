import api from './api';

const userService = {
  /**
   * Obtener lista de usuarios con filtros
   * @param {Object} options - Opciones de filtrado
   * @param {string} options.search - Búsqueda por nombre o email
   * @param {number} options.skip - Registros a saltar
   * @param {number} options.limit - Cantidad de registros
   * @returns {Promise} Lista de usuarios con total
   */
  async getAll({ search = '', skip = 0, limit = 50 } = {}) {
    const params = { skip, limit };
    if (search) params.search = search;

    const response = await api.get('/admin/users', { params });
    return response.data;
  },

  /**
   * Crear un nuevo usuario
   * @param {Object} data - { username, email, password, full_name, role }
   * @returns {Promise} Usuario creado
   */
  async create(data) {
    const response = await api.post('/admin/users', data);
    return response.data;
  },

  /**
   * Actualizar un usuario
   * @param {number} id - ID del usuario
   * @param {Object} data - Datos a actualizar (full_name, email, role, is_active)
   * @returns {Promise} Usuario actualizado
   */
  async update(id, data) {
    const response = await api.put(`/admin/users/${id}`, data);
    return response.data;
  },
};

export default userService;
