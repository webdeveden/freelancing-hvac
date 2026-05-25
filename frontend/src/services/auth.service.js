import api from './api.js'

const authService = {
  async login(email, password) {
    const res = await api.post('/auth/login', { email, password })
    return res.data
  },
  async register(full_name, email, password, role) {
    const res = await api.post('/auth/register', { full_name, email, password, role })
    return res.data
  },
  async getMe() {
    const res = await api.get('/auth/me')
    return res.data
  },
}

export default authService
