PRAGMA foreign_keys = ON;

-- ==========================================
-- COMPANY SETTINGS
-- ==========================================

CREATE TABLE IF NOT EXISTS company_settings (
    company_id INTEGER PRIMARY KEY AUTOINCREMENT,

    company_name TEXT NOT NULL,

    timezone TEXT NOT NULL DEFAULT 'Asia/Kolkata',

    language TEXT NOT NULL DEFAULT 'en',

    auto_publish INTEGER NOT NULL DEFAULT 0
        CHECK (auto_publish IN (0,1)),

    default_ai_model TEXT NOT NULL DEFAULT 'auto',

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO company_settings (
    company_name
)
VALUES (
    'Project Atlas'
);

-- ==========================================
-- CATEGORIES
-- ==========================================

CREATE TABLE IF NOT EXISTS categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,

    category_name TEXT NOT NULL UNIQUE,

    priority INTEGER NOT NULL DEFAULT 5,

    status TEXT NOT NULL DEFAULT 'ACTIVE'
        CHECK (status IN ('ACTIVE','INACTIVE')),

    daily_target INTEGER NOT NULL DEFAULT 5,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO categories (
    category_name,
    priority,
    daily_target
)
VALUES
(
    'Kitchen Storage',
    10,
    5
),
(
    'Home Storage',
    9,
    5
);
-- ==========================================
-- JOBS
-- ==========================================

CREATE TABLE IF NOT EXISTS jobs (
    job_id INTEGER PRIMARY KEY AUTOINCREMENT,

    department TEXT NOT NULL,

    job_type TEXT NOT NULL,

    status TEXT NOT NULL DEFAULT 'PENDING'
        CHECK (status IN (
            'PENDING',
            'IN_PROGRESS',
            'COMPLETED',
            'FAILED',
            'CANCELLED'
        )),

    priority INTEGER NOT NULL DEFAULT 5,

    payload TEXT,

    retry_count INTEGER NOT NULL DEFAULT 0,

    error_message TEXT,

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    started_at DATETIME,

    completed_at DATETIME
);
INSERT INTO jobs (
    department,
    job_type,
    priority,
    payload
)
VALUES (
    'Research',
    'DiscoverProducts',
    10,
    '{"category":"Kitchen Storage"}'
);
