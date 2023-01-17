CREATE TABLE
IF NOT EXISTS tags
(
    tag_id TEXT,
    content TEXT,
    owner BIGINT,
    created_at BIGINT,
    views INTEGER
);

CREATE TABLE
IF NOT EXISTS tag_relations
(
    tag_id TEXT,
    alias TEXT
);

CREATE TABLE
IF NOT EXISTS blacklist
(
    user_id BIGINT,
    reason TEXT,
    bot BOOLEAN,
    tickets BOOLEAN,
    tags BOOLEAN,
    expires BIGINT
);

CREATE TABLE
IF NOT EXISTS flag_quizz
(
    user_id BIGINT,
    tries INTEGER,
    correct INTEGER,
    completed INTEGER
    guild_id INTEGER
);

CREATE TABLE
IF NOT EXISTS trivia
(
    id BIGINT,
    correct INTEGER,
    incorrect INTEGER,
    streak INTEGER,
    longest_streak INTEGER
);

CREATE TABLE
IF NOT EXISTS reaction_roles
(
    message_id BIGINT,
    role_id BIGINT,
    emoji TEXT,
    roles_given INTEGER DEFAULT 0
);

CREATE TABLE
IF NOT EXISTS warnings
(
    warning_id SERIAL PRIMARY KEY,
    user_id BIGINT,
    moderator_id BIGINT,
    reason TEXT,
    guild_id BIGINT
);

CREATE TABLE
IF NOT EXISTS levels
(
    guild_id BIGINT,
    user_id BIGINT,
    level INTEGER DEFAULT 0,
    xp INTEGER DEFAULT 0
);

CREATE TABLE
IF NOT EXISTS role_rewards
(
    guild_id BIGINT,
    role_id BIGINT,
    required_lvl INTEGER DEFAULT 0
);

CREATE TABLE
IF NOT EXISTS birthday
(
    user_id BIGINT,
    birthday TEXT DEFAULT NULL,
    birthday_last_changed BIGINT DEFAULT NULL
);

CREATE TABLE
IF NOT EXISTS timezone
(
    user_id BIGINT,
    timezone TEXT DEFAULT NULL,
    timezone_last_changed BIGINT DEFAULT NULL
);

CREATE TABLE
IF NOT EXISTS config
(
    guild_id BIGINT,
    xp_boost INTEGER DEFAULT 1,
    xp_boost_expiry BIGINT DEFAULT 0,
    xp_boost_enabled BOOLEAN DEFAULT TRUE,
    UNIQUE(guild_id)


);

DROP TABLE IF EXISTS xp_boosts_user;


