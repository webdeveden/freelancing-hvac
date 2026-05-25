<script setup>
/**
 * JobDetailView.vue — Full job detail page
 *
 * Role-based actions:
 *   Admin    : Edit details, Assign tech, Delete
 *   All users: Update status (pending / in-progress / complete)
 *   All users: Post / delete own comments (admin deletes any)
 */
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore }       from '../stores/auth.store.js'
import jobsService            from '../services/jobs.service.js'
import AppLayout              from '../components/layout/AppLayout.vue'
import JobStatusBadge         from '../components/jobs/JobStatusBadge.vue'
import AssignTechModal        from '../components/jobs/AssignTechModal.vue'
import JobComments            from '../components/jobs/JobComments.vue'
import ConfirmDialog          from '../components/ui/ConfirmDialog.vue'
import LoadingSpinner         from '../components/ui/LoadingSpinner.vue'

const route  = useRoute()
const router = useRouter()
const auth   = useAuthStore()

const job          = ref(null)
const loading      = ref(true)
const error        = ref(null)
const showAssign   = ref(false)
const showDelete   = ref(false)
const statusLoading = ref(false)

onMounted(async () => {
  try {
    const data = await jobsService.getJob(route.params.id)
    job.value  = data.job
  } catch {
    error.value = 'Job not found or you do not have access.'
  } finally {
    loading.value = false
  }
})

async function updateStatus(status) {
  if (!job.value) return
  statusLoading.value = true
  try {
    const data = await jobsService.updateJob(job.value.id, { status })
    job.value  = data.job
  } finally {
    statusLoading.value = false
  }
}

async function confirmDelete() {
  await jobsService.deleteJob(job.value.id)
  router.push('/jobs')
}

