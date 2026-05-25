/**
 * jobs.store.js — Jobs list and detail state
 *
 * Handles both REST fetching and real-time Socket.IO updates.
 * Socket.IO events are wired up by useSocket.js composable after this store is used.
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import jobsService from '../services/jobs.service.js'

export const useJobsStore = defineStore('jobs', () => {
  const jobs         = ref([])
  const total        = ref(0)
  const statusCounts = ref({})
  const loading      = ref(false)
  const error        = ref(null)

  // Current filters applied to the list view
  const filters = ref({ status: '', priority: '', page: 1, limit: 20 })

  async function fetchJobs(overrides = {}) {
    loading.value = true
    error.value   = null
    try {
      const params  = { ...filters.value, ...overrides }
      const data         = await jobsService.listJobs(params)
      jobs.value         = data.jobs
      total.value        = data.total
      statusCounts.value = data.statusCounts || {}
      filters.value = { ...filters.value, ...overrides }
    } catch (err) {
      error.value = err.message
    } finally {
      loading.value = false
    }
  }

  async function fetchJob(id) {
    const data = await jobsService.getJob(id)
    return data.job
  }

  async function updateJob(id, payload) {
    const data = await jobsService.updateJob(id, payload)
    _upsertJob(data.job)
    return data.job
  }

  async function assignTech(id, techId) {
    const data = await jobsService.assignTech(id, techId)
    _upsertJob(data.job)
    return data.job
  }

  async function deleteJob(id) {
    await jobsService.deleteJob(id)
    jobs.value = jobs.value.filter(j => j.id !== id)
    total.value = Math.max(0, total.value - 1)
  }

  // ── Socket.IO handlers ────────────────────────────────────────────────────

  function onJobCreated(job) {
    // Prepend to list (newest first)
    if (!jobs.value.find(j => j.id === job.id)) {
      jobs.value.unshift(job)
      total.value++
    }
  }

  function onJobUpdated(job) {
    _upsertJob(job)
  }

  function onJobDeleted(jobId) {
    jobs.value = jobs.value.filter(j => j.id !== jobId)
    total.value = Math.max(0, total.value - 1)
  }

  // ── Internal helpers ──────────────────────────────────────────────────────

  function _upsertJob(job) {
    const idx = jobs.value.findIndex(j => j.id === job.id)
    if (idx >= 0) jobs.value[idx] = job
    else jobs.value.unshift(job)
  }

  return {
    jobs, total, statusCounts, loading, error, filters,
    fetchJobs, fetchJob, updateJob, assignTech, deleteJob,
    onJobCreated, onJobUpdated, onJobDeleted,
  }
})
