import prisma        from '../config/prisma.js'
import * as socket   from '../services/socket.service.js'

const JOB_INCLUDE = {
  assigned_tech: { select: { full_name: true, phone: true } },
  requested_by:  { select: { full_name: true } },
}

function formatJob(j) {
  const { assigned_tech, requested_by, ...rest } = j
  return {
    ...rest,
    assigned_tech_name:  assigned_tech?.full_name ?? null,
    assigned_tech_phone: assigned_tech?.phone     ?? null,
    requested_by_name:   requested_by?.full_name  ?? null,
  }
}

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
    tech_name:          tech?.full_name          ?? null,
    dispatched_by_name: dispatcher?.full_name    ?? null,
  }
}

export async function listJobs(req, res, next) {
  try {
    const { status, priority, assigned_tech_id, page = 1, limit = 20 } = req.query
    const offset = (parseInt(page) - 1) * parseInt(limit)

    const where = {}
    if (status)           where.status           = status
    if (priority)         where.priority         = priority
    if (assigned_tech_id) where.assigned_tech_id = parseInt(assigned_tech_id)

    // Techs can only see pending (to claim) and their own jobs
    if (req.user.role === 'tech') {
      if (assigned_tech_id) {
        // Dispatch board: requesting their own jobs — enforce it's their own ID
        where.assigned_tech_id = req.user.id
      } else if (['in-progress', 'completed'].includes(status)) {
        // Jobs list filtered by status: scope to their own
        where.assigned_tech_id = req.user.id
      } else if (status === 'requested') {
        // Tech filters to requested: show only their own requests
        where.requested_by_id = req.user.id
      } else if (!status) {
        // Default view: all pending jobs to claim + tech's own awaiting-approval requests
        where.OR = [
          { status: 'pending' },
          { status: 'requested', requested_by_id: req.user.id },
        ]
      }
    }

    // For summary counts: techs see pending totals + their own in-progress/completed/requested
    const countWhere = req.user.role === 'tech'
      ? { OR: [
          { status: 'pending' },
          { assigned_tech_id: req.user.id },
          { status: 'requested', requested_by_id: req.user.id },
        ]}
      : {}

    const [jobs, total, statusGroups] = await Promise.all([
      prisma.job.findMany({
        where,
        include:  JOB_INCLUDE,
        orderBy:  { created_at: 'desc' },
        skip:     offset,
        take:     parseInt(limit),
      }),
      prisma.job.count({ where }),
      prisma.job.groupBy({ by: ['status'], where: countWhere, _count: { _all: true } }),
    ])

    const statusCounts = {}
    for (const g of statusGroups) statusCounts[g.status] = g._count._all

    res.json({
      jobs:  jobs.map(formatJob),
      total,
      page:  parseInt(page),
      limit: parseInt(limit),
      statusCounts,
    })
  } catch (err) { next(err) }
}

export async function getJob(req, res, next) {
  try {
    const job = await prisma.job.findUnique({
      where:   { id: parseInt(req.params.id) },
      include: JOB_INCLUDE,
    })
    if (!job) return res.status(404).json({ error: 'Job not found' })
    res.json({ job: formatJob(job) })
  } catch (err) { next(err) }
}

export async function createJob(req, res, next) {
  try {
    const { caller_name, caller_phone, service_type, description, address, city,
            status, priority, scheduled_at, notes, call_sid } = req.body

    if (!caller_phone) return res.status(400).json({ error: 'caller_phone is required' })

    const created = await prisma.job.create({
      data: {
        caller_name,
        caller_phone,
        service_type:    service_type    || null,
        description:     description     || null,
        address:         address         || null,
        city:            city            || null,
        status:          status          || 'pending',
        priority:        priority        || 'normal',
        scheduled_at:    scheduled_at    ? new Date(scheduled_at) : null,
        notes:           notes           || null,
        call_sid:        call_sid        || null,
      },
      include: JOB_INCLUDE,
    })

    const job = formatJob(created)
    socket.emitJobCreated(job)
    if (job.priority === 'emergency') socket.emitEmergencyAlert(job)

    res.status(201).json({ job })
  } catch (err) { next(err) }
}

