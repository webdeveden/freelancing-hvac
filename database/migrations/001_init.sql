-- Initial schema — replaces Prisma's generated schema (backend/prisma/schema.prisma).
-- Auto-run by Postgres on first container start (mounted into docker-entrypoint-initdb.d).

CREATE TABLE users (
    id            SERIAL PRIMARY KEY,
    email         VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role          VARCHAR(50)  NOT NULL DEFAULT 'tech',
    full_name     VARCHAR(255) NOT NULL,
    phone         VARCHAR(50),
    is_active     BOOLEAN      NOT NULL DEFAULT true,
    created_at    TIMESTAMP    NOT NULL DEFAULT now(),
    updated_at    TIMESTAMP    NOT NULL DEFAULT now()
);

CREATE TABLE jobs (
    id               SERIAL PRIMARY KEY,
    caller_name      VARCHAR(255),
    caller_phone     VARCHAR(50) NOT NULL,
    service_type     VARCHAR(255),
    description      TEXT,
    address          VARCHAR(255),
    city             VARCHAR(255),
    status           VARCHAR(50) NOT NULL DEFAULT 'pending',
    priority         VARCHAR(50) NOT NULL DEFAULT 'normal',
    assigned_tech_id INTEGER REFERENCES users(id),
    requested_by_id  INTEGER REFERENCES users(id),
    scheduled_at     TIMESTAMP,
    notes            TEXT,
    call_sid         VARCHAR(255),
    created_at       TIMESTAMP NOT NULL DEFAULT now(),
    updated_at       TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE dispatches (
    id             SERIAL PRIMARY KEY,
    job_id         INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    tech_id        INTEGER REFERENCES users(id),
    dispatched_by  INTEGER REFERENCES users(id),
    dispatch_notes TEXT,
    dispatched_at  TIMESTAMP NOT NULL DEFAULT now(),
    status         VARCHAR(50) NOT NULL DEFAULT 'sent',
    created_at     TIMESTAMP NOT NULL DEFAULT now(),
    updated_at     TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE faq_entries (
    id         SERIAL PRIMARY KEY,
    category   VARCHAR(100) NOT NULL DEFAULT 'general',
    question   TEXT NOT NULL,
    answer     TEXT NOT NULL,
    keywords   TEXT[] NOT NULL DEFAULT '{}',
    active     BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE job_comments (
    id         SERIAL PRIMARY KEY,
    job_id     INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    author_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content    TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_assigned_tech_id ON jobs(assigned_tech_id);
CREATE INDEX idx_dispatches_job_id ON dispatches(job_id);
CREATE INDEX idx_job_comments_job_id ON job_comments(job_id);
