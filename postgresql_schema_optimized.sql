-- ✅ PickleJar Core Schema

CREATE TABLE IF NOT EXISTS pickle_counts (
    user_id VARCHAR(32) PRIMARY KEY,
    count INTEGER DEFAULT 0,
    coins INTEGER DEFAULT 100,
    warnings INTEGER DEFAULT 0,
    last_daily TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pickle_counts_user ON pickle_counts(user_id);

CREATE TABLE IF NOT EXISTS swear_words (
    word TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS positive_words (
    word TEXT PRIMARY KEY,
    reward INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);

-- ✅ Shop System

CREATE TABLE IF NOT EXISTS shop_items (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    emoji TEXT NOT NULL,
    price INTEGER NOT NULL,
    description TEXT,
    role_id TEXT
);

CREATE TABLE IF NOT EXISTS user_inventory (
    user_id VARCHAR(32),
    item_id INTEGER,
    quantity INTEGER DEFAULT 1,
    PRIMARY KEY (user_id, item_id),
    FOREIGN KEY (item_id) REFERENCES shop_items(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS shop_purchases (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(32) NOT NULL,
    item_id INTEGER NOT NULL,
    price_paid INTEGER NOT NULL,
    purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES shop_items(id) ON DELETE CASCADE
);

-- ✅ Media Finder Bot

CREATE TABLE IF NOT EXISTS media_collections (
    id SERIAL PRIMARY KEY,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    url TEXT NOT NULL,
    tags TEXT[],
    added_by VARCHAR(32),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_media_category ON media_collections(category);
CREATE INDEX IF NOT EXISTS idx_media_added_by ON media_collections(added_by);

CREATE TABLE IF NOT EXISTS media_stats (
    media_id INTEGER PRIMARY KEY,
    views INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    last_viewed TIMESTAMP,
    FOREIGN KEY (media_id) REFERENCES media_collections(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS media_submissions (
    id SERIAL PRIMARY KEY,
    category TEXT,
    title TEXT,
    description TEXT,
    url TEXT,
    tags TEXT[],
    added_by VARCHAR(32),
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved BOOLEAN DEFAULT FALSE
);

-- ✅ Warnings & Custom Messages

CREATE TABLE IF NOT EXISTS warning_messages (
    message TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS moderation_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);