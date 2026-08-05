CREATE TABLE IF NOT EXISTS pinterest_boards (

    board_id INTEGER PRIMARY KEY AUTOINCREMENT,

    account_id INTEGER NOT NULL,

    board_name TEXT NOT NULL,

    category_slug TEXT NOT NULL,

    status TEXT NOT NULL DEFAULT 'ACTIVE'
        CHECK (
            status IN (
                'ACTIVE',
                'INACTIVE'
            )
        ),

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (account_id)
        REFERENCES pinterest_accounts(account_id)
        ON DELETE CASCADE
);