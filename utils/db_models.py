import time

from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    Text,
    Boolean,
    UniqueConstraint,
    ARRAY,
)
from sqlalchemy.orm import declarative_base

from utils.CONSTANTS import LEVELS_AND_XP
from utils.shortcuts import get_expiry

Base = declarative_base()


class Tag(Base):
    __tablename__ = "tags"
    name = Column(Text, primary_key=True)
    content = Column(Text)
    owner = Column(BigInteger)
    created_at = Column(BigInteger)
    views = Column(Integer)


class TagRelations(Base):
    __tablename__ = "tag_relations"
    id = Column(Integer, primary_key=True)
    name = Column(Text)
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

    def is_expired(self):
        if self.expires == 9999999999:
            return False
        return int(time.time()) > self.expires

    @property
    def get_expiry(self):
        return get_expiry(self.expires)


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


class ReactionRole(Base):
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
    total_xp = Column(Integer, default=0)

    @property
    def level(self):
        # get users level based on total xp
        for level, xp in LEVELS_AND_XP.items():
            if self.total_xp < xp:
                return level - 1

    @property
    def xp(self):
        # get users xp based on total xp
        for level, xp in LEVELS_AND_XP.items():
            if self.total_xp < xp:
                return self.total_xp - LEVELS_AND_XP[level - 1]


class CustomRoles(Base):
    __tablename__ = "custom_roles"
    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)
    role_id = Column(BigInteger)
    user_id = Column(BigInteger)


class RoleReward(Base):
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
    custom_roles_threshold = Column(Integer, default=20)
    min_required_lvl = Column(Integer, default=5)
    position_role_id = Column(BigInteger, default=None)

    @property
    def boost_expired(self):
        from time import time

        now = int(time())
        if self.xp_boost_expiry >= now:
            return False
        return True

    @property
    def boost_time_left(self):
        from time import time

        now = int(time())
        return self.xp_boost_expiry - now

    @property
    def get_boost(self):
        return self.xp_boost

    @property
    def xp_boost_active(self) -> bool:
        return bool(self.xp_boost_enabled) and not self.boost_expired


class Commands(Base):
    __tablename__ = "commands"
    __table_args__ = (UniqueConstraint("guild_id", "command"),)
    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)
    command = Column(Text)
    command_used = Column(Integer, default=0)


class TotalCommands(Base):
    __tablename__ = "total_commands"
    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger, unique=True)
    total_commands_used = Column(Integer, default=0)


class AutoResponseMessages(Base):
    __tablename__ = "auto_response_messages"
    # needs to be list of strings and list of regex strings, channels, guild and response
    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger)
    channel_ids = Column(ARRAY(BigInteger))
    regex_strings = Column(ARRAY(Text))
    strings = Column(ARRAY(Text))
    response = Column(Text)
    case_sensitive = Column(Boolean, default=False)
    enabled = Column(Boolean, default=True)
