import asyncio.exceptions

import disnake
from disnake.ext import commands

import random
import textdistance

from utils.bot import OGIROID
from utils.CONSTANTS import COUNTRIES
from utils.shortcuts import QuickEmb


class DevelopmentCommands(commands.Cog):
    """All commands currently under development!"""

    def __init__(self, bot: OGIROID):
        self.bot = bot
        self.countries = COUNTRIES

    # @command()
    # async def nohi(self, ctx): also do dontasktoask
    #    await ctx.try_reply('https://nohello.net/')

    # @commands.slash_command(name="flagquizz", description="Guess the flags.")
    # async def guess_the_flag(self, inter):
    #     await QuickEmb(inter, "Starting the quiz..").send()
    #     channel = inter.channel
    #     l = list(self.countries.items())
    #     random.shuffle(l)
    #     countries = dict(l)
    #
    #     def check(m):
    #         return m.author == inter.author and m.channel == inter.channel and len(m.content) <= 100
    #
    #     correct = 0
    #     tries = 0
    #     for emoji, country in countries.items():
    #         tries += 1
    #         retry = True
    #         while retry:
    #             embed = disnake.Embed(title="Guess the Flag.",
    #                                   description="To skip onto the next write ``skip``. To give up write ``give up``\n"
    #                                               f"Current Score: {correct}/{tries - 1}", color=0xFFFFFF)
    #             await channel.send(embed=embed)
    #             await channel.send(emoji)
    #             try:
    #                 guess = await self.bot.wait_for("message", check=check, timeout=60.0)
    #             except asyncio.exceptions.TimeoutError:
    #                 await QuickEmb(channel, "Due to no response the quiz ended early.").send()
    #                 return
    #
    #             if textdistance.hamming.normalized_similarity(guess.content.lower(), country.lower()) >= 0.8:
    #                 embed = QuickEmb(channel, f"Correct. The country indeed was {country}")
    #                 await embed.success().send()
    #                 correct += 1
    #                 retry = False
    #             elif guess.content.lower() == "skip":
    #                 await QuickEmb(channel, f'The country was {country}').send()
    #                 retry = False
    #             elif guess.content.lower() == "give up":
    #                 await QuickEmb(channel, f"Your Score: {correct}/{tries}. Thanks for playing.").send()
    #                 return
    #             else:
    #                 embed = QuickEmb(channel, "Incorrect")
    #                 await embed.error().send()
    #
    #     await channel.send(f"Great Job on finishing the entire Quiz. Score: {correct}/{tries}")

    # @commands.command(aliases=['ss'])
    # @commands.is_nsfw() ref https://github.com/JasonLovesDoggo/edoC/blob/55d3a36166eccdc1fe0b56bf9498d30fbb93f995/cogs/Info.py#L149
    # @commands.max_concurrency(1, BucketType.user)
    # async def screenshot(self, ctx, *, url: str):
    #    """
    #    Takes a screenshot of the given website.
    #    """


#
#    url = url.strip('<>')
#    if not match(URL_REGEX, url):
#        return await ctx.error('That is not a valid url. Try again with a valid one.')
#    link = f'https://image.thum.io/get/{url}'
#    # byt = BytesIO(await res.read())
#
#    em = Embed(description=f'`URL`: {link}', color=invis)
#    em.set_image(url=link)
#    await ctx.send(embed=em)

# @command(aliases=("spotify", "spot"),
#         brief="Show what song a member listening to in Spotify", )
# @cooldown(1, 5, BucketType.user)
# @guild_only()
# async def spotifyinfo(self, ctx, user: MemberConverterr = None):
#    user = user or ctx.author
#
#    spotify: discord.Spotify = discord.utils.find(
#        lambda s: isinstance(s, discord.Spotify), user.activities
#    )
#    if not spotify:
#        return await ctx.error(
#            f"{user} is not listening to Spotify!"
#        )
#
#    e = (
#        Embed(
#            title=spotify.title,
#            colour=spotify.colour,
#            url=f"https://open.spotify.com/track/{spotify.track_id}"
#        ).set_author(name="Spotify", icon_url="https://i.imgur.com/PA3vvdN.png"
#                     ).set_thumbnail(url=spotify.album_cover_url)
#    )
#
#    # duration
#    cur, dur = (
#        utcnow() - spotify.start.replace(tzinfo=timezone.utc),
#        spotify.duration,
#    )
#
#    # Bar stuff
#    barLength = 5 if user.is_on_mobile() else 17
#    bar = renderBar(
#        int((cur.seconds / dur.seconds) * 100),
#        fill="─",
#        empty="─",
#        point="⬤",
#        length=barLength,
#    )
#
#    e.add_field(name="Artist", value=", ".join(spotify.artists))
#
#    e.add_field(name="Album", value=spotify.album)
#
#    e.add_field(
#        name="Duration",
#        value=(
#                f"{cur.seconds // 60:02}:{cur.seconds % 60:02}"
#                + f" {bar} "
#                + f"{dur.seconds // 60:02}:"
#                + f"{dur.seconds % 60:02}"
#        ),
#        inline=False,
#    )
#    await ctx.try_reply(embed=e)


def setup(bot):
    bot.add_cog(DevelopmentCommands(bot))
