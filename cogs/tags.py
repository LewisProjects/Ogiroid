from __future__ import annotations

from typing import Set

from disnake import Embed
from disnake.ext import commands
import disnake

from utils.bot import OGIROID
from utils.exceptions import *
from utils.models import *
from utils.shortcuts import QuickEmb


class TagManager:
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        self.session = self.bot.session

    async def exists(self, name):
        async with self.db.execute("SELECT * FROM tags WHERE tag_id = ?", [name]) as cur:
            if await cur.fetchone() is not None:
                return True
            return False

    async def create(self, name, content, owner):  # todo add owner or remove depending on what answer O get
        if await self.exists(name):
            raise TagAlreadyExists
        await self.db.execute(
            "INSERT INTO tags (tag_id, content, owner, views, created_at) VALUES (?, ?, ?, 0, ?)",
            [name, content, owner, int(time.time())],
        )
        await self.db.commit()

    async def get(self, name) -> Tag | TagNotFound:
        if not await self.exists(name):
            raise TagNotFound
        async with self.db.execute("SELECT * FROM tags WHERE tag_id = ?", [name]) as cur:
            async for row in cur:
                return Tag(*row)

    async def get_all(self) -> Set[Tag]:
        tags = {}
        async with self.db.execute("SELECT * FROM tags") as cur:
            async for row in cur:
                print(*row)
                tags += Tag(*row)  # todo fix this
        return tags

    async def delete(self, name):
        if not self.exists(name):
            raise TagNotFound
        await self.db.execute("DELETE FROM tags WHERE tag_id = ?", [name])
        await self.db.commit()

    async def update(self, name, param, new_value):
        if not await self.exists(name):
            raise TagNotFound
        async with self.db.execute(f"UPDATE tags SET {param} = ? WHERE tag_id = ?", [new_value, name]):
            await self.db.commit()

    async def transfer(self, name, new_owner: int):
        if not await self.exists(name):
            raise TagNotFound
        await self.update(name, "owner", new_owner)

    async def increment_views(self, name):
        if not await self.exists(name):
            raise TagNotFound
        # increment a tag's views by one
        current_views = (await self.get(name)).views
        await self.update(name, "views", (current_views + 1))


def manage_messages_perms(inter):
    return inter.channel.permissions_for(inter.author).manage_messages


