from disnake.ext import commands

from utils.bot import OGIROID


class DevelopmentCommands(commands.Cog):
    """All commands currently under development!"""

    def __init__(self, bot: OGIROID):
        self.bot = bot


def setup(bot):
    bot.add_cog(DevelopmentCommands(bot))
