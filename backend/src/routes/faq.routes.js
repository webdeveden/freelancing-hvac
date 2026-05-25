import { Router }      from 'express'
import {
  listFAQ, createFAQEntry, updateFAQEntry, deleteFAQEntry,
} from '../controllers/faq.controller.js'
import { requireAuth, requireAdmin } from '../middleware/auth.js'

const router = Router()

router.get('/',      requireAuth,  listFAQ)
router.post('/',     requireAdmin, createFAQEntry)
router.patch('/:id', requireAdmin, updateFAQEntry)
router.delete('/:id', requireAdmin, deleteFAQEntry)

export default router
