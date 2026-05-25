import prisma from '../config/prisma.js'

export async function listFAQ(req, res, next) {
  try {
    const { category, active } = req.query

    const where = {}
    if (category)          where.category = category
    if (active !== undefined) where.active = active === 'true'

    const faq = await prisma.faqEntry.findMany({
      where,
      orderBy: [{ category: 'asc' }, { id: 'asc' }],
    })
    res.json({ faq })
  } catch (err) { next(err) }
}

export async function createFAQEntry(req, res, next) {
  try {
    const { category, question, answer, keywords } = req.body
    if (!question || !answer) return res.status(400).json({ error: 'question and answer are required' })

    const entry = await prisma.faqEntry.create({
      data: { category: category || 'general', question, answer, keywords: keywords || [] },
    })
    res.status(201).json({ entry })
  } catch (err) { next(err) }
}

export async function updateFAQEntry(req, res, next) {
  try {
    const { category, question, answer, keywords, active } = req.body
    const id = parseInt(req.params.id)

    const data = {}
    if (category !== undefined) data.category = category
    if (question !== undefined) data.question = question
    if (answer   !== undefined) data.answer   = answer
    if (keywords !== undefined) data.keywords = keywords
    if (active   !== undefined) data.active   = active

    if (Object.keys(data).length === 0) return res.status(400).json({ error: 'No fields to update' })

    const entry = await prisma.faqEntry.update({ where: { id }, data })
      .catch(e => { if (e.code === 'P2025') return null; throw e })

    if (!entry) return res.status(404).json({ error: 'FAQ entry not found' })
    res.json({ entry })
  } catch (err) { next(err) }
}

export async function deleteFAQEntry(req, res, next) {
  try {
    const id = parseInt(req.params.id)
    const result = await prisma.faqEntry.deleteMany({ where: { id } })
    if (result.count === 0) return res.status(404).json({ error: 'FAQ entry not found' })
    res.json({ message: 'FAQ entry deleted', id })
  } catch (err) { next(err) }
}
