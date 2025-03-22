
-- === PickleJar PostgreSQL Schema (Optimized) ===

-- Main user tracking table
CREATE TABLE IF NOT EXISTS pickle_counts (
  user_id BIGINT PRIMARY KEY,
  count INTEGER DEFAULT 0,
  pickles INTEGER DEFAULT 100,
  warnings INTEGER DEFAULT 0,
  last_daily TIMESTAMP
);

-- Index for quick lookup by warnings or pickles
CREATE INDEX IF NOT EXISTS idx_pickle_warnings ON pickle_counts (warnings);
CREATE INDEX IF NOT EXISTS idx_pickle_counts ON pickle_counts (pickles);

-- Shop items
CREATE TABLE IF NOT EXISTS shop_items (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  emoji TEXT NOT NULL,
  price INTEGER NOT NULL,
  description TEXT,
  role_id BIGINT
);

-- Default shop entries
INSERT INTO shop_items (name, emoji, price, description)
VALUES
  ('Swear Pass', '🎟️', 150, 'One-time pass to swear without penalty'),
  ('Money Bag', '💰', 100, 'Grants 50 bonus pickles'),
  ('Mute Token', '🔇', 300, 'Mute someone for 5 minutes')
ON CONFLICT DO NOTHING;

-- Inventory table
CREATE TABLE IF NOT EXISTS user_inventory (
  user_id BIGINT NOT NULL,
  item_id INTEGER NOT NULL,
  quantity INTEGER DEFAULT 1,
  PRIMARY KEY (user_id, item_id)
);

-- Purchases
CREATE TABLE IF NOT EXISTS shop_purchases (
  id SERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL,
  item_id INTEGER NOT NULL,
  price_paid INTEGER NOT NULL,
  purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Positive words
CREATE TABLE IF NOT EXISTS positive_words (
  word TEXT PRIMARY KEY,
  reward INTEGER NOT NULL
);

-- Default positive words
INSERT INTO positive_words (word, reward)
VALUES 
  ('thanks', 5),
  ('great', 5),
  ('awesome', 5)
ON CONFLICT DO NOTHING;

-- Swear words
CREATE TABLE IF NOT EXISTS swear_words (
  word TEXT PRIMARY KEY
);

-- Warning messages
CREATE TABLE IF NOT EXISTS warning_messages (
  message TEXT PRIMARY KEY
);

-- Settings
CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT
);

-- Media Submissions
CREATE TABLE IF NOT EXISTS media_submissions (
  id SERIAL PRIMARY KEY,
  url TEXT NOT NULL,
  title TEXT,
  description TEXT,
  tags TEXT[],
  submitted_by BIGINT NOT NULL,
  approved BOOLEAN DEFAULT FALSE,
  submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for media lookups
CREATE INDEX IF NOT EXISTS idx_media_approved ON media_submissions (approved);
CREATE INDEX IF NOT EXISTS idx_media_user ON media_submissions (submitted_by);
