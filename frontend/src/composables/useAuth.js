/**
 * useAuth.js — Auth composable
 *
 * Thin wrapper over the auth store for ergonomic use in templates.
 */

import { useAuthStore } from '../stores/auth.store.js'
import { useRouter }    from 'vue-router'

export function useAuth() {
  const store  = useAuthStore()
  const router = useRouter()

  async function login(email, password) {
    await store.login(email, password)
    router.push('/jobs')
  }

  async function logout() {
    store.logout()
    router.push('/login')
  }

  return {
    user:       store.user,
    isLoggedIn: store.isLoggedIn,
    isAdmin:    store.isAdmin,
    login,
    logout,
  }
}
