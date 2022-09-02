from __future__ import annotations

import os

from utils.CONSTANTS import *


@dataclass
class Tokens:
    SRA: str = os.getenv("SRA_API_KEY")
    bot: str = os.getenv("TOKEN")
    weathermap: str = os.getenv("OPEN_WEATHER_MAP_API_KEY")


@dataclass
class Config:
    Development = True  # if true will use base server ID's else will use development server ID's
    colors = Colors
    colours = colors
    tokens = Tokens
    if Development:
        print("Using Development Config variables")
        channels = Channels.dev()
        roles = Roles.dev()
        emojis = Emojis.dev()
        debug = True
    else:
        emojis = Emojis
        channels = Channels
        roles = Roles
        debug = False
