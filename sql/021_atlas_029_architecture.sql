PRAGMA foreign_keys = ON;

-- ==========================================
-- ATLAS-029 NEXT PHASE: ARCHITECTURE / SCHEMA
-- ==========================================
--
-- Additive schema for the 029 NEXT PHASE work. No existing table, row,
-- column or value is modified or dropped; every statement only adds.
--
--   1) Categories become frontend-managed entities wired to Pinterest
--      accounts and boards through category_routes (by FK, not by
--      free-text slug).
--   2) Products become provider-agnostic: provider / marketplace /
--      external_product_id / affiliate_url on both research_products
--      and product_registry.
--   3) Affiliate configuration stays on account_connections /
--      connection_credentials (provider AMAZON_ASSOCIATES); this
--      migration only documents that contract, no new table is needed.
--   4) Export-ready concept: pinterest_queue.exported_at records when a
--      pin was manually exported (download + copy). PUBLISHED still means
--      a real Pinterest publish only.

-- --------------------------------------------------
-- 1) CATEGORIES <-> ACCOUNTS <-> BOARDS WIRING
-- --------------------------------------------------
-- Add a stable slug to categories so legacy category_routes.category_slug
-- rows can be linked to real category rows by FK.
ALTER TABLE categories ADD COLUMN category_slug TEXT;

-- Backfill the two seed categories with their canonical slugs.
UPDATE categories
SET category_slug = 'kitchen'
WHERE category_name = 'Kitchen Storage';

UPDATE categories
SET category_slug = 'home'
WHERE category_name = 'Home Storage';

-- One slug per category; NULL allowed for future rows awaiting a slug.
CREATE UNIQUE INDEX IF NOT EXISTS idx_categories_category_slug
    ON categories (category_slug)
    WHERE category_slug IS NOT NULL;

-- Seed categories for every known legacy route slug so existing routes
-- resolve to a real categories row. INSERT OR IGNORE keeps this safe to
-- re-run.
INSERT OR IGNORE INTO categories (
    category_name,
    category_slug,
    priority,
    status,
    daily_target
)
VALUES
    ('Pantry', 'pantry', 8, 'ACTIVE', 5),
    ('Bathroom', 'bathroom', 8, 'ACTIVE', 5),
    ('Closet', 'closet', 8, 'ACTIVE', 5);

-- Wire category_routes to the categories table. The legacy category_slug
-- column stays (the current queue path still reads it), but the FK is now
-- the authoritative relationship.
ALTER TABLE category_routes ADD COLUMN category_id INTEGER
    REFERENCES categories (category_id)
    ON DELETE CASCADE;

UPDATE category_routes
SET category_id = (
    SELECT categories.category_id
    FROM categories
    WHERE categories.category_slug = category_routes.category_slug
)
WHERE category_id IS NULL;

-- Generic fallback: any legacy route whose slug has no matching category
-- gets one created (slug becomes the display name until renamed in the
-- UI), so no existing route is ever left without a category FK.
INSERT OR IGNORE INTO categories (
    category_name,
    category_slug,
    priority,
    status,
    daily_target
)
SELECT
    upper(substr(replace(orphan.slug, '_', ' '), 1, 1))
        || substr(replace(orphan.slug, '_', ' '), 2),
    orphan.slug,
    5,
    'ACTIVE',
    5
FROM (
    SELECT DISTINCT category_slug AS slug
    FROM category_routes
    WHERE category_id IS NULL
      AND category_slug IS NOT NULL
) AS orphan
WHERE NOT EXISTS (
    SELECT 1
    FROM categories
    WHERE categories.category_slug = orphan.slug
);

UPDATE category_routes
SET category_id = (
    SELECT categories.category_id
    FROM categories
    WHERE categories.category_slug = category_routes.category_slug
)
WHERE category_id IS NULL;

CREATE INDEX IF NOT EXISTS idx_category_routes_category_id
    ON category_routes (category_id);

-- --------------------------------------------------
-- 2) PROVIDER-AGNOSTIC PRODUCT MODEL
-- --------------------------------------------------
-- A product now declares WHERE it came from (provider / marketplace) and
-- the provider's own identifier (external_product_id, e.g. an Amazon
-- ASIN) independently of the Atlas-internal columns. affiliate_url is
-- NULL unless a real affiliate URL exists; nothing is ever invented.
ALTER TABLE research_products ADD COLUMN provider TEXT NOT NULL DEFAULT 'AMAZON';
ALTER TABLE research_products ADD COLUMN marketplace TEXT NOT NULL DEFAULT 'US';
ALTER TABLE research_products ADD COLUMN external_product_id TEXT;
ALTER TABLE research_products ADD COLUMN affiliate_url TEXT;

UPDATE research_products
SET external_product_id = asin
WHERE external_product_id IS NULL
  AND asin IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_research_products_provider
    ON research_products (provider);

CREATE INDEX IF NOT EXISTS idx_research_products_external_id
    ON research_products (external_product_id);

ALTER TABLE product_registry ADD COLUMN provider TEXT NOT NULL DEFAULT 'AMAZON';
ALTER TABLE product_registry ADD COLUMN marketplace TEXT NOT NULL DEFAULT 'US';
ALTER TABLE product_registry ADD COLUMN external_product_id TEXT;
ALTER TABLE product_registry ADD COLUMN affiliate_url TEXT;

UPDATE product_registry
SET external_product_id = asin
WHERE external_product_id IS NULL
  AND asin IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_product_registry_provider
    ON product_registry (provider);

CREATE INDEX IF NOT EXISTS idx_product_registry_external_id
    ON product_registry (external_product_id);

-- --------------------------------------------------
-- 3) AFFILIATE CONFIGURATION
-- --------------------------------------------------
-- The Amazon Associates affiliate configuration (associate tag / API
-- keys) lives on an account_connections row with provider
-- 'AMAZON_ASSOCIATES'; secrets are stored in connection_credentials and
-- never serialized. Marketplace is already a column on
-- account_connections. No schema change required here.

-- --------------------------------------------------
-- 4) EXPORT-READY CONCEPT
-- --------------------------------------------------
-- exported_at records the manual export action (downloaded PNG/JPG and/or
-- copied title/description/URL). It is distinct from published_at, which
-- stays reserved for a real Pinterest API publish.
ALTER TABLE pinterest_queue ADD COLUMN exported_at DATETIME;

CREATE INDEX IF NOT EXISTS idx_queue_exported_at
    ON pinterest_queue (exported_at);
