import { Router }    from 'express'
import { listTechs } from '../controllers/techs.controller.js'
import { requireAuth } from '../middleware/auth.js'

const router = Router()

router.get('/', requireAuth, listTechs)

export default router
