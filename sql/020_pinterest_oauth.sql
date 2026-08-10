PRAGMA foreign_keys = ON;

-- ==========================================
-- ATLAS-029C: REAL PINTEREST OAUTH
-- ==========================================
--
-- Additive schema for the real Pinterest OAuth Authorization Code flow.
-- Every statement is additive; no existing table or row is modified or
-- dropped.
--
--   oauth_states
--       Server-side store for the OAuth `state` parameter (CSRF
--       protection). A cryptographically random state is created when the
--       authorization flow starts and deleted once the callback validates
--       it. Stored here (not in a signed cookie) so validation can reject
--       missing, mismatched and expired state values.
--
--   pinterest_accounts.pinterest_user_id
--       The real Pinterest user ID returned by the authenticated user
--       endpoint. Globally unique on Pinterest; NULL for seed/dev
--       accounts. Lets reconnection find and reuse the existing real
--       account instead of creating duplicates.
--
--   pinterest_boards.pinterest_board_id
--       The real Pinterest board ID returned by the boards endpoint.
--       Globally unique on Pinterest; NULL for seed/dev boards. Lets
--       board sync upsert instead of duplicating on re-sync.
--
--   pinterest_boards.privacy
--       Board privacy reported by Pinterest (PUBLIC / SECRET); NULL for
--       seed/dev boards.
--
-- Seed rows keep NULL for the new columns so real data stays
-- distinguishable from development/test data.

-- --------------------------------------------------
-- OAUTH STATE STORE
-- --------------------------------------------------
CREATE TABLE IF NOT EXISTS oauth_states (
    state TEXT PRIMARY KEY,
    expires_at DATETIME NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_oauth_states_expires_at
    ON oauth_states (expires_at);

-- --------------------------------------------------
-- REAL PINTEREST IDENTITY
-- --------------------------------------------------
ALTER TABLE pinterest_accounts ADD COLUMN pinterest_user_id TEXT;

ALTER TABLE pinterest_boards ADD COLUMN pinterest_board_id TEXT;

ALTER TABLE pinterest_boards ADD COLUMN privacy TEXT;

-- One real Pinterest user -> one Atlas account.
CREATE UNIQUE INDEX IF NOT EXISTS idx_pinterest_accounts_pinterest_user_id
    ON pinterest_accounts (pinterest_user_id)
    WHERE pinterest_user_id IS NOT NULL;

-- One real Pinterest board -> one Atlas board.
CREATE UNIQUE INDEX IF NOT EXISTS idx_pinterest_boards_pinterest_board_id
    ON pinterest_boards (pinterest_board_id)
    WHERE pinterest_board_id IS NOT NULL;
