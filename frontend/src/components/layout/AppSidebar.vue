<script setup>
import { ref } from 'vue'
import { useRoute } from 'vue-router'

const props = defineProps({
  isOpen: { type: Boolean, default: false },
})
const emit = defineEmits(['close'])

const route = useRoute()

// Swipe left to close
let touchStartX = 0
function onTouchStart(e) { touchStartX = e.touches[0].clientX }
function onTouchEnd(e) {
  if (touchStartX - e.changedTouches[0].clientX > 50) emit('close')
}
</script>

<template>
  <!-- Backdrop — mobile only, closes sidebar on tap -->
  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="isOpen"
        class="fixed inset-0 z-30 bg-black/50 md:hidden"
        @click="emit('close')"
      />
    </Transition>
  </Teleport>

  <!-- Sidebar panel -->
  <nav
    class="fixed inset-y-0 left-0 z-40 w-64
           md:static md:z-auto md:w-56 md:translate-x-0
           shrink-0 bg-gray-900 dark:bg-gray-950 text-white flex flex-col
           transform transition-transform duration-300 ease-in-out"
    :class="isOpen ? 'translate-x-0' : '-translate-x-full'"
    @touchstart.passive="onTouchStart"
    @touchend.passive="onTouchEnd"
  >
    <!-- Brand -->
    <div class="h-14 flex items-center px-5 border-b border-gray-800 shrink-0">
      <div class="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center mr-3 shrink-0">
        <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z"/>
        </svg>
      </div>
      <span class="text-sm font-bold tracking-wide">HVAC Pro</span>

      <!-- Close button — mobile only -->
      <button
        class="ml-auto p-1.5 rounded-lg hover:bg-gray-800 transition md:hidden"
        @click="emit('close')"
      >
        <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
        </svg>
      </button>
    </div>

    <!-- Nav links -->
    <div class="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
      <RouterLink
        to="/jobs"
        class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition"
        :class="route.path.startsWith('/jobs')
          ? 'bg-brand-600 text-white'
          : 'text-gray-400 hover:bg-gray-800 hover:text-white'"
        @click="emit('close')"
      >
        <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
        </svg>
        Jobs
      </RouterLink>

      <RouterLink
        to="/dispatch"
        class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition"
        :class="route.path === '/dispatch'
          ? 'bg-brand-600 text-white'
          : 'text-gray-400 hover:bg-gray-800 hover:text-white'"
        @click="emit('close')"
      >
        <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
        </svg>
        Dispatch Board
      </RouterLink>
    </div>

    <!-- Footer -->
    <div class="px-5 py-3 border-t border-gray-800 shrink-0">
      <p class="text-xs text-gray-600">AI Receptionist v1.0</p>
    </div>
  </nav>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from,
.fade-leave-to    { opacity: 0; }
</style>
