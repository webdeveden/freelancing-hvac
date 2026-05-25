/**
 * theme.store.js — Dark / Light / System theme management
 *
 * `theme` is the user's explicit choice: 'dark' | 'light' | 'system'
 * `resolvedTheme` is what actually gets applied to <html>:
 *   - 'system' resolves to 'dark' or 'light' based on prefers-color-scheme
 *   - explicit choices resolve to themselves
 *
 * The resolved class is applied in App.vue via watchEffect.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useThemeStore = defineStore('theme', () => {
  const STORAGE_KEY = 'hvac-theme'

  // Load from localStorage or default to 'system'
  const theme = ref(localStorage.getItem(STORAGE_KEY) || 'system')

  // Watch system preference
  const systemDark = ref(window.matchMedia('(prefers-color-scheme: dark)').matches)

  const mq = window.matchMedia('(prefers-color-scheme: dark)')
  mq.addEventListener('change', (e) => { systemDark.value = e.matches })

  const resolvedTheme = computed(() => {
    if (theme.value === 'system') return systemDark.value ? 'dark' : 'light'
    return theme.value
  })

  function setTheme(newTheme) {
    theme.value = newTheme
    localStorage.setItem(STORAGE_KEY, newTheme)
  }

  // Cycle: system → light → dark → system
  function cycleTheme() {
    const order = ['system', 'light', 'dark']
    const idx   = order.indexOf(theme.value)
    setTheme(order[(idx + 1) % order.length])
  }

  return { theme, resolvedTheme, setTheme, cycleTheme }
})
