from disnake.ext import commands
import disnake
from disnake import TextInputStyle
from utils.bot import OGIROID

class Latex(commands.Cog):
    """Latex related commands"""

    def __init__(self, bot: OGIROID):
        self.bot = bot


    @commands.slash_command(name="strtolatex")
    @commands.guild_only()
    async def strtolatex(self, ctx, expression:str):
        """Convert a string to LaTeX"""
        expression_url = f"https://latex.codecogs.com/gif.latex?{expression}"
        embed = disnake.Embed(title="LaTeX", description=f"```{expression}```", color=0x00ff00)
        embed.set_image(url=expression_url)
        await ctx.send(embed=embed)

        

def setup(bot: OGIROID):
    bot.add_cog(Latex(bot))
