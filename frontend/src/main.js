/**
 * main.js — Vue application entry point
 *
 * Mounts the app, registers Pinia and Vue Router.
 * Theme initialization runs before mount so the correct class
 * is on <html> before the first paint (avoids flash of wrong theme).
 */

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App    from './App.vue'
import router from './router/index.js'
import './app.css'

const pinia = createPinia()
const app   = createApp(App)

app.use(pinia)
app.use(router)
app.mount('#app')
