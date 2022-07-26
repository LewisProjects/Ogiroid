import email
from disnake.ext import commands
import disnake
import time

# import speedtest

#
# Tag System Made by github.com/FreebieII
#
from cogs.utils.bot import OGIROID


class RedditBot(commands.Cog, name="Reddit Bot"):
    """All the Reddit Bot related commands!\n\n"""

    def __init__(self, bot: OGIROID):
        self.bot = bot

    @property
    def db(self):
        return self.bot.db

    @commands.slash_command(name="maketag", description="Creates a tag")
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def make_tag(self, ctx, name, *, content):
        """Makes a new tag"""
        await self.db.execute("INSERT INTO tags (tag_id, content) VALUES (?, ?)", [name, content])
        await self.db.commit()
        await ctx.reply(f"I have successfully made **{name}**. To view it do /tag {name}")

    @commands.slash_command(name="edittag", description="Edits the tag")
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def edittag(self, ctx, name, *, new_content):
        """Edit a tag"""

        await self.db.execute("UPDATE tags SET content = ? WHERE tag_id = ?", [new_content, name])
        await self.db.commit()
        await ctx.reply(f"I have successfully updated **{name}**. \n\n **{name}**\n__{new_content}__")

    @commands.slash_command(name="deltag", description="Deletes the tag.")
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def deltag(self, ctx, name):
        """Delete a tag"""
        if name is None:
            await ctx.send("Please tell me which tag to delete! `/deltag tag_name`")
            return

        await self.db.execute("DELETE FROM tags WHERE tag_id = ?", [name])
        await self.db.commit()
        await ctx.reply(f"I have successfully deleted **{name}**.")

    @commands.slash_command(name="tag", description="Gives you the tags value")
    @commands.guild_only()
    async def tag(self, ctx, name):

        if name is None:
            await ctx.send("Which tag do you want to use? You can use `/tags` to see all available tags!")
            return

        async with self.db.execute("SELECT content FROM tags WHERE tag_id = ? LIMIT 20", [name]) as cur:
            async for row in cur:
                await ctx.send(f"{row[0]}")

    @commands.slash_command(name="taglist", description="Lists tags")
    @commands.guild_only()
    async def list_tags(self, ctx):
        embed = disnake.Embed(
            title="\n",
            description="Tagging system made by [FreebieII](https://github.com/FreebieII)",
            color=0x53E7CE,
        )
        embed.set_footer(
            text="Reddit Help Bot",
            icon_url="https://64.media.tumblr.com/0f377879537d8206fcf018a01cd395fa/tumblr_pdcvzmjvvm1qeyvpto1_500.gif",
        )
        # embed.set_thumbnail(url="https://i.gifer.com/4EfW.gif")
        async with self.db.execute("SELECT * FROM tags LIMIT 20") as cur:
            async for tags in cur:
                embed.add_field(name="Showing all available tags", value=f" `{tags[0]}`")
        await ctx.send(embed=embed)

    @commands.slash_command(name="taghelp", description="Help for the tag system")
    @commands.guild_only()
    async def tag_help(self, ctx):
        await ctx.send(
            "```\n/tag [name] - Prints out the message for the given tag (or /t [name])\n!!maketag [name] [content...] - Creates a new tag\n/deltag [name] - Deletes an existing tag\n/edittag [name] [new_contant...] - Edits and existing tag\n/taglist (or !!tags) - Shows a list of available tags\n\n**NOTE:** You must have the `Manage Messages` permission to use these commands.\n```"
        )

    # Get Information Related to the GitHub of the Bot
    @commands.slash_command(name="rbgithub", description="Get Information Related to the GitHub of the Reddit Bot")
    @commands.guild_only()
    async def rbgithub(self, ctx):
        url = await self.bot.session.get("https://api.github.com/repos/elebumm/RedditVideoMakerBot")
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
