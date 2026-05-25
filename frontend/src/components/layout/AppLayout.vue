<script setup>
import { ref, onMounted }   from 'vue'
import AppHeader             from './AppHeader.vue'
import AppSidebar            from './AppSidebar.vue'
import ToastNotification     from '../ui/ToastNotification.vue'
import { useSocket }         from '../../composables/useSocket.js'

const { connect, toast, dismissToast } = useSocket()

const sidebarOpen = ref(false)

// Swipe right from the left edge of the screen to open sidebar
let touchStartX = 0
function onTouchStart(e) { touchStartX = e.touches[0].clientX }
function onTouchEnd(e) {
  const dx = e.changedTouches[0].clientX - touchStartX
  if (touchStartX < 30 && dx > 60) sidebarOpen.value = true
}

onMounted(() => connect())
</script>

<template>
  <div
    class="flex h-screen overflow-hidden bg-gray-50 dark:bg-gray-950"
    @touchstart.passive="onTouchStart"
    @touchend.passive="onTouchEnd"
  >
    <AppSidebar
      :is-open="sidebarOpen"
      @close="sidebarOpen = false"
    />

    <div class="flex flex-col flex-1 min-w-0 overflow-hidden">
      <AppHeader @toggle-sidebar="sidebarOpen = !sidebarOpen" />

      <main class="flex-1 overflow-y-auto p-4 md:p-6">
        <slot />
      </main>
    </div>

    <ToastNotification
      v-if="toast"
      :toast="toast"
      @dismiss="dismissToast"
    />
  </div>
</template>
