<script setup>
defineProps({
  status:   { type: String, required: true },
  priority: { type: String, default: 'normal' },
})

const statusStyles = {
  pending:      'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300',
  assigned:     'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300',
  'in-progress':'bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300',
  completed:    'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300',
  cancelled:    'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
}

const priorityStyles = {
  normal:    '',
  high:      'bg-orange-100 text-orange-800 dark:bg-orange-900/40 dark:text-orange-300',
  emergency: 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300 animate-pulse',
}
</script>

<template>
  <div class="flex items-center gap-1.5 flex-wrap">
    <span
      class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize"
      :class="statusStyles[status] || statusStyles.pending"
    >
      {{ status }}
    </span>
    <span
      v-if="priority !== 'normal'"
      class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize"
      :class="priorityStyles[priority]"
    >
      {{ priority }}
    </span>
  </div>
</template>
