PRAGMA foreign_keys = ON;

ALTER TABLE pinterest_boards ADD COLUMN pin_count INTEGER NOT NULL DEFAULT 0;
ALTER TABLE pinterest_boards ADD COLUMN follower_count INTEGER NOT NULL DEFAULT 0;

INSERT OR IGNORE INTO pinterest_accounts (
    account_id,
    account_name,
    username,
    niche_slug,
    daily_limit,
    status
)
VALUES
    (1, 'Atlas Home', 'atlashome', 'home-living', 15, 'ACTIVE'),
    (2, 'Atlas Finds', 'atlasfinds', 'everyday-finds', 15, 'ACTIVE');

INSERT OR IGNORE INTO pinterest_boards (
    board_id,
    account_id,
    board_name,
    category_slug,
    status,
    pin_count,
    follower_count
)
VALUES
    (1, 1, 'Home Essentials', 'home', 'ACTIVE', 1240, 48200),
    (2, 1, 'Kitchen Organization', 'kitchen', 'ACTIVE', 890, 32100),
    (3, 1, 'Laundry Hacks', 'laundry', 'ACTIVE', 560, 21400),
    (4, 2, 'Bathroom Ideas', 'bathroom', 'ACTIVE', 720, 27600),
    (5, 2, 'Amazon Home Finds', 'home', 'ACTIVE', 1520, 91400);

INSERT OR IGNORE INTO category_routes (
    category_slug,
    account_id,
    board_id,
    priority
)
VALUES
    ('kitchen', 1, 2, 1),
    ('home', 1, 1, 1),
    ('pantry', 1, 1, 1),
    ('bathroom', 2, 4, 1),
    ('closet', 1, 3, 1);
