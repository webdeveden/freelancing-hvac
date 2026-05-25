/**
 * auth.store.js — JWT authentication state
 *
 * Persists the JWT in localStorage. Decodes the payload (base64) to extract
 * user info and role — no extra /me call needed after login.
 *
 * `isAdmin` is derived from the role in the token and drives all
 * role-based UI rendering in components.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import authService from '../services/auth.service.js'

const TOKEN_KEY = 'hvac-token'

function decodeToken(token) {
  try {
    const payload = token.split('.')[1]
    return JSON.parse(atob(payload))
  } catch {
    return null
  }
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem(TOKEN_KEY) || null)
  const user  = ref(token.value ? decodeToken(token.value) : null)

  const isLoggedIn    = computed(() => !!token.value)
  const isAdmin       = computed(() => user.value?.role === 'admin')
  const isDispatcher  = computed(() => user.value?.role === 'dispatcher')
  const isTech        = computed(() => user.value?.role === 'tech')

  async function login(email, password) {
    const data = await authService.login(email, password)
    token.value = data.token
    user.value  = data.user
    localStorage.setItem(TOKEN_KEY, data.token)
  }

  async function register(full_name, email, password, role) {
    const data = await authService.register(full_name, email, password, role)
    token.value = data.token
    user.value  = data.user
    localStorage.setItem(TOKEN_KEY, data.token)
  }

  function logout() {
    token.value = null
    user.value  = null
    localStorage.removeItem(TOKEN_KEY)
  }

  // Called by the Axios interceptor to get the current token
  function getToken() {
    return token.value
  }

  return { token, user, isLoggedIn, isAdmin, isDispatcher, isTech, login, register, logout, getToken }
})
