<script setup>
/**
 * App.vue — Root component
 *
 * Applies the dark/light class to <html> reactively based on the theme store.
 * The theme store reads localStorage and the system media query.
 */
import { watchEffect }  from 'vue'
import { useThemeStore } from './stores/theme.store.js'

const theme = useThemeStore()

// Apply the resolved theme class to <html> whenever it changes
watchEffect(() => {
  const html = document.documentElement
  html.classList.remove('dark', 'light')
  html.classList.add(theme.resolvedTheme)
})
</script>

<template>
  <RouterView />
</template>
