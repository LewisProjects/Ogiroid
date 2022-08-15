import disnake
from disnake.ext import commands
import random

from utils.bot import OGIROID
from utils.shortcuts import sucEmb, errorEmb, QuickEmb
from utils.CONSTANTS import levels, xp_probability


class Level(commands.Cog):
    def __init__(self, bot: OGIROID):
        self.bot = bot
        self.levels = levels

    @staticmethod
    async def random_xp():
        return random.choice(xp_probability)




def setup(bot: OGIROID):
    bot.add_cog(Level(bot))
