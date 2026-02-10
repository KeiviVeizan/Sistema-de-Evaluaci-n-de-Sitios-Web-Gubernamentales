import api from './api';

const authService = {
  /**
   * Iniciar sesión con username y contraseña (Paso 1 de 2FA)
   * @param {string} username
   * @param {string} password
   * @returns {Promise} Respuesta con username para el paso 2
   */
  async login(username, password) {
    const response = await api.post('/auth/login', { username, password });
    return response.data;
  },

  /**
   * Verificar código 2FA (Paso 2)
   * @param {string} username - Username del usuario
   * @param {string} code - Código 2FA de 6 dígitos
   * @returns {Promise} Respuesta con tokens de acceso
   */
  async verify2FA(username, code) {
    const response = await api.post('/auth/verify-2fa', { username, code });
    return response.data;
  },

  /**
   * Configurar 2FA para el usuario (genera QR code)
   * @returns {Promise} Respuesta con QR code y secret
   */
  async setup2FA() {
    const response = await api.post('/auth/setup-2fa');
    return response.data;
  },

  /**
   * Activar 2FA después de configurarlo
   * @param {string} code - Código de verificación inicial
   * @returns {Promise}
   */
  async enable2FA(code) {
    const response = await api.post('/auth/enable-2fa', { code });
    return response.data;
  },

  /**
   * Desactivar 2FA
   * @param {string} password - Contraseña para confirmar
   * @returns {Promise}
   */
  async disable2FA(password) {
    const response = await api.post('/auth/disable-2fa', { password });
    return response.data;
  },

  /**
   * Cerrar sesión
   * @returns {Promise}
   */
  async logout() {
    try {
      await api.post('/auth/logout');
    } finally {
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
    }
  },

  /**
   * Obtener perfil del usuario actual
   * @returns {Promise} Datos del usuario
   */
  async getProfile() {
    const response = await api.get('/auth/me');
    return response.data;
  },

  /**
   * Refrescar token de acceso
   * @returns {Promise} Nuevo token de acceso
   */
  async refreshToken() {
    const refreshToken = localStorage.getItem('refreshToken');
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }
    const response = await api.post('/auth/refresh', {
      refresh_token: refreshToken
    });
    return response.data;
  },

  /**
   * Guardar tokens en localStorage
   * @param {string} accessToken
   * @param {string} refreshToken
   */
  saveTokens(accessToken, refreshToken) {
    localStorage.setItem('accessToken', accessToken);
    if (refreshToken) {
      localStorage.setItem('refreshToken', refreshToken);
    }
  },

  /**
   * Verificar si hay una sesión activa
   * @returns {boolean}
   */
  isAuthenticated() {
    return !!localStorage.getItem('accessToken');
  },

  /**
   * Obtener token de acceso actual
   * @returns {string|null}
   */
  getAccessToken() {
    return localStorage.getItem('accessToken');
  },
};

export default authService;
