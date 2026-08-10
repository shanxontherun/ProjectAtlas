PRAGMA foreign_keys = ON;

-- ==========================================
-- ATLAS-029B: ACCOUNTS FOUNDATION
-- ==========================================
--
-- Establishes the Account / Connection / Credential separation that makes
-- Accounts the source of truth for external integrations.
--
--   Account      -> an integration identity (display name, provider)
--   Connection   -> the external connection state for that account
--                   (NOT_CONNECTED / CONNECTING / CONNECTED / ERROR /
--                   DISCONNECTED / NOT_CONFIGURED)
--   Credential   -> server-side only secrets, never serialized to the API
--
-- Pinterest account identity is REUSED from pinterest_accounts (no parallel
-- Pinterest table). Amazon Associates and AI providers can add rows here in
-- future sprints.
--
-- Additive and idempotent: every statement is safe to run more than once.

-- --------------------------------------------------
-- CONNECTIONS
-- --------------------------------------------------
-- One row per integration account. Never store secrets here.
CREATE TABLE IF NOT EXISTS account_connections (

    connection_id INTEGER PRIMARY KEY AUTOINCREMENT,

    provider TEXT NOT NULL
        CHECK (
            provider IN (
                'PINTEREST',
                'AMAZON_ASSOCIATES',
                'AI'
            )
        ),

    display_name TEXT NOT NULL,

    -- Safe display identifier (Pinterest username, etc.). Never a secret.
    username TEXT,

    -- Marketplace for Amazon Associates (e.g. US, UK); NULL for others.
    marketplace TEXT,

    -- Pinterest account identity is reused from pinterest_accounts.
    pinterest_account_id INTEGER
        REFERENCES pinterest_accounts(account_id)
        ON DELETE CASCADE,

    connection_status TEXT NOT NULL DEFAULT 'NOT_CONNECTED'
        CHECK (
            connection_status IN (
                'NOT_CONFIGURED',
                'NOT_CONNECTED',
                'CONNECTING',
                'CONNECTED',
                'ERROR',
                'DISCONNECTED',
                'CONFIGURED'
            )
        ),

    connected_at DATETIME,

    is_seed INTEGER NOT NULL DEFAULT 0,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (provider, pinterest_account_id)
);

CREATE INDEX IF NOT EXISTS idx_account_connections_provider
    ON account_connections (provider);

CREATE INDEX IF NOT EXISTS idx_account_connections_status
    ON account_connections (connection_status);

-- --------------------------------------------------
-- CREDENTIALS (server-side only)
-- --------------------------------------------------
-- Secrets live here and are NEVER returned by the API. Kept separate from
-- safe metadata so accidental SELECT * never leaks a token.
CREATE TABLE IF NOT EXISTS connection_credentials (

    credential_id INTEGER PRIMARY KEY AUTOINCREMENT,

    connection_id INTEGER NOT NULL,

    credential_type TEXT NOT NULL,

    credential_value TEXT NOT NULL,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (connection_id, credential_type),

    FOREIGN KEY (connection_id)
        REFERENCES account_connections(connection_id)
        ON DELETE CASCADE
);

-- --------------------------------------------------
-- SEED: represent every existing Pinterest account as a connection.
-- --------------------------------------------------
-- All existing pinterest_accounts rows are seed/dev accounts (is_seed = 1)
-- or real accounts with no OAuth yet. None is genuinely connected, so every
-- row starts NOT_CONNECTED. is_seed stays separate from connection_status:
-- a non-seed account is NOT automatically connected.
INSERT OR IGNORE INTO account_connections (
    provider,
    display_name,
    username,
    marketplace,
    pinterest_account_id,
    connection_status,
    connected_at,
    is_seed
)
SELECT
    'PINTEREST',
    account_name,
    username,
    NULL,
    account_id,
    'NOT_CONNECTED',
    NULL,
    is_seed
FROM pinterest_accounts;
