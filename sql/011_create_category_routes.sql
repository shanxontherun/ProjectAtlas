PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS category_routes (

    route_id INTEGER PRIMARY KEY AUTOINCREMENT,

    category_slug TEXT NOT NULL,

    account_id INTEGER NOT NULL,

    board_id INTEGER NOT NULL,

    priority INTEGER NOT NULL DEFAULT 1,

    status TEXT NOT NULL DEFAULT 'ACTIVE'
        CHECK (
            status IN (
                'ACTIVE',
                'INACTIVE'
            )
        ),

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (
        category_slug,
        account_id,
        board_id
    ),

    FOREIGN KEY (account_id)
        REFERENCES pinterest_accounts(account_id)
        ON DELETE CASCADE,

    FOREIGN KEY (board_id)
        REFERENCES pinterest_boards(board_id)
        ON DELETE CASCADE
);

CREATE INDEX idx_category_routes_slug
ON category_routes(category_slug);

CREATE INDEX idx_category_routes_priority
ON category_routes(priority);