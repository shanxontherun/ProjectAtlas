BEGIN TRANSACTION;

-- Create the new table with the updated CHECK constraint
CREATE TABLE research_products_new (
    research_product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    category TEXT NOT NULL,
    product_name TEXT NOT NULL,
    product_url TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'Amazon',
    price REAL,
    currency TEXT NOT NULL DEFAULT 'USD',
    rating REAL,
    review_count INTEGER,
    image_url TEXT,
    ai_summary TEXT,
    status TEXT NOT NULL DEFAULT 'NEW'
        CHECK (
            status IN (
                'NEW',
                'GENERATED',
                'QUEUED',
                'PUBLISHED',
                'FAILED'
            )
        ),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES jobs(job_id)
);

-- Copy all existing data
INSERT INTO research_products_new (
    research_product_id,
    job_id,
    category,
    product_name,
    product_url,
    source,
    price,
    currency,
    rating,
    review_count,
    image_url,
    ai_summary,
    status,
    created_at
)
SELECT
    research_product_id,
    job_id,
    category,
    product_name,
    product_url,
    source,
    price,
    currency,
    rating,
    review_count,
    image_url,
    ai_summary,
    status,
    created_at
FROM research_products;

DROP TABLE research_products;

ALTER TABLE research_products_new
RENAME TO research_products;

COMMIT;