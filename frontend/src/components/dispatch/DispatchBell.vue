<script setup>
import { useDispatchesStore } from '../../stores/dispatches.store.js'
import { useRouter }          from 'vue-router'

const dispatches = useDispatchesStore()
const router     = useRouter()

function goToDispatch() {
  dispatches.clearAlerts()
  router.push('/dispatch')
}
</script>

<template>
  <button
    @click="goToDispatch"
    class="relative p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition"
    title="Dispatch board"
  >
    <svg class="w-5 h-5 text-gray-600 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
        d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/>
    </svg>
    <!-- Badge -->
    <span
      v-if="dispatches.unreadAlerts > 0"
      class="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-red-500 text-white
             text-[10px] font-bold flex items-center justify-center animate-bounce"
    >
      {{ dispatches.unreadAlerts > 9 ? '9+' : dispatches.unreadAlerts }}
    </span>
  </button>
</template>
