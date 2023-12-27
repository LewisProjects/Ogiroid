from sqlalchemy import Column, Integer, BigInteger, Text, Boolean, UniqueConstraint
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Tags(Base):
    __tablename__ = "tags"
    tag_id = Column(Text, primary_key=True)
    content = Column(Text)
    owner = Column(BigInteger)
    created_at = Column(BigInteger)
    views = Column(Integer)


class TagRelations(Base):
    __tablename__ = "tag_relations"
    id = Column(Integer, primary_key=True)
    tag_id = Column(Text)
    alias = Column(Text)


class Blacklist(Base):
    __tablename__ = "blacklist"
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger)
    reason = Column(Text)
    bot = Column(Boolean)
    tickets = Column(Boolean)
    tags = Column(Boolean)
    expires = Column(BigInteger)


class FlagQuiz(Base):
    __tablename__ = "flag_quiz"
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger)
    tries = Column(Integer)
    correct = Column(Integer)
    completed = Column(Integer)
    guild_id = Column(BigInteger)


class Trivia(Base):
    __tablename__ = "trivia"
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger)
    correct = Column(Integer)
    incorrect = Column(Integer)
    streak = Column(Integer)
    longest_streak = Column(Integer)


class ReactionRoles(Base):
    __tablename__ = "reaction_roles"
    id = Column(Integer, primary_key=True)
    message_id = Column(BigInteger)
    role_id = Column(BigInteger)
    emoji = Column(Text)
    roles_given = Column(Integer, default=0)


class Warnings(Base):
    __tablename__ = "warnings"
    warning_id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger)
    moderator_id = Column(BigInteger)
    reason = Column(Text)
    guild_id = Column(BigInteger)


class Levels(Base):
    __tablename__ = "levels"
    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)
    user_id = Column(BigInteger)
    level = Column(Integer, default=0)
    xp = Column(Integer, default=0)


class RoleRewards(Base):
    __tablename__ = "role_rewards"
    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)
    role_id = Column(BigInteger)
    required_lvl = Column(Integer, default=0)


class Birthday(Base):
    __tablename__ = "birthday"
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger)
    birthday = Column(Text, default=None)
    birthday_last_changed = Column(BigInteger, default=None)


class Timezone(Base):
    __tablename__ = "timezone"
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger)
    timezone = Column(Text, default=None)
    timezone_last_changed = Column(BigInteger, default=None)


class Config(Base):
    __tablename__ = "config"
    guild_id = Column(BigInteger, primary_key=True)
    xp_boost = Column(Integer, default=1)
    xp_boost_expiry = Column(BigInteger, default=0)
    xp_boost_enabled = Column(Boolean, default=True)


class Commands(Base):
    __tablename__ = "commands"
    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)
    command = Column(Text)
    command_used = Column(Integer, default=0)
    UniqueConstraint("guild_id", "command", name="guild_command")


class TotalCommands(Base):
    __tablename__ = "total_commands"
    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger, unique=True)
    total_commands_used = Column(Integer, default=0)
