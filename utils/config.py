from __future__ import annotations

import os

from utils.CONSTANTS import *


@dataclass
class Tokens:
    SRA: str = os.getenv("SRA_API_KEY")
    bot: str = os.getenv("TOKEN")
    weathermap: str = os.getenv("OPEN_WEATHER_MAP_API_KEY")


@dataclass
class Database:
    user: str = os.getenv("POSTGRES_USER")
    password: str = os.getenv("POSTGRES_PASSWORD")
    host: str = os.getenv("POSTGRES_HOST")
    port: str = os.getenv("POSTGRES_PORT")
    database: str = "production"

    @classmethod
    def dev(cls):
        cls.user: str = os.getenv("POSTGRES_PASSWORD")
        cls.password: str = os.getenv("POSTGRES_PASS")
        cls.host: str = os.getenv("POSTGRES_HOST")
        cls.port: str = os.getenv("POSTGRES_PORT")
        cls.database = "development"
        return cls


@dataclass
class Config:
    Development = False  # if true will use base server ID's else will use development server ID's
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
