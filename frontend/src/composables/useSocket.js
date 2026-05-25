/**
 * useSocket.js — Socket.IO singleton composable
 *
 * Creates one socket connection for the lifetime of the app.
 * Wires all server events to the appropriate Pinia store handlers.
 * Also manages the toast notification for emergencies.
 *
 * Call useSocket() once in App.vue or a top-level authenticated layout.
 */

import { ref, onUnmounted } from 'vue'
import { io }               from 'socket.io-client'
import { useJobsStore }      from '../stores/jobs.store.js'
import { useDispatchesStore } from '../stores/dispatches.store.js'

let socket = null   // Singleton socket instance

export function useSocket() {
  const jobsStore      = useJobsStore()
  const dispatchesStore = useDispatchesStore()

  // Toast state — components can watch this to show notifications
  const toast = ref(null) // { type, message, job } | null

  function connect() {
    if (socket?.connected) return

    const token = localStorage.getItem('hvac-token')
    if (!token) return

    socket = io(import.meta.env.VITE_SOCKET_URL || 'http://localhost:3001', {
      transports: ['websocket'],
    })

    socket.on('connect', () => {
      console.log('[socket] Connected:', socket.id)
      // Authenticate and join the dispatchers room
      socket.emit('join:dispatchers', { token })
    })

    socket.on('disconnect', () => {
      console.log('[socket] Disconnected')
    })

    // ── Job events ─────────────────────────────────────────────────────────
    socket.on('job:created', ({ job }) => {
      jobsStore.onJobCreated(job)
      toast.value = { type: 'info', message: `New job: ${job.service_type || 'Service Request'} — ${job.caller_name || job.caller_phone}`, job }
      setTimeout(() => { toast.value = null }, 5000)
    })

    socket.on('job:updated', ({ job }) => {
      jobsStore.onJobUpdated(job)
    })

    socket.on('job:requested', ({ job }) => {
      jobsStore.onJobUpdated(job)
      dispatchesStore.onJobRequested()
      toast.value = {
        type: 'request',
        message: `Job request: ${job.requested_by_name || 'A tech'} wants Job #${job.id} — ${job.service_type || 'Service Request'}`,
        job,
      }
      setTimeout(() => { toast.value = null }, 6000)
    })

    socket.on('job:deleted', ({ jobId }) => {
      jobsStore.onJobDeleted(jobId)
    })

    // ── Dispatch events ────────────────────────────────────────────────────
    socket.on('dispatch:new', ({ dispatch, job }) => {
      dispatchesStore.onDispatchNew(dispatch)
      toast.value = { type: 'dispatch', message: `Dispatch sent for job #${job?.id}`, job }
      setTimeout(() => { toast.value = null }, 5000)
    })

    socket.on('dispatch:status', ({ dispatchId, status }) => {
      dispatchesStore.onDispatchStatus(dispatchId, status)
    })

    // ── Emergency alert ────────────────────────────────────────────────────
    socket.on('emergency:alert', ({ job, message }) => {
      dispatchesStore.onEmergencyAlert()
      // Emergency toasts persist until manually dismissed
      toast.value = { type: 'emergency', message, job, persistent: true }
      _playAlertSound()
    })
  }

  function disconnect() {
    socket?.disconnect()
    socket = null
  }

  function dismissToast() {
    toast.value = null
  }

  onUnmounted(() => {
    // Don't disconnect on unmount — socket is a singleton across nav
  })

  return { connect, disconnect, toast, dismissToast }
}

// ── Alert sound via Web Audio API ─────────────────────────────────────────

function _playAlertSound() {
  try {
    const ctx = new AudioContext()
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.connect(gain)
    gain.connect(ctx.destination)
    osc.type = 'sine'
    osc.frequency.value = 880
    gain.gain.setValueAtTime(0.3, ctx.currentTime)
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.8)
    osc.start(ctx.currentTime)
    osc.stop(ctx.currentTime + 0.8)
  } catch { /* Web Audio not available */ }
}
