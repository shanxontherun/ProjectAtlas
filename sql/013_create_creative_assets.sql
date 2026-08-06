CREATE TABLE IF NOT EXISTS creative_assets (

    creative_id INTEGER PRIMARY KEY AUTOINCREMENT,

    ai_content_id INTEGER NOT NULL,

    template_name TEXT NOT NULL,

    headline TEXT NOT NULL,

    image_path TEXT NOT NULL,

    status TEXT NOT NULL DEFAULT 'GENERATED',

    error TEXT,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(ai_content_id)
        REFERENCES ai_content(ai_content_id)
);

CREATE INDEX IF NOT EXISTS idx_creative_assets_ai_content_id
    ON creative_assets (ai_content_id);
