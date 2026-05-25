import { Router }                from 'express'
import {
  listJobs, getJob, createJob, updateJob, assignTech, deleteJob,
  getComments, addComment, deleteComment,
} from '../controllers/jobs.controller.js'
import { requireAuth, requireAdmin } from '../middleware/auth.js'

const router = Router()

router.get('/',             requireAuth,  listJobs)
router.get('/:id',          requireAuth,  getJob)
router.post('/',            requireAdmin, createJob)
router.patch('/:id',        requireAuth,  updateJob)
router.patch('/:id/assign', requireAdmin, assignTech)
router.delete('/:id',       requireAdmin, deleteJob)

router.get('/:id/comments',         requireAuth, getComments)
router.post('/:id/comments',        requireAuth, addComment)
router.delete('/:id/comments/:cid', requireAuth, deleteComment)

export default router
