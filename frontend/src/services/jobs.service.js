import api from './api.js'

const jobsService = {
  async listJobs(params = {}) {
    const res = await api.get('/jobs', { params })
    return res.data
  },
  async getJob(id) {
    const res = await api.get(`/jobs/${id}`)
    return res.data
  },
  async createJob(payload) {
    const res = await api.post('/jobs', payload)
    return res.data
  },
  async updateJob(id, payload) {
    const res = await api.patch(`/jobs/${id}`, payload)
    return res.data
  },
  async assignTech(id, techId) {
    const res = await api.patch(`/jobs/${id}/assign`, { tech_id: techId })
    return res.data
  },
  async claimJob(id) {
    const res = await api.post(`/jobs/${id}/claim`)
    return res.data
  },
  async approveRequest(id) {
    const res = await api.patch(`/jobs/${id}/approve`)
    return res.data
  },
  async rejectRequest(id) {
    const res = await api.patch(`/jobs/${id}/reject`)
    return res.data
  },
  async deleteJob(id) {
    const res = await api.delete(`/jobs/${id}`)
    return res.data
  },
  async getComments(jobId) {
    const res = await api.get(`/jobs/${jobId}/comments`)
    return res.data
  },
  async addComment(jobId, content) {
    const res = await api.post(`/jobs/${jobId}/comments`, { content })
    return res.data
  },
  async deleteComment(jobId, commentId) {
    const res = await api.delete(`/jobs/${jobId}/comments/${commentId}`)
    return res.data
  },
}

export default jobsService
