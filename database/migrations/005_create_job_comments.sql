-- ============================================================
-- Migration: 005_create_job_comments
-- Purpose  : Markdown comments on a job — posted by any
--            authenticated user (admin, dispatcher, or tech).
--            Content is raw markdown, rendered on the frontend.
-- ============================================================

CREATE TABLE IF NOT EXISTS job_comments (
    id         SERIAL PRIMARY KEY,
    job_id     INTEGER      NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    author_id  INTEGER      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content    TEXT         NOT NULL,  -- Raw markdown text
    created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_job_comments_job_id ON job_comments(job_id);
CREATE INDEX IF NOT EXISTS idx_job_comments_author ON job_comments(author_id);
