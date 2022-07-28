from __future__ import annotations


from typing import List, Literal

from disnake import Embed
from disnake.ext import commands
import disnake

from utils.bot import OGIROID
from utils.exceptions import *
from utils.models import *
from utils.pagination import CreatePaginator
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
        await self.db.execute("INSERT INTO tags (tag_id, content, owner, views, created_at) VALUES (?, ?, ?, 0, ?)",
                              [name, content, owner, int(time.time())], )
        await self.db.commit()

    async def get(self, name) -> Tag | TagNotFound:
        if not await self.exists(name):
            raise TagNotFound
        async with self.db.execute("SELECT * FROM tags WHERE tag_id = ?", [name]) as cur:
            async for row in cur:
                return Tag(*row)

    async def all(self, orderby: Literal["views", "created_at"] = "views", limit=10) -> List[Tag]:
        tags = []
        async with self.db.execute(
                f"SELECT * FROM tags ORDER BY {orderby} DESC{f' LIMIT {limit}' if limit > 1 else ''}") as cur:
            async for row in cur:
                tags.append(Tag(*row))
        if len(tags) == 0:
            raise TagsNotFound
        return tags

    async def delete(self, name):
        if not await self.exists(name):
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
        current_views = (await self.get(name)).views
        await self.update(name, "views", (current_views + 1))

    async def get_top(self, limit=10):
        tags = []
        async with self.db.execute(f"SELECT tag_id, views FROM tags ORDER BY views DESC LIMIT {limit}") as cur:
            async for row in cur:
                tags.append(Tag(*row))
        if len(tags) == 0:
            raise TagsNotFound
        return tags

    async def get_tags_by_owner(self, owner: int, limit=10, orderby: Literal["views", "created_at"] = "views"):
        tags = []
        async with self.db.execute(
                f"SELECT tag_id, views FROM tags WHERE owner = {owner} ORDER BY {orderby} DESC LIMIT {limit}") as cur:
            async for row in cur:
                tags.append(Tag(*row))
        if len(tags) == 0:
            raise TagsNotFound
        return tags

    # get amount of tags in database
    async def count(self) -> int:
        async with self.db.execute("SELECT COUNT(*) FROM tags") as cur:
            return int(tuple(await cur.fetchone())[0])


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
        if len(content) >= 1980:
            return await QuickEmb(inter, "The tag's content must be under 1980 chars").error().send()
        elif len(name) >= 25:
            return await QuickEmb(inter, "The tag's name must be under 25 chars").error().send()
        try:  # todo add a check if the user is blacklisted
            await self.tags.create(name, content, inter.author.id)
            await inter.send(f"I have successfully made **{name}**. To view it do /tag {name}")
        except TagAlreadyExists:
            return await QuickEmb(inter, f"tag {name} already exists").error().send()

    @commands.slash_command(name="edittag", description="Edits the tag")
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def edittag(self, inter, name, *, content):
        try:
            if (inter.author.id != (await self.tags.get(name)).owner) and not manage_messages_perms(
                    inter):
                return await QuickEmb(inter, "You do not have permission to edit this tag").error().send()
            await self.tags.update(name, "content", content)
            await QuickEmb(inter,
                           f"I have successfully updated **{name}**. \n\n **{name}**\n__{content}__").success().send()
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
                    inter):
                return await QuickEmb(inter, "You must be the owner of the tag to transfer it!").error().send()
            await self.tags.transfer(name, new_owner.id)
            await inter.send(f"I have successfully transferred **{name}** to {new_owner.mention}",
                             allowed_mentions=disnake.AllowedMentions(everyone=False, users=False), )
        except TagNotFound:
            return await QuickEmb(inter, f"tag {name} does not exist").error().send()

    @commands.slash_command(name="claimtag", description="Claims ownership of the tag if the owner isn't in the guild")
    @commands.guild_only()
    async def claimtag(self, inter, name):
        try:
            if (await self.tags.get(name)).owner == inter.author.id:
                return await QuickEmb(inter, "You already own this tag!").error().send()
            elif inter.author.guild_permissions.manage_messages or inter.author.guild_permissions.administrator:
                await self.tags.transfer(name, inter.author.id)
                return await QuickEmb(inter, f"I have transferred **{name}** to you").success().send()
            elif (await self.tags.get(name)).owner in [member.id for member in inter.guild.members]:
                return await QuickEmb(inter, "The owner of this tag is still in this guild!").error().send()
            await self.tags.transfer(name, inter.author.id)
            return await QuickEmb(inter,
                                  f"You have now claimed this tag because the previous owner of the tag is no longer in {inter.guild.name}").success().send()
        except TagNotFound:
            return await QuickEmb(inter, f"tag {name} does not exist").error().send()

    @commands.slash_command(name="deltag", description="Deletes the tag.")
    @commands.guild_only()
    # @commands.has_permissions(manage_messages=True)
    async def deltag(self, inter, name):
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
        try:
            await self.tags.increment_views(name)
            tag = await self.tags.get(name)
            owner = self.bot.get_user(tag.owner)
            emb = Embed(
                color=disnake.Color.random(seed=hash(tag.name)))  # hash -> seed makes the color the same for the tag
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
        try:
            tag_count = await self.tags.count()
        except AttributeError:
            return await QuickEmb(ctx, 'wait for the bot to load').error().send()
        if tag_count == 0:
            return await QuickEmb(ctx, "There are no tags").error().send()

        tags = await self.tags.all(limit=0)
        tag_embs = []
        nested_tags = [[]]
        nested_count = 0
        tag_content_count = 0
        for tag in tags:
            #print(f'{tag.name}' + '      ' + f'{(len(tag.content) + tag_content_count) <= 1000}' + '     ' + str(tag_content_count + len(tag.content)))
            if (len(tag.content) + tag_content_count) <= 1989 and len(tag.content) <= 500:
                #print('adding')
                tag_content_count += len(tag.content)
                if isinstance(nested_tags[nested_count], Tag):
                    nested_count += 1
                    nested_tags.append([])
                nested_tags[nested_count].append(tag)
            else:
                #print('new')
                tag_content_count = 0
                nested_tags.append(tag)
                nested_count += 1

        for tag_list in nested_tags:
            if not tag_list:
                continue

            if isinstance(tag_list, list):
                emb = Embed(color=self.bot.config.colors.invis, description='')
                for tag in tag_list:
                    emb.add_field(name=f'**{tag.name}**', value=tag.content)

                tag_embs.append(emb)
            elif isinstance(tag_list, Tag):
                emb = Embed(color=self.bot.config.colors.invis, description='')
                emb.title = f'**{tag_list.name}**'
                emb.description = tag_list.content
                tag_embs.append(emb)
            else:
                print(tag_list)

        tag_embs.append(Embed(color=self.bot.config.colors.invis, description='The end ;D'))
        start_emb = Embed(title="Tags", color=self.bot.config.colors.invis)
        start_emb.description = f"There are currently {tag_count:,d} tags, use the arrows below to navigate through them"
        tag_embs.insert(0, start_emb)
        await ctx.send(embed=tag_embs[0], view=CreatePaginator(tag_embs, ctx.author.id))

    @commands.slash_command(name="taghelp", description="Help for the tag system")
    @commands.guild_only()
    async def tag_help(self, ctx):
        await ctx.send(  # todo fix this
            "```\n/tag [name] - Prints out the message for the given tag (or /t [name])\n/maketag [name] [content...] - Creates a new tag\n/deltag [name] - Deletes an existing tag\n/edittag [name] [new_contant...] - Edits and existing tag\n/taglist (or !!tags) - Shows a list of available tags\n\n**NOTE:** You must have the `Manage Messages` permission to use these commands.\n```")


def setup(bot):
    bot.add_cog(Tags(bot))

# todo make a rename tag command
