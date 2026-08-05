ALTER TABLE ai_content
ADD COLUMN validation_status TEXT NOT NULL DEFAULT 'PENDING';

ALTER TABLE ai_content
ADD COLUMN validation_error TEXT;
