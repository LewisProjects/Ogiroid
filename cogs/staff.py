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
        channel = self.bot.get_channel(
            985554459948122142
        )  # replace ID with #reddit-faq channel ID
        message = await channel.send(f"{person.mention}")
        time.sleep(2)
        await message.delete()
        embed = disnake.Embed(
            title="Done"
        )
        await ctx.response.send_message(embed=embed, delete_after=2)


def setup(bot):
    bot.add_cog(Staff(bot))
