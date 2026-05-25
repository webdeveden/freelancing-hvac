-- ============================================================
-- Migration: 003_create_dispatches
-- Purpose  : Dispatch records — created when admin sends a tech
--            to a job. Triggers real-time Socket.IO notification.
-- ============================================================

CREATE TABLE IF NOT EXISTS dispatches (
    id              SERIAL PRIMARY KEY,
    job_id          INTEGER      NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    tech_id         INTEGER      REFERENCES users(id) ON DELETE SET NULL,
    dispatched_by   INTEGER      REFERENCES users(id) ON DELETE SET NULL,
    dispatch_notes  TEXT,
    dispatched_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    status          VARCHAR(50)  NOT NULL DEFAULT 'sent',
        -- Allowed: 'sent' | 'acknowledged' | 'en-route' | 'on-site' | 'resolved'
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_dispatches_job_id ON dispatches(job_id);
CREATE INDEX IF NOT EXISTS idx_dispatches_status ON dispatches(status);
CREATE INDEX IF NOT EXISTS idx_dispatches_tech   ON dispatches(tech_id);
