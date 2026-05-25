/**
 * Seed Script — run_seeds.js
 *
 * Reads JSON mock data from ../mock/ and inserts into PostgreSQL.
 * Handles bcrypt password hashing for users and resolves index-based
 * references in dispatches (job_index, tech_index, etc.)
 *
 * Usage:
 *   DB_HOST=localhost DB_PORT=5432 DB_NAME=hvac_db \
 *   DB_USER=hvac_user DB_PASSWORD=secret node run_seeds.js
 *
 *   Or with a .env file:
 *   node --env-file=../../backend/.env run_seeds.js
 */

import pg       from 'pg'
import bcrypt   from 'bcryptjs'
import path     from 'path'
import fs       from 'fs'
import { fileURLToPath } from 'url'

const { Pool } = pg

// ESM replacement for __dirname
const __filename = fileURLToPath(import.meta.url)
const __dirname  = path.dirname(__filename)

// ── Helpers ────────────────────────────────────────────────────────────────

function loadJSON(filename) {
  return JSON.parse(
    fs.readFileSync(path.join(__dirname, '../mock', filename), 'utf-8')
  )
}

function log(msg) {
  console.log(`[seed] ${msg}`)
}

// ── Database connection ────────────────────────────────────────────────────

const pool = new Pool({
  host:     process.env.DB_HOST     || 'localhost',
  port:     parseInt(process.env.DB_PORT || '5432'),
  database: process.env.DB_NAME     || 'hvac_db',
  user:     process.env.DB_USER     || 'hvac_user',
  password: process.env.DB_PASSWORD || 'hvacpassword',
})

// ── Seed functions ─────────────────────────────────────────────────────────

async function seedUsers(client) {
  log('Seeding users...')
  const users = loadJSON('users.json')
  const insertedIds = []

  for (const user of users) {
    const hash = await bcrypt.hash(user.password, 10)
    const result = await client.query(
      `INSERT INTO users (email, password_hash, role, full_name, phone)
       VALUES ($1, $2, $3, $4, $5)
       ON CONFLICT (email) DO UPDATE SET
         password_hash = EXCLUDED.password_hash,
         role          = EXCLUDED.role,
         full_name     = EXCLUDED.full_name,
         phone         = EXCLUDED.phone
       RETURNING id`,
      [user.email, hash, user.role, user.full_name, user.phone]
    )
    insertedIds.push(result.rows[0].id)
    log(`  → User "${user.full_name}" (${user.role}) id=${result.rows[0].id}`)
  }

  return insertedIds
}

async function seedJobs(client, userIds) {
  log('Seeding jobs...')
  const jobs    = loadJSON('jobs.json')
  const techIds = userIds.slice(3)  // indices 3-5 are technicians
  const insertedIds = []

  for (let i = 0; i < jobs.length; i++) {
    const job = jobs[i]

    let techId = null
    if (['assigned', 'in-progress', 'completed'].includes(job.status)) {
      techId = techIds[i % techIds.length]
    }

    const result = await client.query(
      `INSERT INTO jobs
         (caller_name, caller_phone, service_type, description, address, city,
          status, priority, assigned_tech_id, scheduled_at, notes, call_sid)
       VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)
       RETURNING id`,
      [
        job.caller_name, job.caller_phone, job.service_type, job.description,
        job.address, job.city, job.status, job.priority,
        techId, job.scheduled_at || null, job.notes || null, job.call_sid || null,
      ]
    )
    insertedIds.push(result.rows[0].id)
    log(`  → Job #${result.rows[0].id} "${job.service_type}" [${job.priority}/${job.status}]`)
  }

  return insertedIds
}

async function seedDispatches(client, jobIds, userIds) {
  log('Seeding dispatches...')
  const dispatches = loadJSON('dispatches.json')
  const techIds    = userIds.slice(3)

  for (const d of dispatches) {
    const jobId          = jobIds[d.job_index]
    const techId         = techIds[d.tech_index - 3] || techIds[0]
    const dispatchedById = userIds[d.dispatched_by_index]

    if (!jobId) {
      log(`  ! Skipping dispatch — job_index ${d.job_index} out of range`)
      continue
    }

    await client.query(
      `INSERT INTO dispatches (job_id, tech_id, dispatched_by, dispatch_notes, status)
       VALUES ($1,$2,$3,$4,$5)`,
      [jobId, techId, dispatchedById, d.dispatch_notes, d.status]
    )
    log(`  → Dispatch job #${jobId} → tech #${techId} [${d.status}]`)
  }
}

async function seedFAQ(client) {
  log('Seeding FAQ entries...')
  const faqs = loadJSON('faq_entries.json')

  for (const faq of faqs) {
    await client.query(
      `INSERT INTO faq_entries (category, question, answer, keywords)
       VALUES ($1, $2, $3, $4)`,
      [faq.category, faq.question, faq.answer, faq.keywords]
    )
    log(`  → FAQ [${faq.category}] "${faq.question.substring(0, 50)}..."`)
  }
}

async function seedComments(client, jobIds, userIds) {
  log('Seeding sample comments...')
  const adminId    = userIds[0]
  const dispatchId = userIds[1]

  const comments = [
    { jobIdx: 1, authorId: adminId,    content: '**Emergency flagged** — caller confirmed no heat for 6+ hours. Family with infant. Bumped to top of queue.' },
    { jobIdx: 1, authorId: dispatchId, content: 'Called Mike at 8:15 AM. ETA 45 minutes. Client notified via text.' },
    { jobIdx: 4, authorId: dispatchId, content: '**Note:** Derek reports burning smell from wiring harness. May need full motor replacement. Will update with parts estimate.' },
    { jobIdx: 4, authorId: adminId,    content: 'Approved up to $800 for repairs without additional authorization. Call if it exceeds that.' },
    { jobIdx: 2, authorId: dispatchId, content: 'Carlos is a service plan member — no charge for this visit. Mark the plan contract number: `SVC-2024-0882`.' },
    { jobIdx: 8, authorId: adminId,    content: 'Install completed on schedule.\n\n- Equipment: Carrier 5-ton split system\n- Permit: pulled and approved\n- Warranty registered: **10-year parts, 5-year labor**' },
  ]

  for (const c of comments) {
    const jobId = jobIds[c.jobIdx]
    if (!jobId) continue
    await client.query(
      `INSERT INTO job_comments (job_id, author_id, content) VALUES ($1,$2,$3)`,
      [jobId, c.authorId, c.content]
    )
    log(`  → Comment on job #${jobId} by user #${c.authorId}`)
  }
}

// ── Main ───────────────────────────────────────────────────────────────────

async function main() {
  const client = await pool.connect()
  try {
    log('Starting seed transaction...')
    await client.query('BEGIN')

    await client.query('DELETE FROM job_comments')
    await client.query('DELETE FROM dispatches')
    await client.query('DELETE FROM jobs')
    await client.query('DELETE FROM faq_entries')
    await client.query('DELETE FROM users')
    log('Cleared existing seed data.')

    const userIds = await seedUsers(client)
    const jobIds  = await seedJobs(client, userIds)
    await seedDispatches(client, jobIds, userIds)
    await seedFAQ(client)
    await seedComments(client, jobIds, userIds)

    await client.query('COMMIT')
    log('✓ Seed completed successfully.')
  } catch (err) {
    await client.query('ROLLBACK')
    console.error('[seed] ERROR — rolled back:', err.message)
    process.exit(1)
  } finally {
    client.release()
    await pool.end()
  }
}

main()
