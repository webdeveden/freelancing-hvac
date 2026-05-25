/**
 * handlers.js — Socket.IO event handlers
 *
 * Called once per connected socket. Verifies the JWT before admitting
 * the client to the 'dispatchers' room.
 */

import jwt from 'jsonwebtoken'

export function registerHandlers(socket) {
  socket.on('join:dispatchers', ({ token } = {}) => {
    if (!token) {
      socket.emit('error', { message: 'Token required to join dispatchers room' })
      return
    }

    try {
      const user = jwt.verify(token, process.env.JWT_SECRET)
      socket.user = user
      socket.join('dispatchers')
      socket.emit('joined', { room: 'dispatchers', user: { id: user.id, role: user.role } })
      console.log(`[socket] User ${user.id} (${user.role}) joined dispatchers`)
    } catch {
      socket.emit('error', { message: 'Invalid or expired token' })
    }
  })

  socket.on('dispatch:acknowledge', ({ dispatchId } = {}) => {
    if (!socket.user) return
    socket.to('dispatchers').emit('dispatch:acknowledged', {
      dispatchId,
      by: socket.user.id,
    })
  })

  socket.on('disconnect', () => {
    if (socket.user) {
      console.log(`[socket] User ${socket.user.id} disconnected`)
    }
  })
}
