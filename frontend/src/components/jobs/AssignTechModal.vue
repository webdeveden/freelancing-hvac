<script setup>
import { ref, onMounted } from 'vue'
import api from '../../services/api.js'

const props = defineProps({
  jobId: { type: Number, required: true },
})
const emit = defineEmits(['assigned', 'close'])

const techs    = ref([])
const selected = ref(null)
const loading  = ref(false)

onMounted(async () => {
  const res = await api.get('/techs')
  techs.value = res.data.techs
})

async function assign() {
  if (!selected.value) return
  loading.value = true
  try {
    const res = await api.patch(`/jobs/${props.jobId}/assign`, { tech_id: selected.value })
    emit('assigned', res.data.job)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
    <div class="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full max-w-sm p-6">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Assign Technician</h3>

      <div class="space-y-2">
        <label
          v-for="tech in techs"
          :key="tech.id"
          class="flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition"
          :class="selected === tech.id
            ? 'border-brand-500 bg-brand-50 dark:bg-brand-950'
            : 'border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800'"
        >
          <input type="radio" v-model="selected" :value="tech.id" class="accent-brand-600" />
          <div>
            <p class="text-sm font-medium text-gray-900 dark:text-gray-100">{{ tech.full_name }}</p>
            <p class="text-xs text-gray-500 dark:text-gray-400">{{ tech.phone }}</p>
          </div>
        </label>
      </div>

      <div class="mt-6 flex gap-3 justify-end">
        <button
          @click="emit('close')"
          class="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-700
                 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800"
        >
          Cancel
        </button>
        <button
          @click="assign"
          :disabled="!selected || loading"
          class="px-4 py-2 text-sm rounded-lg font-medium bg-brand-600 hover:bg-brand-700
                 text-white disabled:opacity-50 transition"
        >
          {{ loading ? 'Assigning...' : 'Assign' }}
        </button>
      </div>
    </div>
  </div>
</template>
