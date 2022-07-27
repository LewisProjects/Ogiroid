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

    @commands.slash_command(name="prune")
    @commands.guild_only()
    @commands.has_role("Staff")
    async def prune(self, ctx, amount: int):
        """Delete messages, max limit set to 25."""
        # Checking if amount > 25:
        if amount > 25:
            await ctx.send("Amount is too high, please use a lower amount")
            return
        await ctx.channel.purge(limit=amount)
        await ctx.send(f"Deleted {amount} messages successfully!")

    @commands.slash_command(name="channellock")
    @commands.guild_only()
    @commands.has_role("Staff")
    async def channellock(self, ctx, channel: disnake.TextChannel):
        """Lock a channel"""
        # Lock's a channel by not letting anyone send messages to it
        await channel.set_permissions(ctx.guild.default_role, send_messages=False)
        await ctx.send(f"🔒 Locked {channel.mention} successfully!")

    @commands.slash_command(name="channelunlock")
    @commands.guild_only()
    @commands.has_role("Staff")
    async def channelunlock(self, ctx, channel: disnake.TextChannel):
        """Unlock a channel"""
        # Unlock's a channel by letting everyone send messages to it
        await channel.set_permissions(ctx.guild.default_role, send_messages=True)
        await ctx.send(f"🔓 Unlocked {channel.mention} successfully!")


def setup(bot):
    bot.add_cog(Staff(bot))
