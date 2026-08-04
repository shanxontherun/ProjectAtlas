-- ==========================================
-- PRODUCT REGISTRY
-- ==========================================

CREATE TABLE IF NOT EXISTS product_registry (

    product_id INTEGER PRIMARY KEY AUTOINCREMENT,

    product_key TEXT NOT NULL UNIQUE,

    product_url TEXT NOT NULL,

    asin TEXT,

    product_name TEXT NOT NULL,

    category TEXT NOT NULL,

    source TEXT NOT NULL DEFAULT 'Amazon',

    status TEXT NOT NULL DEFAULT 'DISCOVERED'
        CHECK (
            status IN (
                'DISCOVERED',
                'CONTENT_READY',
                'PUBLISHED',
                'ARCHIVED'
            )
        ),

    first_seen_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    last_seen_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    last_job_id INTEGER,

    FOREIGN KEY (last_job_id)
        REFERENCES jobs(job_id)
);