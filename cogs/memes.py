from disnake.ext import commands
from datetime import datetime
import disnake
import aiohttp


class Memes(commands.Cog):
    """Meme Commands"""
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot

    @commands.slash_command(name="onlyfans", description="Lewis' OnlyFans")
    async def onlyfans(self, inter):
        """Lewis' Onlyfans"""
        await inter.response.send_message(
            "https://media.wired.com/photos/59548ac98e8cc150fa8ec379/master/w_2560%2Cc_limit/GettyImages-56196238.jpg"
        )

    @commands.slash_command(
        name="meme", aliases=["dankmeme"], description="Random meme from r/memes"
    )
    async def meme(self, inter):
        """Random meme from r/memes"""
        url = "https://api.reddit.com/r/memes/random"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                r = await response.json()
                upvotes = r[0]["data"]["children"][0]["data"]["ups"]
                embed = disnake.Embed(
                    title=f'{r[0]["data"]["children"][0]["data"]["title"]}',
                    description=f'{r[0]["data"]["children"][0]["data"]["selftext"]}',
                    colour=0x00B8FF,
                    timestamp=datetime.utcnow(),
                    url=f"https://www.reddit.com{r[0]['data']['children'][0]['data']['permalink']}",
                )
                embed.set_image(url=r[0]["data"]["children"][0]["data"]["url"])
                embed.set_footer(
                    text=f"{upvotes} Upvotes ",
                    icon_url="https://cdn.discordapp.com/attachments/925750381840064525/925755794669047899/PngItem_715538.png",
                )
                await inter.response.send_message(embed=embed)

    @commands.slash_command(
        name="programmerhumor", aliases=["progmeme","programmermeme","memeprogrammer"], description="Random meme from r/programmerhumor"
    )
    async def programmerhumor(self, inter):
        """Random meme from r/programmerhumor"""
        url = "https://api.reddit.com/r/ProgrammerHumor/random"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                r = await response.json()
                upvotes = r[0]["data"]["children"][0]["data"]["ups"]
                embed = disnake.Embed(
                    title=f'{r[0]["data"]["children"][0]["data"]["title"]}',
                    description=f'{r[0]["data"]["children"][0]["data"]["selftext"]}',
                    colour=0x00B8FF,
                    timestamp=datetime.utcnow(),
                    url=f"https://www.reddit.com{r[0]['data']['children'][0]['data']['permalink']}",
                )
                embed.set_image(url=r[0]["data"]["children"][0]["data"]["url"])
                embed.set_footer(
                    text=f"{upvotes} Upvotes ",
                    icon_url="https://cdn.discordapp.com/attachments/925750381840064525/925755794669047899/PngItem_715538.png",
                )
                await inter.response.send_message(embed=embed)


def setup(bot):
    bot.add_cog(Memes(bot))
