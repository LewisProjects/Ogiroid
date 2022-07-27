from disnake.ext import commands
import disnake
import time

from utils.CONSTANTS import REDDIT_FAQ_CHANNEL
from utils.bot import OGIROID


class Staff(commands.Cog):
    """Commands for the staff team!\n\n"""

    def __init__(self, bot: OGIROID):
        self.bot = bot

    @commands.slash_command(name="faq")
    @commands.guild_only()
    @commands.has_role("Staff")
    async def faq(self, ctx, person: disnake.Member):
        """FAQ command for the staff team"""
        channel = self.bot.get_channel(REDDIT_FAQ_CHANNEL)
        await channel.send(f"{person.mention}", delete_after=2)
        # Sending Done so this Application didn't respond error can be avoided
        await ctx.send("Done", delete_after=1)


def setup(bot):
    bot.add_cog(Staff(bot))
