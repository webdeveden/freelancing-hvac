-- ============================================================
-- Migration: 001_create_users
-- Purpose  : Stores all system users — admins, dispatchers, techs
-- ============================================================

CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    email         VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,          -- bcrypt hash, never plaintext
    role          VARCHAR(50)  NOT NULL DEFAULT 'tech',
        -- Allowed values: 'admin' | 'dispatcher' | 'tech'
    full_name     VARCHAR(255),
    phone         VARCHAR(50),
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- Speed up lookups by role (e.g. list all technicians)
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
