/**
 * db.js — PostgreSQL connection pool
 *
 * All database queries across the app use this shared pool.
 * pg.Pool manages connection reuse and handles reconnects automatically.
 */

import pg from 'pg'
const { Pool } = pg

const pool = new Pool({
  host:     process.env.DB_HOST     || 'localhost',
  port:     parseInt(process.env.DB_PORT || '5432'),
  database: process.env.DB_NAME     || 'hvac_db',
  user:     process.env.DB_USER     || 'hvac_user',
  password: process.env.DB_PASSWORD || 'hvacpassword',
  max: 10,
  idleTimeoutMillis: 30000,
})

pool.on('error', (err) => {
  console.error('[db] Unexpected pool error:', err.message)
})

export default pool
