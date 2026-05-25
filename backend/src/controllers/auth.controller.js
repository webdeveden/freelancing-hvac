import bcrypt from 'bcryptjs'
import jwt    from 'jsonwebtoken'
import prisma from '../config/prisma.js'

export async function login(req, res, next) {
  try {
    const { email, password } = req.body
    if (!email || !password) {
      return res.status(400).json({ error: 'Email and password are required' })
    }

    const user = await prisma.user.findFirst({
      where: { email: email.trim().toLowerCase(), is_active: true },
      select: { id: true, email: true, password_hash: true, role: true, full_name: true },
    })

    if (!user) return res.status(401).json({ error: 'Invalid credentials' })

    const passwordMatch = await bcrypt.compare(password, user.password_hash)
    if (!passwordMatch) return res.status(401).json({ error: 'Invalid credentials' })

    const token = jwt.sign(
      { id: user.id, email: user.email, role: user.role, name: user.full_name },
      process.env.JWT_SECRET,
      { expiresIn: process.env.JWT_EXPIRES_IN || '8h' }
    )

    res.json({
      token,
      user: { id: user.id, email: user.email, role: user.role, name: user.full_name },
    })
  } catch (err) { next(err) }
}

export async function register(req, res, next) {
  try {
    const { full_name, email, password, role } = req.body
    if (!full_name || !email || !password) {
      return res.status(400).json({ error: 'full_name, email, and password are required' })
    }

    const userRole = ['dispatcher', 'tech'].includes(role) ? role : 'dispatcher'
    const normalizedEmail = email.trim().toLowerCase()

    const existing = await prisma.user.findUnique({ where: { email: normalizedEmail } })
    if (existing) return res.status(409).json({ error: 'An account with that email already exists' })

    const hash = await bcrypt.hash(password, 10)
    const user = await prisma.user.create({
      data: { full_name: full_name.trim(), email: normalizedEmail, password_hash: hash, role: userRole },
      select: { id: true, email: true, role: true, full_name: true },
    })

    const token = jwt.sign(
      { id: user.id, email: user.email, role: user.role, name: user.full_name },
      process.env.JWT_SECRET,
      { expiresIn: process.env.JWT_EXPIRES_IN || '8h' }
    )

    res.status(201).json({ token, user: { id: user.id, email: user.email, role: user.role, name: user.full_name } })
  } catch (err) { next(err) }
}

export async function getMe(req, res, next) {
  try {
    const user = await prisma.user.findUnique({
      where: { id: req.user.id },
      select: { id: true, email: true, role: true, full_name: true, phone: true },
    })
    if (!user) return res.status(404).json({ error: 'User not found' })
    res.json({ user })
  } catch (err) { next(err) }
}
