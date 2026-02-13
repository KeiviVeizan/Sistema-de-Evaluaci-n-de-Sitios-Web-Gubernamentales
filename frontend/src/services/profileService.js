import api from './api';

const profileService = {
  async getProfile() {
    const response = await api.get('/profile/me');
    return response.data;
  },

  async updateProfile(data) {
    const response = await api.patch('/profile/me', data);
    return response.data;
  },

  async changePassword(data) {
    const response = await api.post('/profile/change-password', data);
    return response.data;
  },
};

export default profileService;
