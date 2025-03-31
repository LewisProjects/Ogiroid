import disnake
from disnake.ext import commands

from utils.bot import OGIROID


class RedditBot(commands.Cog, name="Reddit Bot"):
    """All the Reddit Bot related commands!"""

    def __init__(self, bot: OGIROID):
        self.bot = bot

    # Get Information Related to the GitHub of the Bot
    @commands.slash_command(
        name="rbgithub",
        description="Get Information Related to the GitHub of the Reddit Bot",
    )
    @commands.guild_only()
    async def rbgithub(self, ctx):
        url = await self.bot.session.get(
            "https://api.github.com/repos/elebumm/RedditVideoMakerBot"
        )
        json = await url.json()
        if url.status == 200:
            # Creat an embed with the information: Name, Description, URL, Stars, Gazers, Forks, Last Updated
            embed = disnake.Embed(
                title=f"{json['name']} information",
                description=f"{json['description']}",
                color=0xFFFFFF,
            )
            embed.set_thumbnail(url=f"{json['owner']['avatar_url']}")
            embed.add_field(
                name="GitHub Link: ",
                value=f"**[Link to the Reddit Bot]({json['html_url']})**",
                inline=True,
            )
            embed.add_field(
                name="Stars <:starr:990647250847940668>: ",
                value=f"{json['stargazers_count']}",
                inline=True,
            )
            embed.add_field(
                name="Gazers <:gheye:990645707427950593>: ",
                value=f"{json['subscribers_count']}",
                inline=True,
            )
            embed.add_field(
                name="Forks <:fork:990644980773187584>: ",
                value=f"{json['forks_count']}",
                inline=True,
            )
            embed.add_field(
                name="Open Issues <:issue:990645996918808636>: ",
                value=f"{json['open_issues_count']}",
                inline=True,
            )
            embed.add_field(
                name="License <:license:990646337118818404>: ",
                value=f"{json['license']['spdx_id']}",
                inline=True,
            )
            embed.add_field(
                name="Clone Command <:clone:990646924640153640>: ",
                value=f"```git clone {json['clone_url']}```",
                inline=False,
            )
            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(RedditBot(bot))
