<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import AppLayout     from '../components/layout/AppLayout.vue'
import jobsService   from '../services/jobs.service.js'

const router  = useRouter()
const loading = ref(false)
const error   = ref('')

const form = ref({
  caller_name:  '',
  caller_phone: '',
  service_type: '',
  description:  '',
  address:      '',
  city:         '',
  priority:     'normal',
  scheduled_at: '',
  notes:        '',
})

async function submit() {
  error.value = ''
  if (!form.value.caller_phone.trim()) {
    error.value = 'Caller phone is required.'
    return
  }
  loading.value = true
  try {
    const payload = { ...form.value }
    if (!payload.scheduled_at) delete payload.scheduled_at
    const { job } = await jobsService.createJob(payload)
    router.push(`/jobs/${job.id}`)
  } catch (err) {
    error.value = err.response?.data?.error || 'Failed to create job.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AppLayout>
    <div class="max-w-2xl mx-auto">
      <!-- Header -->
      <div class="flex items-center gap-4 mb-6">
        <button
          @click="router.back()"
          class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition"
        >
          <svg class="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
          </svg>
        </button>
        <div>
          <h1 class="text-xl font-bold text-gray-900 dark:text-gray-100">New Job</h1>
          <p class="text-sm text-gray-500 dark:text-gray-400 mt-0.5">Create a new service job</p>
        </div>
      </div>

      <form @submit.prevent="submit" class="bg-white dark:bg-gray-900 rounded-2xl border
            border-gray-200 dark:border-gray-800 shadow-sm p-6 space-y-5">

        <!-- Caller info -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Caller Name
            </label>
            <input
              v-model="form.caller_name"
              type="text"
              placeholder="Jane Smith"
              class="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700
                     bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
                     focus:outline-none focus:ring-2 focus:ring-brand-500 transition"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Caller Phone <span class="text-red-500">*</span>
            </label>
            <input
              v-model="form.caller_phone"
              type="tel"
              placeholder="(555) 123-4567"
              class="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700
                     bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
                     focus:outline-none focus:ring-2 focus:ring-brand-500 transition"
            />
          </div>
        </div>

        <!-- Service type -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Service Type
          </label>
          <input
            v-model="form.service_type"
            type="text"
            placeholder="e.g. AC Repair, Heating, Maintenance"
            class="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700
                   bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
                   focus:outline-none focus:ring-2 focus:ring-brand-500 transition"
          />
        </div>

        <!-- Address -->
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div class="sm:col-span-2">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Address
            </label>
            <input
              v-model="form.address"
              type="text"
              placeholder="123 Main St"
              class="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700
                     bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
                     focus:outline-none focus:ring-2 focus:ring-brand-500 transition"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              City
            </label>
            <input
              v-model="form.city"
              type="text"
              placeholder="Dallas"
              class="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700
                     bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
                     focus:outline-none focus:ring-2 focus:ring-brand-500 transition"
            />
          </div>
        </div>

        <!-- Priority + Scheduled -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Priority
            </label>
            <select
              v-model="form.priority"
              class="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700
                     bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
                     focus:outline-none focus:ring-2 focus:ring-brand-500 transition"
            >
              <option value="normal">Normal</option>
              <option value="high">High</option>
              <option value="emergency">Emergency</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Scheduled At
            </label>
            <input
              v-model="form.scheduled_at"
              type="datetime-local"
              class="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700
                     bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
                     focus:outline-none focus:ring-2 focus:ring-brand-500 transition"
            />
          </div>
        </div>

        <!-- Description -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Description
          </label>
          <textarea
            v-model="form.description"
            rows="3"
            placeholder="Describe the issue..."
            class="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700
                   bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
                   focus:outline-none focus:ring-2 focus:ring-brand-500 transition resize-none"
          />
        </div>

        <!-- Notes -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Internal Notes
          </label>
          <textarea
            v-model="form.notes"
            rows="2"
            placeholder="Any internal notes..."
            class="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700
                   bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100
                   focus:outline-none focus:ring-2 focus:ring-brand-500 transition resize-none"
          />
        </div>

        <p v-if="error" class="text-sm text-red-600 dark:text-red-400">{{ error }}</p>

        <!-- Actions -->
        <div class="flex justify-end gap-3 pt-2">
          <button
            type="button"
            @click="router.back()"
            class="px-4 py-2.5 text-sm rounded-lg border border-gray-300 dark:border-gray-700
                   text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition"
          >
            Cancel
          </button>
          <button
            type="submit"
            :disabled="loading"
            class="px-6 py-2.5 text-sm font-medium rounded-lg bg-brand-600 hover:bg-brand-700
                   text-white disabled:opacity-60 transition"
          >
            {{ loading ? 'Creating...' : 'Create Job' }}
          </button>
        </div>
      </form>
    </div>
  </AppLayout>
</template>
