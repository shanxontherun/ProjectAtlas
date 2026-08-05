CREATE TABLE IF NOT EXISTS pinterest_accounts (

    account_id INTEGER PRIMARY KEY AUTOINCREMENT,

    account_name TEXT NOT NULL,

    username TEXT NOT NULL UNIQUE,

    niche_slug TEXT NOT NULL,

    daily_limit INTEGER NOT NULL DEFAULT 15,

    status TEXT NOT NULL DEFAULT 'ACTIVE'
        CHECK (
            status IN (
                'ACTIVE',
                'INACTIVE'
            )
        ),

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);