from disnake.ext import commands
import disnake


class Google(commands.Cog):
    """Google stuff"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(description="Returns a google search for your query")
    async def google(self, inter, query):
        """Googles the keyword entered"""
        query = query.replace(" ", "+")
        await inter.send(f"https://www.google.com/search?q={query}")

    @commands.slash_command(name="feeling-lucky", description="Returns the first google result for your query")
    async def lucky(self, inter, query):
        """Googles the keyword entered and returns the first result"""
        query = query.replace(" ", "+")
        await inter.send(f"https://www.google.com/search?q={query}&btnI")


def setup(bot: commands.Bot):
    bot.add_cog(Google(bot))
