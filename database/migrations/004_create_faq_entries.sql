-- ============================================================
-- Migration: 004_create_faq_entries
-- Purpose  : FAQ knowledge base used by the AI voice receptionist
--            to answer common HVAC questions without hallucinating
--            prices, services, or availability.
-- ============================================================

CREATE TABLE IF NOT EXISTS faq_entries (
    id         SERIAL PRIMARY KEY,
    category   VARCHAR(100),
        -- e.g. 'pricing', 'services', 'availability', 'emergency', 'maintenance'
    question   TEXT         NOT NULL,
    answer     TEXT         NOT NULL,
    keywords   TEXT[]       NOT NULL DEFAULT '{}',  -- Match keywords for retrieval
    active     BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- GIN index allows fast keyword array containment queries
CREATE INDEX IF NOT EXISTS idx_faq_category ON faq_entries(category);
CREATE INDEX IF NOT EXISTS idx_faq_keywords ON faq_entries USING GIN(keywords);
CREATE INDEX IF NOT EXISTS idx_faq_active   ON faq_entries(active);
