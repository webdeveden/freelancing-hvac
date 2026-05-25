import { Router }  from 'express'
import prisma       from '../config/prisma.js'
import * as socket  from '../services/socket.service.js'

const router = Router()

router.post('/jobs', async (req, res, next) => {
  try {
    const secret = req.headers['x-internal-secret']
    if (!secret || secret !== process.env.INTERNAL_API_SECRET) {
      return res.status(401).json({ error: 'Unauthorized' })
    }

    const { job_id } = req.body
    if (!job_id) return res.status(400).json({ error: 'job_id is required' })

    const raw = await prisma.job.findUnique({
      where:   { id: parseInt(job_id) },
      include: { assigned_tech: { select: { full_name: true } } },
    })
    if (!raw) return res.status(404).json({ error: 'Job not found' })

    const { assigned_tech, ...rest } = raw
    const job = { ...rest, assigned_tech_name: assigned_tech?.full_name ?? null }

    socket.emitJobCreated(job)
    if (job.priority === 'emergency') socket.emitEmergencyAlert(job)

    res.status(201).json({ job })
  } catch (err) { next(err) }
})

export default router
