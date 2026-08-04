PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS pinterest_queue (

    pin_id INTEGER PRIMARY KEY AUTOINCREMENT,

    research_product_id INTEGER NOT NULL,

    pinterest_title TEXT,

    pinterest_description TEXT,

    pinterest_keywords TEXT,

    board_name TEXT,

    affiliate_url TEXT,

    image_url TEXT,

    status TEXT NOT NULL DEFAULT 'PENDING'
        CHECK (
            status IN (
                'PENDING',
                'READY',
                'PUBLISHED',
                'FAILED'
            )
        ),

    scheduled_at DATETIME,

    published_at DATETIME,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (research_product_id)
        REFERENCES research_products(research_product_id)
);