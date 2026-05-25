<script setup>
defineProps({ size: { type: String, default: 'md' } })
</script>

<template>
  <div class="flex items-center justify-center">
    <div
      class="animate-spin rounded-full border-2 border-gray-300 dark:border-gray-700 border-t-brand-600"
      :class="size === 'sm' ? 'w-4 h-4' : size === 'lg' ? 'w-10 h-10' : 'w-7 h-7'"
    />
  </div>
</template>
