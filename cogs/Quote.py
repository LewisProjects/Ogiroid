import os
import textwrap
from io import BytesIO

import disnake
import requests
from PIL import Image, ImageDraw, ImageFont
from disnake.ext import commands
from utils.bot import OGIROID


class Quote(commands.Cog):
    """Commands involving Quote! :)"""

    def __init__(self, bot: OGIROID):
        self.bot = bot




def setup(bot):
    bot.add_cog(Quote(bot))
