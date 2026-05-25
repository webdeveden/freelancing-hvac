<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth.store.js'
import { useRouter }    from 'vue-router'

const store    = useAuthStore()
const router   = useRouter()

const mode     = ref('signin')   // 'signin' | 'signup'
const loading  = ref(false)
const error    = ref('')

// Sign-in fields
const email    = ref('')
const password = ref('')

// Sign-up fields
const fullName  = ref('')
const regEmail  = ref('')
const regPass   = ref('')
const regPass2  = ref('')
const role      = ref('dispatcher')

function switchMode(m) {
  mode.value  = m
  error.value = ''
}

async function handleSignIn() {
  error.value = ''
  if (!email.value || !password.value) { error.value = 'Please enter your email and password.'; return }
  loading.value = true
  try {
    await store.login(email.value, password.value)
    router.push(router.currentRoute.value.query.redirect || '/jobs')
  } catch (err) {
    error.value = err.response?.data?.error || 'Login failed. Please try again.'
  } finally {
    loading.value = false
  }
}

async function handleSignUp() {
  error.value = ''
  if (!fullName.value || !regEmail.value || !regPass.value) { error.value = 'All fields are required.'; return }
  if (regPass.value !== regPass2.value) { error.value = 'Passwords do not match.'; return }
  if (regPass.value.length < 8) { error.value = 'Password must be at least 8 characters.'; return }
  loading.value = true
  try {
    await store.register(fullName.value, regEmail.value, regPass.value, role.value)
    router.push('/jobs')
  } catch (err) {
    error.value = err.response?.data?.error || 'Registration failed. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-brand-900 to-brand-600 dark:from-gray-950 dark:to-gray-900 px-4">
    <div class="w-full max-w-md">
      <!-- Logo / Brand -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-white/10 backdrop-blur-sm mb-4">
          <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z"/>
          </svg>
        </div>
        <h1 class="text-3xl font-bold text-white">HVAC Pro</h1>
        <p class="text-white/70 mt-1 text-sm">Dispatch Dashboard</p>
      </div>

      <!-- Card -->
      <div class="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl p-8">

        <!-- Tab toggle -->
        <div class="flex rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700 mb-6">
          <button
            @click="switchMode('signin')"
            class="flex-1 py-2 text-sm font-medium transition-colors"
            :class="mode === 'signin'
              ? 'bg-brand-600 text-white'
              : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800'"
          >Sign In</button>
          <button
            @click="switchMode('signup')"
            class="flex-1 py-2 text-sm font-medium transition-colors"
            :class="mode === 'signup'
              ? 'bg-brand-600 text-white'
              : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800'"
          >Sign Up</button>
        </div>

        <!-- Sign In form -->
        <form v-if="mode === 'signin'" @submit.prevent="handleSignIn" class="space-y-5">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email</label>
            <input v-model="email" type="email" autocomplete="email" placeholder="you@hvacpro.com"
              class="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700
                     bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
                     focus:outline-none focus:ring-2 focus:ring-brand-500 transition"/>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Password</label>
            <input v-model="password" type="password" autocomplete="current-password" placeholder="••••••••"
              class="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700
                     bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
                     focus:outline-none focus:ring-2 focus:ring-brand-500 transition"/>
          </div>
          <p v-if="error" class="text-sm text-red-600 dark:text-red-400">{{ error }}</p>
          <button type="submit" :disabled="loading"
            class="w-full py-2.5 bg-brand-600 hover:bg-brand-700 disabled:opacity-60
                   text-white font-semibold rounded-lg transition">
            <span v-if="loading">Signing in…</span>
            <span v-else>Sign In</span>
          </button>
        </form>

        <!-- Sign Up form -->
        <form v-else @submit.prevent="handleSignUp" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Full Name</label>
            <input v-model="fullName" type="text" autocomplete="name" placeholder="Jane Smith"
              class="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700
                     bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
                     focus:outline-none focus:ring-2 focus:ring-brand-500 transition"/>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email</label>
            <input v-model="regEmail" type="email" autocomplete="email" placeholder="you@hvacpro.com"
              class="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700
                     bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
                     focus:outline-none focus:ring-2 focus:ring-brand-500 transition"/>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Role</label>
            <select v-model="role"
              class="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700
                     bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
                     focus:outline-none focus:ring-2 focus:ring-brand-500 transition">
              <option value="dispatcher">Dispatcher</option>
              <option value="tech">Technician</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Password</label>
            <input v-model="regPass" type="password" autocomplete="new-password" placeholder="Min 8 characters"
              class="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700
                     bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
                     focus:outline-none focus:ring-2 focus:ring-brand-500 transition"/>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Confirm Password</label>
            <input v-model="regPass2" type="password" autocomplete="new-password" placeholder="••••••••"
              class="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700
                     bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
                     focus:outline-none focus:ring-2 focus:ring-brand-500 transition"/>
          </div>
          <p v-if="error" class="text-sm text-red-600 dark:text-red-400">{{ error }}</p>
          <button type="submit" :disabled="loading"
            class="w-full py-2.5 bg-brand-600 hover:bg-brand-700 disabled:opacity-60
                   text-white font-semibold rounded-lg transition">
            <span v-if="loading">Creating account…</span>
            <span v-else>Create Account</span>
          </button>
        </form>

        <p class="mt-6 text-xs text-center text-gray-400 dark:text-gray-600">
          HVAC Pro Dispatch System &mdash; Internal use only
        </p>
      </div>
    </div>
  </div>
</template>
