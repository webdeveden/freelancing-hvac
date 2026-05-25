import api from './api.js'

const dispatchesService = {
  async listDispatches(params = {}) {
    const res = await api.get('/dispatches', { params })
    return res.data
  },
  async getDispatch(id) {
    const res = await api.get(`/dispatches/${id}`)
    return res.data
  },
  async createDispatch(payload) {
    const res = await api.post('/dispatches', payload)
    return res.data
  },
  async updateStatus(id, status) {
    const res = await api.patch(`/dispatches/${id}/status`, { status })
    return res.data
  },
}

export default dispatchesService
