<script setup>
import { onMounted, ref, watch } from 'vue'
import { useJobsStore }  from '../stores/jobs.store.js'
import { useAuthStore }  from '../stores/auth.store.js'
import AppLayout         from '../components/layout/AppLayout.vue'
import JobCard           from '../components/jobs/JobCard.vue'
import JobFilters        from '../components/jobs/JobFilters.vue'
import LoadingSpinner    from '../components/ui/LoadingSpinner.vue'

const jobs = useJobsStore()
const auth = useAuthStore()

const filters = ref({ status: '', priority: '' })
const showCreateModal = ref(false)

onMounted(() => jobs.fetchJobs())

function onFilter(f) {
  jobs.fetchJobs({ ...f, page: 1 })
}

function onCardClick(s) {
  filters.value = { ...filters.value, status: filters.value.status === s ? '' : s }
  onFilter(filters.value)
}

// Stats for the summary bar — sourced from backend aggregate, not filtered list
const statuses = ['pending', 'assigned', 'in-progress', 'completed']
function countByStatus(s) {
  return jobs.statusCounts[s] ?? 0
}
</script>

<template>
  <AppLayout>
    <div>
      <!-- Page header -->
      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-xl font-bold text-gray-900 dark:text-gray-100">Jobs</h1>
          <p class="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
            {{ jobs.total }} total jobs
          </p>
        </div>

        <!-- Admin-only: Create Job -->
        <button
          v-if="auth.isAdmin"
          @click="$router.push('/jobs/new')"
          class="flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-700
                 text-white text-sm font-medium rounded-lg transition"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
          </svg>
          New Job
        </button>
      </div>

      <!-- Status summary bar -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
        <div
          v-for="s in statuses"
          :key="s"
          class="bg-white dark:bg-gray-900 rounded-xl border p-4 cursor-pointer transition-colors
                 hover:border-brand-500 dark:hover:border-brand-400"
          :class="s === filters.status
            ? 'border-brand-500 dark:border-brand-400'
            : 'border-gray-200 dark:border-gray-800'"
          @click="onCardClick(s)"
        >
          <p class="text-2xl font-bold text-gray-900 dark:text-gray-100">{{ countByStatus(s) }}</p>
          <p class="text-xs text-gray-500 dark:text-gray-400 capitalize mt-0.5">{{ s }}</p>
        </div>
      </div>

      <!-- Filters -->
      <div class="mb-5">
        <JobFilters v-model="filters" @filter="onFilter" />
      </div>

      <!-- Job grid -->
      <div v-if="jobs.loading" class="flex justify-center py-16">
        <LoadingSpinner size="lg" />
      </div>

      <div
        v-else-if="jobs.jobs.length"
        class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4"
      >
        <JobCard
          v-for="job in jobs.jobs"
          :key="job.id"
          :job="job"
        />
      </div>

      <div v-else class="text-center py-16">
        <p class="text-gray-400 dark:text-gray-600">No jobs found.</p>
        <p v-if="filters.status || filters.priority" class="text-sm text-gray-400 mt-1">
          Try clearing your filters.
        </p>
      </div>
    </div>
  </AppLayout>
</template>
