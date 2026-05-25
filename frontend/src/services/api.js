/**
 * api.js — Axios instance with JWT interceptor
 *
 * All API services import this instance. The request interceptor automatically
 * adds the Authorization header from the auth store, so individual service
 * calls never need to handle tokens manually.
 */

import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:3001/api',
  headers: { 'Content-Type': 'application/json' },
})

// Attach JWT to every outgoing request
api.interceptors.request.use((config) => {
  // Import lazily to avoid circular dependency with auth store initialization
  const token = localStorage.getItem('hvac-token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Redirect to login on 401 (expired or invalid token)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('hvac-token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
