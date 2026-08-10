PRAGMA foreign_keys = ON;

UPDATE pinterest_accounts
SET is_seed = 1
WHERE username = 'kitchenatlas';
