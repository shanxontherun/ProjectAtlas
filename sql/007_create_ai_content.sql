PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS ai_content (

    ai_content_id INTEGER PRIMARY KEY AUTOINCREMENT,

    research_product_id INTEGER NOT NULL UNIQUE,

    seo_title TEXT,

    pinterest_title TEXT,

    pinterest_description TEXT,

    pinterest_keywords TEXT,

    board_name TEXT,

    instagram_caption TEXT,

    blog_summary TEXT,

    ai_score INTEGER
        CHECK (ai_score BETWEEN 0 AND 100),

    status TEXT NOT NULL DEFAULT 'GENERATED'
        CHECK (
            status IN (
                'GENERATED',
                'APPROVED',
                'REJECTED'
            )
        ),

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (research_product_id)
        REFERENCES research_products(research_product_id)
);
