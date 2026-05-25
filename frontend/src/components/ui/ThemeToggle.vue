<script setup>
import { computed }      from 'vue'
import { useThemeStore } from '../../stores/theme.store.js'

const theme = useThemeStore()

const icon = computed(() => {
  if (theme.theme === 'dark')   return '🌙'
  if (theme.theme === 'light')  return '☀️'
  return '💻'  // system
})

const label = computed(() => {
  if (theme.theme === 'dark')  return 'Dark'
  if (theme.theme === 'light') return 'Light'
  return 'System'
})
</script>

<template>
  <button
    @click="theme.cycleTheme()"
    class="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium
           bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700
           text-gray-700 dark:text-gray-300 transition"
    :title="`Theme: ${label} — click to cycle`"
  >
    <span>{{ icon }}</span>
    <span class="hidden sm:inline">{{ label }}</span>
  </button>
</template>
