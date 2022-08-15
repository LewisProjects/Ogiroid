from disnake.ext import commands

from utils.bot import OGIROID


class StackOverflow(commands.Cog):
    """StackOverflow stuff"""

    def __init__(self, bot: OGIROID):
        self.bot = bot

    @commands.slash_command(description="Returns a StackOverflow search for your query")
    async def google(self, inter, query):
        """Searches StackOverflow for the query"""
        query = query.rstrip().replace(" ", "+")
        await inter.send(f"https://stackoverflow.com/search?q={query}")


def setup(bot: commands.Bot):
    bot.add_cog(StackOverflow(bot))
