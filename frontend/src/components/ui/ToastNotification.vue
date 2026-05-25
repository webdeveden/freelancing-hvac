<script setup>
/**
 * ToastNotification.vue — Real-time event toasts
 *
 * Emergency toasts are persistent (red, no auto-dismiss) and link to the job.
 * Info/dispatch toasts auto-dismiss in 5s (handled by useSocket.js).
 */
import { useRouter } from "vue-router";

const props = defineProps({
  toast: { type: Object, required: true },
});
const emit = defineEmits(["dismiss"]);
const router = useRouter();

function goToJob() {
  if (props.toast.job?.id) router.push(`/jobs/${props.toast.job.id}`);
  emit("dismiss");
}
</script>

<template>
  <!-- Emergency: full-width persistent banner at top -->
  <div
    v-if="toast.type === 'emergency'"
    class="fixed top-0 inset-x-0 z-50 bg-red-600 text-white shadow-lg px-6 py-3"
  >
    <div class="flex items-start gap-3">
      <!-- Icon -->
      <svg
        class="w-5 h-5 shrink-0 mt-0.5 animate-pulse"
        fill="currentColor"
        viewBox="0 0 20 20"
      >
        <path
          fill-rule="evenodd"
          d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
          clip-rule="evenodd"
        />
      </svg>
      <!-- Message — wraps naturally, full text always visible -->
      <div class="flex-1 min-w-0">
        <p class="font-semibold text-sm leading-snug">
          EMERGENCY: {{ toast.message }}
        </p>
      </div>
      <!-- Actions -->
      <div class="flex items-center gap-3 shrink-0 ml-4">
        <button
          @click="goToJob"
          class="text-sm underline hover:no-underline whitespace-nowrap"
        >
          View Job
        </button>
        <button @click="emit('dismiss')" class="p-1 hover:bg-red-700 rounded">
          <svg
            class="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>
    </div>
  </div>

  <!-- Regular toast: bottom-right floating card -->
  <div
    v-else
    class="fixed bottom-5 right-5 z-40 flex items-start gap-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-xl p-4 max-w-sm"
  >
    <!-- Icon -->
    <div
      class="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
      :class="{
        'bg-brand-100 dark:bg-brand-900': toast.type === 'dispatch',
        'bg-teal-100 dark:bg-teal-900':   toast.type === 'request',
        'bg-green-100 dark:bg-green-900':  toast.type === 'info',
      }"
    >
      <!-- Request icon: hand raise -->
      <svg v-if="toast.type === 'request'" class="w-4 h-4 text-teal-600 dark:text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
          d="M7 11.5V14m0-2.5v-6a1.5 1.5 0 113 0m-3 6a1.5 1.5 0 00-3 0v2a7.5 7.5 0 0015 0v-5a1.5 1.5 0 00-3 0m-6-3V11m0-5.5v-1a1.5 1.5 0 013 0v1m0 0V11m0-5.5a1.5 1.5 0 013 0v3m0 0V11"/>
      </svg>
      <!-- Bell icon for dispatch / info -->
      <svg v-else class="w-4 h-4" :class="toast.type === 'dispatch' ? 'text-brand-600' : 'text-green-600'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
          d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/>
      </svg>
    </div>
    <div class="flex-1 min-w-0">
      <p class="text-sm font-medium text-gray-900 dark:text-gray-100">
        {{ toast.type === 'dispatch' ? 'New Dispatch' : toast.type === 'request' ? 'Job Request' : 'New Job' }}
      </p>
      <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5 truncate">
        {{ toast.message }}
      </p>
      <button
        v-if="toast.job"
        @click="goToJob"
        class="text-xs text-brand-600 dark:text-brand-400 mt-1 hover:underline"
      >
        View →
      </button>
    </div>
    <button
      @click="emit('dismiss')"
      class="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
    >
      <svg
        class="w-3.5 h-3.5 text-gray-400"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M6 18L18 6M6 6l12 12"
        />
      </svg>
    </button>
  </div>
</template>
