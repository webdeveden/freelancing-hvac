/**
 * socket.service.js — Socket.IO emit helpers
 *
 * Holds a reference to the Socket.IO server instance (set once at startup)
 * and exposes named broadcast functions for each event type.
 * Controllers import these instead of calling io.emit directly.
 */

let io = null

export function init(socketIoServer) {
  io = socketIoServer
}

function getIO() {
  if (!io) throw new Error('Socket.IO has not been initialized — call init() first')
  return io
}

// ── Job events ─────────────────────────────────────────────────────────────

export function emitJobCreated(job) {
  getIO().to('dispatchers').emit('job:created', { job })
}

export function emitJobUpdated(job) {
  getIO().to('dispatchers').emit('job:updated', { job })
}

export function emitJobDeleted(jobId) {
  getIO().to('dispatchers').emit('job:deleted', { jobId })
}

// ── Dispatch events ────────────────────────────────────────────────────────

export function emitDispatchNew(dispatch, job) {
  getIO().to('dispatchers').emit('dispatch:new', { dispatch, job })
}

export function emitDispatchStatus(dispatchId, status) {
  getIO().to('dispatchers').emit('dispatch:status', { dispatchId, status })
}

// ── Emergency alert ────────────────────────────────────────────────────────

export function emitEmergencyAlert(job) {
  getIO().to('dispatchers').emit('emergency:alert', {
    job,
    message: `EMERGENCY: ${job.service_type || 'HVAC Emergency'} at ${job.address}, ${job.city || ''}`.trim(),
  })
}

// ── Comment events ─────────────────────────────────────────────────────────

export function emitCommentAdded(jobId, comment) {
  getIO().to('dispatchers').emit('comment:added', { jobId, comment })
}

export function emitCommentDeleted(jobId, commentId) {
  getIO().to('dispatchers').emit('comment:deleted', { jobId, commentId })
}
