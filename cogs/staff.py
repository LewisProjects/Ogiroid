from disnake.ext import commands
import disnake
import time

class staff(commands.Cog):
    """Commands for the staff team!\n\n"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="faq")
    @commands.guild_only()
    @commands.has_role("Staff")
    async def faq(self, ctx, person: disnake.Member = None):
        """FAQ command for the staff team"""

        if person is None:
            await ctx.send("Please specify a person to tag")
            return
        channel = self.bot.get_channel(
            985554459948122142
        )  # replace ID with #reddit-faq channel ID
        message = await channel.send(f"{person.mention}")
        time.sleep(2)
        await message.delete()

def setup(bot):
    bot.add_cog(staff(bot))