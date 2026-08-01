PRAGMA foreign_keys = ON;

-- ==========================================
-- RESEARCH PRODUCTS
-- Discovered product candidates linked to a
-- Research department job for review/approval.
-- ==========================================

CREATE TABLE IF NOT EXISTS research_products (
    research_product_id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Owning Research job that discovered this product
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
        CHECK (status IN ('NEW', 'APPROVED', 'REJECTED')),

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (job_id) REFERENCES jobs (job_id)
);

-- Lookup products by category (Research / filtering)
CREATE INDEX IF NOT EXISTS idx_research_products_category
    ON research_products (category);

-- Filter by review status (NEW / APPROVED / REJECTED)
CREATE INDEX IF NOT EXISTS idx_research_products_status
    ON research_products (status);

-- Join / fetch all products for a given job
CREATE INDEX IF NOT EXISTS idx_research_products_job_id
    ON research_products (job_id);
