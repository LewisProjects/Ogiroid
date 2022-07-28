CREATE TABLE
IF NOT EXISTS tags
(
    tag_id TEXT,
    content TEXT,
    owner INTEGER,
    created_at INTEGER,
    views INTEGER
);

CREATE TABLE
IF NOT EXISTS tickets
(
    channel_id INTEGER UNIQUE NOT NULL,
    user_id INTEGER NOT NULL
);
