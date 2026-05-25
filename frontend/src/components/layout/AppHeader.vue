<script setup>
import { useAuthStore } from '../../stores/auth.store.js'
import { useRouter }    from 'vue-router'
import ThemeToggle      from '../ui/ThemeToggle.vue'
import DispatchBell     from '../dispatch/DispatchBell.vue'

defineEmits(['toggle-sidebar'])

const auth   = useAuthStore()
const router = useRouter()

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <header class="h-14 flex items-center justify-between px-4 md:px-6
                 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800
                 shrink-0">

    <div class="flex items-center gap-3">
      <!-- Hamburger — mobile only -->
      <button
        class="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition md:hidden"
        @click="$emit('toggle-sidebar')"
        aria-label="Open menu"
      >
        <svg class="w-5 h-5 text-gray-600 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
        </svg>
      </button>

      <span class="text-sm font-semibold text-gray-700 dark:text-gray-200">
        HVAC Pro Dispatch
      </span>
    </div>

    <!-- Right controls -->
    <div class="flex items-center gap-3">
      <ThemeToggle />
      <DispatchBell />

      <div class="flex items-center gap-2 pl-3 border-l border-gray-200 dark:border-gray-700">
        <div class="text-right hidden sm:block">
          <p class="text-xs font-medium text-gray-800 dark:text-gray-200 leading-none">
            {{ auth.user?.name || 'User' }}
          </p>
          <p class="text-xs text-gray-400 dark:text-gray-500 capitalize mt-0.5">
            {{ auth.user?.role }}
          </p>
        </div>
        <button
          @click="logout"
          class="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition"
          title="Sign out"
        >
          <svg class="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
          </svg>
        </button>
      </div>
    </div>
  </header>
</template>
