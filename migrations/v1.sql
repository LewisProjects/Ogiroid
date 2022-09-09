CREATE TABLE levels_temp AS SELECT guild_id, user_id, level, xp FROM levels;
DROP TABLE levels;
ALTER TABLE levels_temp RENAME TO levels;
