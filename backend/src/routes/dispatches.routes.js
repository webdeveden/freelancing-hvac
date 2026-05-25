import { Router }          from 'express'
import {
  listDispatches, getDispatch, createDispatch, updateDispatchStatus,
} from '../controllers/dispatches.controller.js'
import { requireAuth }    from '../middleware/auth.js'

const router = Router()

router.get('/',             requireAuth, listDispatches)
router.get('/:id',          requireAuth, getDispatch)
router.post('/',            requireAuth, createDispatch)
router.patch('/:id/status', requireAuth, updateDispatchStatus)

export default router
