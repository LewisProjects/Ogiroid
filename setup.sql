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
IF NOT EXISTS tag_relations
(
    tag_id TEXT,
    alias TEXT
);

CREATE TABLE
IF NOT EXISTS tickets
(
    channel_id TEXT,
    user_id TEXT
);

CREATE TABLE
IF NOT EXISTS blacklist
(
    user_id INTEGER,
    reason TEXT,
    bot BOOLEAN,
    tickets BOOLEAN,
    tags BOOLEAN,
    expires TEXT
);

CREATE TABLE
IF NOT EXISTS flag_quizz
(
    user_id INTEGER,
    tries INTEGER,
    correct INTEGER,
    completed INTEGER
);
