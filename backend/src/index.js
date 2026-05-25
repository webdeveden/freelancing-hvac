/**
 * index.js — Node.js API server entry point
 *
 * Bootstraps Express, Socket.IO, all REST routes, and the global error handler.
 */

import 'dotenv/config'

import express           from 'express'
import { createServer }  from 'http'
import { Server }        from 'socket.io'
import cors              from 'cors'
import helmet            from 'helmet'
import morgan            from 'morgan'

import errorHandler            from './middleware/errorHandler.js'
import { init as initSocket }  from './services/socket.service.js'
import { registerHandlers }    from './socket/handlers.js'

import authRoutes     from './routes/auth.routes.js'
import jobsRoutes     from './routes/jobs.routes.js'
import dispatchRoutes from './routes/dispatches.routes.js'
import techsRoutes    from './routes/techs.routes.js'
import faqRoutes      from './routes/faq.routes.js'
import internalRoutes from './routes/internal.routes.js'

const PORT = process.env.PORT || 3001

const ALLOWED_ORIGINS = [
  process.env.FRONTEND_URL || 'http://localhost:5173',
  'http://localhost:5173',
]

const corsOptions = {
  origin: (origin, cb) => {
    if (!origin || ALLOWED_ORIGINS.includes(origin)) return cb(null, true)
    cb(new Error(`CORS: origin ${origin} not allowed`))
  },
  credentials: true,
}

// ── Express ────────────────────────────────────────────────────────────────

const app = express()

app.use(helmet())
app.use(cors(corsOptions))
app.use(express.json())
app.use(morgan('dev'))

app.use('/api/auth',       authRoutes)
app.use('/api/jobs',       jobsRoutes)
app.use('/api/dispatches', dispatchRoutes)
app.use('/api/techs',      techsRoutes)
app.use('/api/faq',        faqRoutes)
app.use('/api/internal',   internalRoutes)

app.get('/health', (_req, res) => res.json({ status: 'ok', service: 'hvac-backend' }))

app.use(errorHandler)

// ── Socket.IO ──────────────────────────────────────────────────────────────

const server = createServer(app)

const io = new Server(server, {
  cors: { origin: ALLOWED_ORIGINS, methods: ['GET', 'POST'], credentials: true },
})

initSocket(io)

io.on('connection', (socket) => {
  console.log(`[socket] New connection: ${socket.id}`)
  registerHandlers(socket)
})

// ── Start ──────────────────────────────────────────────────────────────────

server.listen(PORT, () => {
  console.log(`[server] HVAC backend running on port ${PORT}`)
  console.log(`[server] CORS allowed origins: ${ALLOWED_ORIGINS.join(', ')}`)
})
