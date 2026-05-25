/**
 * errorHandler.js — Global Express error handler
 *
 * Must be registered AFTER all routes (last app.use call).
 * Catches any error passed via next(err) and returns a consistent JSON response.
 */

export default function errorHandler(err, req, res, next) { // eslint-disable-line no-unused-vars
  const status  = err.status || 500
  const message = err.message || 'Internal server error'

  if (process.env.NODE_ENV !== 'production') {
    console.error(`[error] ${req.method} ${req.path} → ${status}:`, err)
  }

  res.status(status).json({ error: message })
}
