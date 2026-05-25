import { Router }                from 'express'
import {
  listJobs, getJob, createJob, updateJob, assignTech, deleteJob,
  claimJob, approveRequest, rejectRequest,
  getComments, addComment, deleteComment,
} from '../controllers/jobs.controller.js'
import { requireAuth, requireAdmin, requireAdminOrDispatcher } from '../middleware/auth.js'

const router = Router()

router.get('/',                      requireAuth,               listJobs)
router.get('/:id',                   requireAuth,               getJob)
router.post('/',                     requireAdmin,              createJob)

router.patch('/:id',                 requireAuth,               updateJob)
router.patch('/:id/assign',          requireAdmin,              assignTech)
router.post('/:id/claim',            requireAuth,               claimJob)
router.patch('/:id/approve',         requireAdminOrDispatcher,  approveRequest)
router.patch('/:id/reject',          requireAdminOrDispatcher,  rejectRequest)
router.delete('/:id',                requireAdmin,              deleteJob)

router.get('/:id/comments',         requireAuth, getComments)
router.post('/:id/comments',        requireAuth, addComment)
router.delete('/:id/comments/:cid', requireAuth, deleteComment)

export default router
