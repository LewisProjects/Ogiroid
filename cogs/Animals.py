import disnake
from disnake.ext import commands
import aiohttp
from utils.bot import OGIROID


class Animals(commands.Cog):
    """Animals related commands!"""

    def __init__(self, bot: OGIROID):
        self.bot = bot

    @commands.slash_command(description="Gets a random picture of the specified animal")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def animal(self, inter):
        pass

    @animal.sub_command(description="get a catfact")
    async def catfact(interaction: disnake.ApplicationCommandInteraction):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://catfact.ninja/fact") as response:
                fact = (await response.json())["fact"]
                length = (await response.json())["length"]
                embed = disnake.Embed(title=f'Random Cat Fact Number: **{length}**', description=f'Cat Fact: {fact}', colour=0x400080)
                embed.set_footer(text="")
                await interaction.response.send_message(embed=embed)

    @animal.sub_command(name="cat", description="Get a random cat picture")
    async def cat(self, inter):
        """Get a random cat picture!"""
        response = await self.bot.session.get("https://some-random-api.com/animal/cat")
        data = await response.json()
        embed = disnake.Embed(
            title="Cat Picture! 🐱",
            description="Get a picture of a cat!",
            color=0xFFFFFF,
        )
        embed.set_image(url=data["image"])
        embed.set_footer(
            text=f"Command issued by: {inter.author.name}",
            icon_url=inter.author.display_avatar,
        )
        await inter.send(f"**Fun Fact: **" + data["fact"], embed=embed)

    # Similar methods for other animals omitted for brevity

def setup(bot):
    bot.add_cog(Animals(bot))
