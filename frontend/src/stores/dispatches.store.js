/**
 * dispatches.store.js — Dispatch board state
 *
 * Tracks dispatches and the unread emergency alert count for the bell badge.
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import dispatchesService from '../services/dispatches.service.js'

export const useDispatchesStore = defineStore('dispatches', () => {
  const dispatches   = ref([])
  const total        = ref(0)
  const loading      = ref(false)
  const unreadAlerts = ref(0)   // Badge count for DispatchBell

  async function fetchDispatches(params = {}) {
    loading.value = true
    try {
      const data       = await dispatchesService.listDispatches(params)
      dispatches.value = data.dispatches
      total.value      = data.total
    } finally {
      loading.value = false
    }
  }

  async function updateStatus(id, status) {
    await dispatchesService.updateStatus(id, status)
    const dispatch = dispatches.value.find(d => d.id === id)
    if (dispatch) dispatch.status = status
  }

  // ── Socket.IO handlers ───────────────────────────────────────────────��─

  function onDispatchNew(dispatch) {
    dispatches.value.unshift(dispatch)
    total.value++
    unreadAlerts.value++
  }

  function onDispatchStatus(dispatchId, status) {
    const dispatch = dispatches.value.find(d => d.id === dispatchId)
    if (dispatch) dispatch.status = status
  }

  function onEmergencyAlert() {
    unreadAlerts.value++
  }

  function clearAlerts() {
    unreadAlerts.value = 0
  }

  return {
    dispatches, total, loading, unreadAlerts,
    fetchDispatches, updateStatus,
    onDispatchNew, onDispatchStatus, onEmergencyAlert, clearAlerts,
  }
})
