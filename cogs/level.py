import disnake
from disnake.ext import commands
import random

from utils.bot import OGIROID
from utils.shortcuts import sucEmb, errorEmb, QuickEmb
from utils.CONSTANTS import levels, xp_probability


class Level(commands.Cog):
    def __init__(self, bot: OGIROID):
        self.bot = bot
        self.xp_probability = xp_probability
        self.levels = levels

    @staticmethod
    async def random_xp(self):
        return random.choice(self.xp_probability)
