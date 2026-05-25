-- ============================================================
-- Migration: 002_create_jobs
-- Purpose  : Central job/work-order table — created by AI voice calls
--            or manually by admin, tracked through to completion
-- ============================================================

CREATE TABLE IF NOT EXISTS jobs (
    id               SERIAL PRIMARY KEY,
    caller_name      VARCHAR(255),
    caller_phone     VARCHAR(50)  NOT NULL,
    service_type     VARCHAR(100),
        -- e.g. 'AC Repair', 'Heating', 'Maintenance', 'Installation', 'Emergency'
    description      TEXT,                        -- AI-summarized or manually entered
    address          TEXT,
    city             VARCHAR(100),
    status           VARCHAR(50)  NOT NULL DEFAULT 'pending',
        -- Allowed: 'pending' | 'assigned' | 'in-progress' | 'completed' | 'cancelled'
    priority         VARCHAR(20)  NOT NULL DEFAULT 'normal',
        -- Allowed: 'normal' | 'high' | 'emergency'
    assigned_tech_id INTEGER      REFERENCES users(id) ON DELETE SET NULL,
    scheduled_at     TIMESTAMPTZ,                 -- Requested appointment time
    notes            TEXT,                        -- Internal dispatcher notes
    call_sid         VARCHAR(100),                -- Twilio CallSid for reference/audit
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_jobs_status     ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_priority   ON jobs(priority);
CREATE INDEX IF NOT EXISTS idx_jobs_created    ON jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_tech       ON jobs(assigned_tech_id);
