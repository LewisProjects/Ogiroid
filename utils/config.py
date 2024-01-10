from __future__ import annotations

import os

from utils.CONSTANTS import *


@dataclass
class Tokens:
    SRA: str = os.getenv("SRA_API_KEY")
    bot: str = os.getenv("TOKEN")
    weathermap: str = os.getenv("OPEN_WEATHER_MAP_API_KEY")
    yt_api_key: str = os.getenv("YT_API_KEY")


@dataclass
class Database:  # Todo switch to rockdb info
    connection_string = os.getenv("POSTGRES_CONNECTION_STRING")

    @classmethod
    def dev(cls):
        cls.database = os.getenv("POSTGRES_CONNECTION_STRING")
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
