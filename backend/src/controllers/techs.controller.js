import prisma from '../config/prisma.js'

export async function listTechs(req, res, next) {
  try {
    const techs = await prisma.user.findMany({
      where:   { role: 'tech', is_active: true },
      select:  { id: true, full_name: true, email: true, phone: true },
      orderBy: { full_name: 'asc' },
    })
    res.json({ techs })
  } catch (err) { next(err) }
}
