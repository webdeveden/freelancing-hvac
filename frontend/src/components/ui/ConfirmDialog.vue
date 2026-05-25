<script setup>
defineProps({
  title:   { type: String, default: 'Confirm' },
  message: { type: String, default: 'Are you sure?' },
  danger:  { type: Boolean, default: false },
})
const emit = defineEmits(['confirm', 'cancel'])
</script>

<template>
  <!-- Backdrop -->
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
    <div class="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full max-w-sm p-6">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">{{ title }}</h3>
      <p class="mt-2 text-sm text-gray-600 dark:text-gray-400">{{ message }}</p>

      <div class="mt-6 flex gap-3 justify-end">
        <button
          @click="emit('cancel')"
          class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-700
                 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition"
        >
          Cancel
        </button>
        <button
          @click="emit('confirm')"
          class="px-4 py-2 text-sm rounded-lg font-medium transition"
          :class="danger
            ? 'bg-red-600 hover:bg-red-700 text-white'
            : 'bg-brand-600 hover:bg-brand-700 text-white'"
        >
          Confirm
        </button>
      </div>
    </div>
  </div>
</template>
