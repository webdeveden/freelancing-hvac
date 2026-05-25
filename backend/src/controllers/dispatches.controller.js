import prisma       from '../config/prisma.js'
import * as socket  from '../services/socket.service.js'

const DISPATCH_INCLUDE = {
  job:        { select: { caller_name: true, caller_phone: true, service_type: true, address: true, city: true, status: true, priority: true } },
  tech:       { select: { full_name: true } },
  dispatcher: { select: { full_name: true } },
}

function formatDispatch(d) {
  const { job, tech, dispatcher, ...rest } = d
  return {
    ...rest,
    caller_name:        job.caller_name,
    caller_phone:       job.caller_phone,
    service_type:       job.service_type,
    address:            job.address,
    city:               job.city,
    job_status:         job.status,
    job_priority:       job.priority,
    tech_name:          tech?.full_name       ?? null,
    dispatched_by_name: dispatcher?.full_name ?? null,
  }
}

export async function listDispatches(req, res, next) {
  try {
    const { status, tech_id, dispatched_by, page = 1, limit = 20 } = req.query
    const offset = (parseInt(page) - 1) * parseInt(limit)

    const where = {}
    if (status)        where.status        = status
    if (tech_id)       where.tech_id       = parseInt(tech_id)
    if (dispatched_by) where.dispatched_by = parseInt(dispatched_by)

    const [dispatches, total] = await Promise.all([
      prisma.dispatch.findMany({
        where,
        include: DISPATCH_INCLUDE,
        orderBy: { dispatched_at: 'desc' },
        skip:    offset,
        take:    parseInt(limit),
      }),
      prisma.dispatch.count({ where }),
    ])

    res.json({
      dispatches: dispatches.map(formatDispatch),
      total,
      page:  parseInt(page),
      limit: parseInt(limit),
    })
  } catch (err) { next(err) }
}

export async function getDispatch(req, res, next) {
  try {
    const dispatch = await prisma.dispatch.findUnique({
      where:   { id: parseInt(req.params.id) },
      include: DISPATCH_INCLUDE,
    })
    if (!dispatch) return res.status(404).json({ error: 'Dispatch not found' })
    res.json({ dispatch: formatDispatch(dispatch) })
  } catch (err) { next(err) }
}

export async function createDispatch(req, res, next) {
  try {
    const { job_id, tech_id, dispatch_notes } = req.body
    if (!job_id) return res.status(400).json({ error: 'job_id is required' })

    const job = await prisma.job.findUnique({ where: { id: parseInt(job_id) } })
    if (!job) return res.status(404).json({ error: 'Job not found' })

    const created = await prisma.dispatch.create({
      data: {
        job_id:         parseInt(job_id),
        tech_id:        tech_id ? parseInt(tech_id) : null,
        dispatched_by:  req.user.id,
        dispatch_notes: dispatch_notes || null,
      },
      include: DISPATCH_INCLUDE,
    })

    if (tech_id) {
      await prisma.job.update({
        where: { id: parseInt(job_id) },
        data:  { status: 'assigned', assigned_tech_id: parseInt(tech_id) },
      })
    }

    const dispatch = formatDispatch(created)
    socket.emitDispatchNew(dispatch, job)
    res.status(201).json({ dispatch })
  } catch (err) { next(err) }
}

export async function updateDispatchStatus(req, res, next) {
  try {
    const { status } = req.body
    const id = parseInt(req.params.id)

    const allowed = ['sent', 'acknowledged', 'en-route', 'on-site', 'resolved']
    if (!allowed.includes(status)) {
      return res.status(400).json({ error: `status must be one of: ${allowed.join(', ')}` })
    }

    const result = await prisma.dispatch.updateMany({
      where: { id },
      data:  { status },
    })
    if (result.count === 0) return res.status(404).json({ error: 'Dispatch not found' })

    socket.emitDispatchStatus(id, status)
    res.json({ message: 'Status updated', dispatchId: id, status })
  } catch (err) { next(err) }
}
