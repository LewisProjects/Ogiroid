import time

from disnake.ext import commands
import disnake

from cogs.redditbot import RedditBot
from utils.bot import OGIROID


class Tags(commands.Cog, name="Tags"):
    """Everything Tag related"""

    def __init__(self, bot: OGIROID):
        self.bot = bot

    @property
    def db(self):
        return self.bot.db

    @commands.slash_command(name="maketag", description="Creates a tag")
    @commands.guild_only()
    @commands.has_permissions()
    async def make_tag(self, inter, name, *, content):
        """Makes a new tag"""
        if not await self.tag_exists(name):
            return await inter.send(f"tag {name} already exists")

        await self.db.execute("INSERT INTO tags (tag_id, content) VALUES (?, ?)", [name, content])
        await self.db.commit()
        await inter.send(f"I have successfully made **{name}**. To view it do /tag {name}")

    @commands.slash_command(name="edittag", description="Edits the tag")
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def edittag(self, inter, name, *, new_content):
        """Edit a tag"""

        await self.db.execute("UPDATE tags SET content = ? WHERE tag_id = ?", [new_content, name])
        await self.db.commit()
        await inter.send(f"I have successfully updated **{name}**. \n\n **{name}**\n__{new_content}__")

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

    async def tag_exists(self, name):  # prob a better way to do this somebody fixes it
        # check if a tag exists based off of tag_id in a sqlite database
        async with self.db.execute("SELECT * FROM tags WHERE tag_id = ?", [name]) as cur:
            async for row in cur:
                print(row)
                time.sleep(21)
                return True
        return False


def setup(bot):
    bot.add_cog(RedditBot(bot))
