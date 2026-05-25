<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['update:modelValue', 'filter'])

const local = ref({
  status: props.modelValue.status || '',
  priority: props.modelValue.priority || '',
})

// Sync when parent updates filters externally (e.g. clicking a summary card)
watch(() => props.modelValue, (val) => {
  if (val.status   !== local.value.status)   local.value.status   = val.status   || ''
  if (val.priority !== local.value.priority) local.value.priority = val.priority || ''
}, { deep: true })

watch(local, (val) => {
  emit('update:modelValue', { ...val })
  emit('filter', { ...val })
}, { deep: true })

function reset() {
  local.value = { status: '', priority: '' }
}
</script>

<template>
  <div class="flex flex-wrap items-center gap-3">
    <!-- Status filter -->
    <select
      v-model="local.status"
      class="text-sm px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-700
             bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300
             focus:outline-none focus:ring-2 focus:ring-brand-500"
    >
      <option value="">All Statuses</option>
      <option value="pending">Pending</option>
      <option value="assigned">Assigned</option>
      <option value="in-progress">In Progress</option>
      <option value="completed">Completed</option>
      <option value="cancelled">Cancelled</option>
    </select>

    <!-- Priority filter -->
    <select
      v-model="local.priority"
      class="text-sm px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-700
             bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300
             focus:outline-none focus:ring-2 focus:ring-brand-500"
    >
      <option value="">All Priorities</option>
      <option value="normal">Normal</option>
      <option value="high">High</option>
      <option value="emergency">Emergency</option>
    </select>

    <!-- Reset -->
    <button
      v-if="local.status || local.priority"
      @click="reset"
      class="text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 underline"
    >
      Clear filters
    </button>
  </div>
</template>
