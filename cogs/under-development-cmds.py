from code import interact
from disnake.ext import commands
import disnake
import string
import secrets


class development_cmds(commands.Cog):
    """All commands currently under development!"""
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot


def setup(bot):
    bot.add_cog(development_cmds(bot))