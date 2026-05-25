<script setup>
import { onMounted, ref }      from 'vue'
import { useDispatchesStore }  from '../stores/dispatches.store.js'
import { useAuthStore }        from '../stores/auth.store.js'
import AppLayout               from '../components/layout/AppLayout.vue'
import DispatchCard            from '../components/dispatch/DispatchCard.vue'
import JobCard                 from '../components/jobs/JobCard.vue'
import LoadingSpinner          from '../components/ui/LoadingSpinner.vue'
import api                     from '../services/api.js'

const dispatches    = useDispatchesStore()
const auth          = useAuthStore()

const isTech        = auth.user?.role === 'tech'
const myJobs        = ref([])
const myJobsLoading = ref(false)

const jobColumns = ['assigned', 'in-progress', 'completed']

function getJobsByStatus(s) {
  return myJobs.value.filter(j => j.status === s)
}

async function loadMyJobs() {
  myJobsLoading.value = true
  try {
    const res = await api.get('/jobs', { params: { assigned_tech_id: auth.user.id, limit: 100 } })
    myJobs.value = res.data.jobs
  } finally {
    myJobsLoading.value = false
  }
}

onMounted(() => {
  if (isTech) {
    loadMyJobs()
  } else {
    dispatches.fetchDispatches()
  }
  dispatches.clearAlerts()
})

async function handleStatusChange({ id, status }) {
  await dispatches.updateStatus(id, status)
}

const columns = ['sent', 'acknowledged', 'en-route', 'on-site', 'resolved']

function getByStatus(s) {
  return dispatches.dispatches.filter(d => d.status === s)
}
</script>

<template>
  <AppLayout>
    <div>
      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-xl font-bold text-gray-900 dark:text-gray-100">Dispatch Board</h1>
          <p class="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
            {{ isTech ? 'Your assigned jobs' : dispatches.total + ' active dispatches — live updates via Socket.IO' }}
          </p>
        </div>
        <div class="flex items-center gap-2 text-xs text-emerald-600 dark:text-emerald-400 font-medium">
          <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"/>
          Live
        </div>
      </div>

      <!-- Tech view: My Assignments -->
      <template v-if="isTech">
        <div v-if="myJobsLoading" class="flex justify-center py-16">
          <LoadingSpinner size="lg" />
        </div>
        <div v-else class="flex divide-x divide-gray-200 dark:divide-gray-700 items-start overflow-x-auto">
          <div v-for="col in jobColumns" :key="col" class="flex-1 min-w-48 px-4 first:pl-0 last:pr-0">
            <div class="flex items-center justify-between mb-3">
              <h2 class="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wide">
                {{ col }}
              </h2>
              <span class="text-xs bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300
                           rounded-full px-2 py-0.5 font-medium">
                {{ getJobsByStatus(col).length }}
              </span>
            </div>
            <div class="space-y-3">
              <JobCard
                v-for="j in getJobsByStatus(col)"
                :key="j.id"
                :job="j"
              />
              <div
                v-if="!getJobsByStatus(col).length"
                class="rounded-xl border-2 border-dashed border-gray-200 dark:border-gray-800
                       p-4 text-center text-xs text-gray-400 dark:text-gray-600"
              >
                No jobs
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- Admin / Dispatcher view: full dispatch kanban -->
      <template v-else>
        <div v-if="dispatches.loading" class="flex justify-center py-16">
          <LoadingSpinner size="lg" />
        </div>
        <div v-else class="flex divide-x divide-gray-200 dark:divide-gray-700 items-start overflow-x-auto">
          <div v-for="col in columns" :key="col" class="flex-1 min-w-48 px-4 first:pl-0 last:pr-0">
            <div class="flex items-center justify-between mb-3">
              <h2 class="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wide">
                {{ col }}
              </h2>
              <span class="text-xs bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300
                           rounded-full px-2 py-0.5 font-medium">
                {{ getByStatus(col).length }}
              </span>
            </div>
            <div class="space-y-3">
              <DispatchCard
                v-for="d in getByStatus(col)"
                :key="d.id"
                :dispatch="d"
                @status-change="handleStatusChange"
              />
              <div
                v-if="!getByStatus(col).length"
                class="rounded-xl border-2 border-dashed border-gray-200 dark:border-gray-800
                       p-4 text-center text-xs text-gray-400 dark:text-gray-600"
              >
                No dispatches
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </AppLayout>
</template>
