PRAGMA foreign_keys = ON;

ALTER TABLE pinterest_accounts ADD COLUMN is_seed INTEGER NOT NULL DEFAULT 0;

UPDATE pinterest_accounts
SET is_seed = 1
WHERE username IN ('atlashome', 'atlasfinds');
