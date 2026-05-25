<script setup>
import { computed } from 'vue'

const props = defineProps({
  dispatch: { type: Object, required: true },
})
const emit = defineEmits(['status-change'])

const statusStyles = {
  sent:         'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300',
  acknowledged: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/40 dark:text-indigo-300',
  'en-route':   'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300',
  'on-site':    'bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300',
  resolved:     'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300',
}

const nextStatus = computed(() => {
  const flow = { sent: 'acknowledged', acknowledged: 'en-route', 'en-route': 'on-site', 'on-site': 'resolved' }
  return flow[props.dispatch.status] || null
})

function formatTime(iso) {
  return new Date(iso).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <div
    class="bg-white dark:bg-gray-900 rounded-xl border shadow-sm p-4"
    :class="dispatch.job_priority === 'emergency'
      ? 'border-red-400 dark:border-red-600'
      : 'border-gray-200 dark:border-gray-800'"
  >
    <!-- Top row -->
    <div class="mb-2">
      <div class="flex items-center justify-between gap-2 mb-1">
        <span
          class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium"
          :class="statusStyles[dispatch.status] || statusStyles.sent"
        >
          {{ dispatch.status }}
        </span>
      </div>
      <RouterLink
        :to="`/jobs/${dispatch.job_id}`"
        class="text-sm font-semibold text-gray-900 dark:text-gray-100 hover:text-brand-600 transition"
      >
        {{ dispatch.service_type || 'Job #' + dispatch.job_id }}
      </RouterLink>
      <p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
        {{ dispatch.caller_name }} &middot; {{ dispatch.caller_phone }}
      </p>
    </div>

    <!-- Address -->
    <a
      v-if="dispatch.address"
      :href="`https://maps.google.com/maps?q=${encodeURIComponent(dispatch.address + (dispatch.city ? ', ' + dispatch.city : ''))}`"
      target="_blank"
      rel="noopener"
      class="block text-xs text-brand-600 dark:text-brand-400 hover:underline mb-2"
    >
      {{ dispatch.address }}<span v-if="dispatch.city">, {{ dispatch.city }}</span>
    </a>

    <!-- Tech + time -->
    <div class="flex items-center justify-between text-xs text-gray-400 dark:text-gray-500 mt-2">
      <span>
        <span class="font-medium text-gray-600 dark:text-gray-400">Tech:</span>
        {{ dispatch.tech_name || 'Unassigned' }}
      </span>
      <span>{{ formatTime(dispatch.dispatched_at) }}</span>
    </div>

    <!-- Notes -->
    <p v-if="dispatch.dispatch_notes" class="mt-2 text-xs text-gray-500 dark:text-gray-400 italic truncate">
      "{{ dispatch.dispatch_notes }}"
    </p>

    <!-- Advance status button -->
    <button
      v-if="nextStatus"
      @click="emit('status-change', { id: dispatch.id, status: nextStatus })"
      class="mt-3 w-full py-1.5 text-xs font-medium rounded-lg border
             border-brand-300 dark:border-brand-700 text-brand-700 dark:text-brand-400
             hover:bg-brand-50 dark:hover:bg-brand-950/40 transition capitalize"
    >
      Mark {{ nextStatus }}
    </button>
  </div>
</template>
