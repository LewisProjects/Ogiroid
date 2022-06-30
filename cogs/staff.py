from disnake.ext import commands
import disnake
import time


#
# Tag System Made by github.com/FreebieII
#


class Staff(commands.Cog):
    """Tag system for the staff team\n\n"""

    def __init__(self, bot):
        self.bot = bot

    @property
    def db(self):
        return self.bot.db

    @commands.command(name="faq")
    @commands.guild_only()
    @commands.has_role("Staff")
    async def faq(self, ctx, person: disnake.Member = None):
        """FAQ command for the staff team"""

        if person is None:
            await ctx.send("Please specify a person to tag")
            return
        channel = self.bot.get_channel(
            985908874362093620
        )  # replace ID with #reddit-faq channel ID
        message = await channel.send(f"{person.mention}")
        time.sleep(2)
        await message.delete()

    @commands.command(name="maketag", usage="!!maketag [name] [content]")
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def make_tag(self, ctx, name, *, content=None):
        """Makes a new tag"""
        if content is None:
            await ctx.send("What should the content be? `!!t tag_name tag_content`")
            return
        await self.db.execute(
            "INSERT INTO tags (tag_id, content) VALUES (?, ?)", [name, content]
        )
        await self.db.commit()
        await ctx.reply(
            f"I have successfully made **{name}**. To view it do !!tag {name}"
        )


    @commands.command(name="edittag", usage="!!edittag [name] [new_content]")
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def edittag(self, ctx, name, *, new_content=None):
        """Edit a tag"""
        #     if new_content or name is None:
        #        await ctx.send("Correct usage: `!!edittag tag_name new_tag_content`")
        #         return

        await self.db.execute(
            "UPDATE tags SET content = ? WHERE tag_id = ?", [new_content, name]
        )
        await self.db.commit()
        await ctx.reply(
            f"I have successfully updated **{name}**. \n\n **{name}**\n__{new_content}__"
        )

    @commands.command(name="deltag", usage="!!deltag [name]")
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def deltag(self, ctx, name):
        """Delete a tag"""
        if name is None:
            await ctx.send("Please tell me which tag to delete! `!!deltag tag_name`")
            return

        await self.db.execute("DELETE FROM tags WHERE tag_id = ?", [name])
        await self.db.commit()
        await ctx.reply(f"I have successfully deleted **{name}**.")

    @commands.command(name="tag", aliases=["t"])
    @commands.guild_only()
    async def tag(self, ctx, name=None):

        if name is None:
            await ctx.send(
                "Which tag do you want to use? You can use `!!tags` to see all available tags!"
            )
            return

        async with self.db.execute(
            "SELECT content FROM tags WHERE tag_id = ? LIMIT 20", [name]
        ) as cur:
            async for row in cur:
                await ctx.send(f"{row[0]}")

    @commands.command(name="taglist", aliases=["tags"])
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
                embed.add_field(
                    name="Showing all available tags", value=f" `{tags[0]}`"
                )
        await ctx.send(embed=embed)

    @commands.command(name="taghelp", aliases=["thelp"])
    @commands.guild_only()
    async def tag_help(self, ctx):
        await ctx.send(
            "```\n!!tag [name] - Prints out the message for the given tag (or !!t [name])\n!!maketag [name] [content...] - Creates a new tag\n!!deltag [name] - Deletes an existing tag\n!!edittag [name] [new_contant...] - Edits and existing tag\n!!taglist (or !!tags) - Shows a list of available tags\n\n**NOTE:** You must have the `Manage Messages` permission to use these commands.\n```"
        )


def setup(bot):
    bot.add_cog(Staff(bot))
