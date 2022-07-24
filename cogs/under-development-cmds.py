from disnake.ext import commands
import disnake


class DevelopmentCommands(commands.Cog):
    """All commands currently under development!"""
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot


def setup(bot):
    bot.add_cog(DevelopmentCommands(bot))