function onAssigned(updatedJob) {
  job.value   = updatedJob
  showAssign.value = false
}

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('en-US', {
    weekday: 'short', month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}
</script>

<template>
  <AppLayout>
    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-16">
      <LoadingSpinner size="lg" />
    </div>

    <!-- Error -->
    <div v-else-if="error" class="text-center py-16">
      <p class="text-gray-500 dark:text-gray-400">{{ error }}</p>
      <button @click="router.push('/jobs')" class="mt-4 text-brand-600 hover:underline text-sm">
        ← Back to jobs
      </button>
    </div>

    <!-- Job detail -->
    <div v-else-if="job">
      <!-- Back + breadcrumb -->
      <button
        @click="router.push('/jobs')"
        class="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-800 dark:hover:text-gray-200 mb-5 transition"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
        </svg>
        All Jobs
      </button>

      <!-- Header card -->
      <div class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-6 mb-6">
        <div class="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 class="text-xl font-bold text-gray-900 dark:text-gray-100">
              {{ job.service_type || 'Service Request' }}
            </h1>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">Job #{{ job.id }}</p>
          </div>

          <!-- Status badges -->
          <JobStatusBadge :status="job.status" :priority="job.priority" />
        </div>

        <!-- Status update buttons (all users) -->
        <div class="mt-5 flex flex-wrap gap-2">
          <p class="text-xs font-medium text-gray-500 dark:text-gray-400 w-full">Update Status:</p>
          <button
            v-for="s in ['pending', 'in-progress', 'completed']"
            :key="s"
            @click="updateStatus(s)"
            :disabled="job.status === s || statusLoading"
            class="px-3 py-1.5 text-xs font-medium rounded-lg border transition capitalize disabled:opacity-40 disabled:cursor-not-allowed"
            :class="job.status === s
              ? 'bg-gray-100 dark:bg-gray-800 border-gray-300 dark:border-gray-700 text-gray-600 dark:text-gray-400'
              : 'border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800'"
          >
            {{ s }}
          </button>
        </div>

        <!-- Admin-only actions -->
        <div v-if="auth.isAdmin" class="mt-4 flex flex-wrap gap-2 pt-4 border-t border-gray-100 dark:border-gray-800">
          <button
            @click="showAssign = true"
            class="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-lg
                   bg-brand-50 dark:bg-brand-950 text-brand-700 dark:text-brand-400
                   hover:bg-brand-100 dark:hover:bg-brand-900 transition"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
            </svg>
            Assign Tech
          </button>

          <button
            @click="showDelete = true"
            class="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-lg
                   bg-red-50 dark:bg-red-950 text-red-700 dark:text-red-400
                   hover:bg-red-100 dark:hover:bg-red-900 transition"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
            </svg>
            Delete Job
          </button>
        </div>
      </div>

      <!-- Details grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <!-- Caller info -->
        <div class="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-5">
          <h3 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3">Caller</h3>
          <dl class="space-y-2 text-sm">
            <div class="flex justify-between">
              <dt class="text-gray-500 dark:text-gray-400">Name</dt>
              <dd class="font-medium text-gray-900 dark:text-gray-100">{{ job.caller_name || '—' }}</dd>
            </div>
            <div class="flex justify-between">
              <dt class="text-gray-500 dark:text-gray-400">Phone</dt>
              <dd class="font-medium text-gray-900 dark:text-gray-100">{{ job.caller_phone }}</dd>
            </div>
          </dl>
        </div>

        <!-- Job info -->
        <div class="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-5">
          <h3 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3">Location</h3>
          <dl class="space-y-2 text-sm">
            <div class="flex justify-between">
              <dt class="text-gray-500 dark:text-gray-400">Address</dt>
              <dd class="font-medium text-right">
                <a
                  v-if="job.address"
                  :href="`https://maps.google.com/maps?q=${encodeURIComponent(job.address + (job.city ? ', ' + job.city : ''))}`"
                  target="_blank"
                  rel="noopener"
                  class="text-brand-600 dark:text-brand-400 hover:underline"
                >
                  {{ job.address }}<span v-if="job.city">, {{ job.city }}</span>
                </a>
                <span v-else class="text-gray-900 dark:text-gray-100">—</span>
              </dd>
            </div>
            <div class="flex justify-between">
              <dt class="text-gray-500 dark:text-gray-400">City</dt>
              <dd class="font-medium text-gray-900 dark:text-gray-100">{{ job.city || '—' }}</dd>
            </div>
          </dl>
        </div>

        <!-- Scheduling -->
        <div class="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-5">
          <h3 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3">Scheduling</h3>
          <dl class="space-y-2 text-sm">
            <div class="flex justify-between">
              <dt class="text-gray-500 dark:text-gray-400">Scheduled</dt>
              <dd class="font-medium text-gray-900 dark:text-gray-100">{{ formatDate(job.scheduled_at) }}</dd>
            </div>
            <div class="flex justify-between">
              <dt class="text-gray-500 dark:text-gray-400">Created</dt>
              <dd class="font-medium text-gray-900 dark:text-gray-100">{{ formatDate(job.created_at) }}</dd>
            </div>
            <div class="flex justify-between">
              <dt class="text-gray-500 dark:text-gray-400">Assigned Tech</dt>
              <dd class="font-medium text-gray-900 dark:text-gray-100">{{ job.assigned_tech_name || 'Unassigned' }}</dd>
            </div>
          </dl>
        </div>

        <!-- Description -->
        <div class="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-5">
          <h3 class="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3">Description</h3>
          <p class="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
            {{ job.description || 'No description provided.' }}
          </p>
          <div v-if="job.notes" class="mt-3 pt-3 border-t border-gray-100 dark:border-gray-800">
            <p class="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Internal Notes</p>
            <p class="text-sm text-gray-600 dark:text-gray-400 italic">{{ job.notes }}</p>
          </div>
        </div>
      </div>

      <!-- Markdown comments section -->
      <div class="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-6">
        <JobComments :job-id="job.id" />
      </div>
    </div>

    <!-- Modals -->
    <AssignTechModal
      v-if="showAssign"
      :job-id="job.id"
      @assigned="onAssigned"
      @close="showAssign = false"
    />

    <ConfirmDialog
      v-if="showDelete"
      title="Delete Job"
      :message="`Are you sure you want to permanently delete Job #${job?.id}? This cannot be undone.`"
      :danger="true"
      @confirm="confirmDelete"
      @cancel="showDelete = false"
    />
  </AppLayout>
</template>
