-- RapidRelief database schema.
--
-- NOTE FOR REVIEWERS: last_name and address are marked NOT NULL below.
-- This is a real schema-level assumption that contradicts POLICY.md
-- REQ-1 (surname optional) and REQ-2 (address optional). It is used by
-- Assumption Zero's database_agent.py as ground-truth evidence.

CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT,                       -- REPAIRED: surname optional (REQ-1)
    address TEXT,                         -- REPAIRED: address optional (REQ-2)
    phone TEXT NOT NULL,
    household_size INTEGER NOT NULL DEFAULT 1,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'submitted',
    idempotency_key TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_applications_idempotency
    ON applications (idempotency_key);
