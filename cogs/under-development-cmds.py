from disnake.ext import commands

from utils.bot import OGIROID


class DevelopmentCommands(commands.Cog):
    """All commands currently under development!"""

    def __init__(self, bot: OGIROID):
        self.bot = bot

    # @command()
    # async def nohi(self, ctx): also do dontasktoask
    #    await ctx.try_reply('https://nohello.net/')

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
