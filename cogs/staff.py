from disnake.ext import commands
import disnake
import time
import asyncio


class Staff(commands.Cog):
    """Commands for the staff team!\n\n"""

    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="faq")
    @commands.guild_only()
    @commands.has_role("Staff")
    async def faq(self, ctx, person: disnake.Member):
        """FAQ command for the staff team"""
        channel = self.bot.get_channel(985908874362093620)  # reddit-faq channel ID
        message = await channel.send(f"{person.mention}")
        time.sleep(2)
        await message.delete()


def setup(bot):
    bot.add_cog(Staff(bot))
