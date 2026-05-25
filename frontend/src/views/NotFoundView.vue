<script setup>
import { useRouter } from 'vue-router'
const router = useRouter()
</script>

<template>
  <div class="min-h-screen flex flex-col items-center justify-center bg-gray-50 dark:bg-gray-950">
    <p class="text-8xl font-black text-brand-600 dark:text-brand-400">404</p>
    <h1 class="mt-4 text-2xl font-bold text-gray-800 dark:text-gray-100">Page not found</h1>
    <p class="mt-2 text-gray-500 dark:text-gray-400">The page you're looking for doesn't exist.</p>
    <button
      @click="router.push('/jobs')"
      class="mt-6 px-6 py-2 bg-brand-600 hover:bg-brand-700 text-white rounded-lg transition"
    >
      Back to Dashboard
    </button>
  </div>
</template>