class Tags(commands.Cog, name="Tags"):
    """Everything Tag related"""

    def __init__(self, bot: OGIROID):
        self.tags: TagManager = None
        self.bot: OGIROID = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.tags: TagManager = TagManager(self.bot, self.bot.db)

    @property
    def db(self):
        return self.bot.db

    @commands.slash_command(name="maketag", description="Creates a tag")
    @commands.guild_only()
    # @commands.has_permissions(manage_messages=True)
    async def make_tag(self, inter, name, *, content):
        """Makes a new tag"""
        try:  # todo add a check if the user is blacklisted
            await self.tags.create(name, content, inter.author.id)
            await inter.send(f"I have successfully made **{name}**. To view it do /tag {name}")
        except TagAlreadyExists:
            return await QuickEmb(inter, f"tag {name} does not exist").error().send()

    @commands.slash_command(name="edittag", description="Edits the tag")
    @commands.guild_only()
    # @commands.has_permissions(manage_messages=True)
    async def edittag(self, inter, name, *, content):
        try:
            if (inter.author.id != (await self.tags.get(name)).owner) and not manage_messages_perms(
                inter
            ):  # todo test manage messages permission check
                return await QuickEmb(inter, "You do not have permission to edit this tag").error().send()
            await self.tags.update(name, "content", content)
            await QuickEmb(inter, f"I have successfully updated **{name}**. \n\n **{name}**\n__{content}__").success().send()
        except TagNotFound:
            return await QuickEmb(inter, f"tag {name} does not exist").error().send()

    @commands.slash_command(name="transfertag", description="Transfers the tag's owner")
    @commands.guild_only()
    # @commands.has_permissions(manage_messages=True)
    async def transfertag(self, inter, name, new_owner: disnake.Member):
        try:
            if new_owner.bot:
                return await QuickEmb(inter, "You can't transfer a tag to a bot!").error().send()
            elif (inter.author.id != (await self.tags.get(name)).owner) and not manage_messages_perms(
                inter
            ):  # todo test manage messages permission check
                return await QuickEmb(inter, "You must be the owner of the tag to transfer it!").error().send()
            await self.tags.transfer(name, new_owner.id)
            await inter.send(
                f"I have successfully transferred **{name}** to {new_owner.mention}",
                allowed_mentions=disnake.AllowedMentions(everyone=False, users=False),
            )
        except TagNotFound:
            return await QuickEmb(inter, f"tag {name} does not exist").error().send()

    @commands.slash_command(name="claimtag", description="Claims ownership of the tag if the owner isn't in the guild")
    @commands.guild_only()
    async def claimtag(self, inter, name):
        try:
            if (await self.tags.get(name)).owner == inter.author.id:
                return await QuickEmb(inter, "You already own this tag!").error().send()
            elif (await self.tags.get(name)).owner in [member.id for member in inter.guild.members]:
                return await QuickEmb(inter, "The owner of this tag is still in this guild!").error().send()
            await self.tags.transfer(name, inter.author.id)
            return await QuickEmb(inter, "You have now claimed this tag!").success().send()
        except TagNotFound:
            return await QuickEmb(inter, f"tag {name} does not exist").error().send()

    @commands.slash_command(name="deltag", description="Deletes the tag.")
    @commands.guild_only()
    # @commands.has_permissions(manage_messages=True)
    async def deltag(self, inter, name):
        if name is None:
            await inter.send("Please tell me which tag to delete! `/deltag tag_name`")
            return

        try:
            if not inter.author.id == (await self.tags.get(name)).owner and not manage_messages_perms(inter):
                return await QuickEmb(inter, "You must be the owner of the tag to delete it!").error().send()
            await self.tags.delete(name)
            await inter.send(f"I have successfully deleted **{name}**.")
        except TagNotFound:
            return await QuickEmb(inter, f"tag {name} does not exist").error().send()

    @commands.slash_command(name="taginfo", description="Gives you the tags info")
    @commands.guild_only()
    async def taginfo(self, inter, name):
        if name is None:
            return await QuickEmb(inter, "Please tell me which tag to view! `/tag tag_name`").error().send()
        try:
            await self.tags.increment_views(name)
            tag = await self.tags.get(name)
            owner = self.bot.get_user(tag.owner)
            emb = Embed(color=disnake.Color.random(seed=hash(tag.name)))  # hash -> seed makes the color the same for the tag
            emb.add_field(name="Name", value=tag.name)
            emb.add_field(name="Owner", value=owner.mention)
            emb.add_field(name="Created At", value=f"<t:{tag.created_at}:R>")
            emb.add_field(name="Times Called", value=abs(tag.views))
            await inter.send(embed=emb)
        except TagNotFound:
            return await QuickEmb(inter, f"tag {name} does not exist").error().send()

    @commands.slash_command(name="tag", description="Gives you the tags value")
    @commands.guild_only()
    async def tag(self, inter, name):
        if name is None:
            return (
                await QuickEmb(inter, "Which tag do you want to use? You can use `/tags` to see all available tags!")
                .error()
                .send()
            )

        try:
            await self.tags.increment_views(name)
            tag = await self.tags.get(name)
            await inter.send(f"**{name}**\n__{tag.content}__")
        except TagNotFound:
            await inter.send(f"tag {name} does not exist")

    @commands.slash_command(name="taglist", description="Lists tags")
    @commands.guild_only()
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def list_tags(self, ctx):  # todo fix this
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
        async with self.db.execute("SELECT * FROM tags LIMIT 1") as cur:
            async for tags in cur:
                embed.add_field(name="Showing all available tags", value=f" `{tags[0]}`")
        await ctx.send(embed=embed)

    @commands.slash_command(name="taghelp", description="Help for the tag system")
    @commands.guild_only()
    async def tag_help(self, ctx):
        await ctx.send(  # todo fix this
            "```\n/tag [name] - Prints out the message for the given tag (or /t [name])\n/maketag [name] [content...] - Creates a new tag\n/deltag [name] - Deletes an existing tag\n/edittag [name] [new_contant...] - Edits and existing tag\n/taglist (or !!tags) - Shows a list of available tags\n\n**NOTE:** You must have the `Manage Messages` permission to use these commands.\n```"
        )


def setup(bot):
    bot.add_cog(Tags(bot))


# todo tag steal command if the owner is gone
