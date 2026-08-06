PRAGMA foreign_keys = ON;

ALTER TABLE research_products
ADD COLUMN asin TEXT;

CREATE INDEX IF NOT EXISTS idx_research_products_asin
    ON research_products (asin);