export async function updateJob(req, res, next) {
  try {
    const id      = parseInt(req.params.id)
    const isAdmin = req.user.role === 'admin'

    const allowed = isAdmin
      ? ['status', 'priority', 'service_type', 'description', 'address', 'city',
         'assigned_tech_id', 'scheduled_at', 'notes']
      : ['status']

    const data = {}
    for (const key of allowed) {
      if (req.body[key] !== undefined) {
        data[key] = key === 'assigned_tech_id' ? parseInt(req.body[key])
                  : key === 'scheduled_at'     ? new Date(req.body[key])
                  : req.body[key]
      }
    }

    if (Object.keys(data).length === 0) {
      return res.status(400).json({ error: 'No updatable fields provided' })
    }

    const updated = await prisma.job.update({
      where:   { id },
      data,
      include: JOB_INCLUDE,
    }).catch(e => { if (e.code === 'P2025') return null; throw e })

    if (!updated) return res.status(404).json({ error: 'Job not found' })

    const job = formatJob(updated)
    socket.emitJobUpdated(job)
    res.json({ job })
  } catch (err) { next(err) }
}

export async function assignTech(req, res, next) {
  try {
    const { tech_id } = req.body
    const id = parseInt(req.params.id)

    if (!tech_id) return res.status(400).json({ error: 'tech_id is required' })

    const tech = await prisma.user.findFirst({
      where: { id: parseInt(tech_id), role: 'tech', is_active: true },
    })
    if (!tech) return res.status(404).json({ error: 'Technician not found' })

    const updated = await prisma.job.update({
      where:   { id },
      data:    { assigned_tech_id: parseInt(tech_id), status: 'assigned' },
      include: JOB_INCLUDE,
    }).catch(e => { if (e.code === 'P2025') return null; throw e })

    if (!updated) return res.status(404).json({ error: 'Job not found' })

    const job = formatJob(updated)

    // Upsert dispatch so the tech sees it in My Assignments
    const existing = await prisma.dispatch.findFirst({ where: { job_id: id } })
    if (existing) {
      await prisma.dispatch.update({
        where: { id: existing.id },
        data:  { tech_id: parseInt(tech_id), dispatched_by: req.user.id },
      })
    } else {
      const dispatch = await prisma.dispatch.create({
        data:    { job_id: id, tech_id: parseInt(tech_id), dispatched_by: req.user.id },
        include: DISPATCH_INCLUDE,
      })
      socket.emitDispatchNew(formatDispatch(dispatch), job)
    }

    socket.emitJobUpdated(job)
    res.json({ job })
  } catch (err) { next(err) }
}

export async function deleteJob(req, res, next) {
  try {
    const id = parseInt(req.params.id)
    const result = await prisma.job.deleteMany({ where: { id } })
    if (result.count === 0) return res.status(404).json({ error: 'Job not found' })

    socket.emitJobDeleted(id)
    res.json({ message: 'Job deleted', jobId: id })
  } catch (err) { next(err) }
}

// ── Tech job requests ──────────────────────────────────────────────────────

export async function claimJob(req, res, next) {
  try {
    const id = parseInt(req.params.id)

    const existing = await prisma.job.findUnique({ where: { id }, select: { status: true, requested_by_id: true } })
    if (!existing)                      return res.status(404).json({ error: 'Job not found' })
    if (existing.status !== 'pending')  return res.status(400).json({ error: 'Only pending jobs can be claimed' })
    if (existing.requested_by_id)       return res.status(409).json({ error: 'Job has already been claimed by another tech' })

    const updated = await prisma.job.update({
      where:   { id },
      data:    { status: 'requested', requested_by_id: req.user.id },
      include: JOB_INCLUDE,
    })

    const job = formatJob(updated)
    socket.emitJobRequested(job)
    res.json({ job })
  } catch (err) { next(err) }
}


