PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS pinterest_queue (

    pin_id INTEGER PRIMARY KEY AUTOINCREMENT,

    ai_content_id INTEGER NOT NULL,

    account_id INTEGER NOT NULL,

    board_id INTEGER NOT NULL,

    affiliate_url TEXT,

    image_url TEXT,

    publish_order INTEGER NOT NULL DEFAULT 1,

    status TEXT NOT NULL DEFAULT 'PENDING'
        CHECK (
            status IN (
                'PENDING',
                'READY',
                'PUBLISHED',
                'FAILED',
                'CANCELLED'
            )
        ),

    scheduled_at DATETIME,

    published_at DATETIME,

    retry_count INTEGER NOT NULL DEFAULT 0,

    last_error TEXT,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ai_content_id)
        REFERENCES ai_content(ai_content_id)
        ON DELETE CASCADE,

    FOREIGN KEY (account_id)
        REFERENCES pinterest_accounts(account_id)
        ON DELETE CASCADE,

    FOREIGN KEY (board_id)
        REFERENCES pinterest_boards(board_id)
        ON DELETE CASCADE,

    UNIQUE (
        ai_content_id,
        account_id,
        board_id
    )
);

CREATE INDEX idx_queue_status
ON pinterest_queue(status);

CREATE INDEX idx_queue_scheduled_at
ON pinterest_queue(scheduled_at);

CREATE INDEX idx_queue_ai_content
ON pinterest_queue(ai_content_id);

CREATE INDEX idx_queue_account
ON pinterest_queue(account_id);

CREATE INDEX idx_queue_board
ON pinterest_queue(board_id);