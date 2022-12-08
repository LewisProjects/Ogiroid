from __future__ import annotations

import os

from utils.CONSTANTS import *


@dataclass
class GConfig:
    guild: int
    xp_boost: int | float
    xp_boost_expiry: int
    xp_boost_enabled: bool

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


@dataclass
class Tokens:
    SRA: str = os.getenv("SRA_API_KEY")
    bot: str = os.getenv("TOKEN")
    weathermap: str = os.getenv("OPEN_WEATHER_MAP_API_KEY")
    yt_api_key: str = os.getenv("YT_API_KEY")


@dataclass
class Database:
    user: str = os.getenv("POSTGRES_USER")
    password: str = os.getenv("POSTGRES_PASSWORD")
    host: str = os.getenv("POSTGRES_HOST")
    port: str = os.getenv("POSTGRES_PORT")
    database: str = "production"

    @classmethod
    def dev(cls):
        cls.database = "development"
        return cls


@dataclass
class Config:
    if os.getenv("DEVELOPMENT").lower() == "true":
        Development: bool = True
    elif os.getenv("DEVELOPMENT").lower() == "false":
        Development: bool = False
    else:
        raise ValueError("DEVELOPMENT in secrets.env must be set to true or false")
    colors = Colors
    colours = colors
    tokens = Tokens
    Database = Database
    if Development:
        print("Using Development Config variables")
        channels = Channels.dev()
        roles = Roles.dev()
        emojis = Emojis.dev()
        guilds = Guilds.dev()
        debug = True
        Database = Database.dev()
    else:
        emojis = Emojis
        channels = Channels
        roles = Roles
        guilds = Guilds
        debug = False