export async function approveRequest(req, res, next) {
  try {
    const id = parseInt(req.params.id)

    const existing = await prisma.job.findUnique({ where: { id }, select: { status: true, requested_by_id: true } })
    if (!existing)                        return res.status(404).json({ error: 'Job not found' })
    if (existing.status !== 'requested')  return res.status(400).json({ error: 'Job is not in requested status' })

    const updated = await prisma.job.update({
      where:   { id },
      data:    { status: 'assigned', assigned_tech_id: existing.requested_by_id },
      include: JOB_INCLUDE,
    })

    const job = formatJob(updated)

    await prisma.dispatch.create({
      data: { job_id: id, tech_id: existing.requested_by_id, dispatched_by: req.user.id },
    })

    socket.emitJobUpdated(job)
    res.json({ job })
  } catch (err) { next(err) }
}

export async function rejectRequest(req, res, next) {
  try {
    const id = parseInt(req.params.id)

    const existing = await prisma.job.findUnique({ where: { id }, select: { status: true } })
    if (!existing)                        return res.status(404).json({ error: 'Job not found' })
    if (existing.status !== 'requested')  return res.status(400).json({ error: 'Job is not in requested status' })

    const updated = await prisma.job.update({
      where:   { id },
      data:    { status: 'rejected' },
      include: JOB_INCLUDE,
    })

    const job = formatJob(updated)
    socket.emitJobUpdated(job)
    res.json({ job })
  } catch (err) { next(err) }
}

// ── Comments ───────────────────────────────────────────────────────────────

export async function getComments(req, res, next) {
  try {
    const comments = await prisma.jobComment.findMany({
      where:   { job_id: parseInt(req.params.id) },
      include: { author: { select: { full_name: true, role: true } } },
      orderBy: { created_at: 'asc' },
    })

    res.json({
      comments: comments.map(({ author, ...c }) => ({
        ...c,
        author_name: author.full_name,
        author_role: author.role,
      })),
    })
  } catch (err) { next(err) }
}

export async function addComment(req, res, next) {
  try {
    const { content } = req.body
    const jobId = parseInt(req.params.id)

    if (!content || !content.trim()) {
      return res.status(400).json({ error: 'Comment content is required' })
    }

    const jobExists = await prisma.job.findUnique({ where: { id: jobId }, select: { id: true } })
    if (!jobExists) return res.status(404).json({ error: 'Job not found' })

    const created = await prisma.jobComment.create({
      data: { job_id: jobId, author_id: req.user.id, content: content.trim() },
      select: { id: true, created_at: true },
    })

    const comment = {
      id:          created.id,
      job_id:      jobId,
      author_id:   req.user.id,
      author_name: req.user.name,
      author_role: req.user.role,
      content:     content.trim(),
      created_at:  created.created_at,
    }

    socket.emitCommentAdded(jobId, comment)
    res.status(201).json({ comment })
  } catch (err) { next(err) }
}

export async function deleteComment(req, res, next) {
  try {
    const { id: jobId, cid: commentId } = req.params

    const comment = await prisma.jobComment.findFirst({
      where: { id: parseInt(commentId), job_id: parseInt(jobId) },
      select: { author_id: true },
    })
    if (!comment) return res.status(404).json({ error: 'Comment not found' })

    const isOwner = comment.author_id === req.user.id
    if (req.user.role !== 'admin' && !isOwner) {
      return res.status(403).json({ error: "Cannot delete another user's comment" })
    }

    await prisma.jobComment.delete({ where: { id: parseInt(commentId) } })
    socket.emitCommentDeleted(parseInt(jobId), parseInt(commentId))
    res.json({ message: 'Comment deleted', commentId: parseInt(commentId) })
  } catch (err) { next(err) }
}
