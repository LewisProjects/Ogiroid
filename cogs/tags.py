from __future__ import annotations

from typing import List, Literal, Optional

from disnake import Embed
from disnake.ext import commands
import disnake

from utils.CONSTANTS import tag_help
from utils.bot import OGIROID
from utils.exceptions import *
from utils.models import *
from utils.pagination import CreatePaginator
from utils.shortcuts import QuickEmb, manage_messages_perms


class TagManager:
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        self.session = self.bot.session
        self.names = set()

    async def startup(self):
        print("[TAGS] Loading tags...")
        tags = await self.all()
        aliases = await self.get_aliases()
        for tag in tags:
            self.names.add(tag.name)
        for alias in aliases:
            self.names.add(alias)
        print(f"Loaded {len(tags)} tags and {len(aliases)} aliases")
        print(self.names)

    async def exists(self, name, exception: TagException, should: bool) -> bool | TagException:
        if should:
            if name in self.names:
                return True # if it should exist and it does.
            raise exception
        else:
            if name not in self.names:
                return True # if it should not exist and it doesn't.
            raise exception

    async def create(self, name, content, owner):  # todo add owner or remove depending on what answer O get
        await self.exists(name, TagAlreadyExists, should=False)
        self.names.add(name)
        await self.db.execute("INSERT INTO tags (tag_id, content, owner, views, created_at) VALUES (?, ?, ?, 0, ?)",
                              [name, content, owner, int(time.time())], )
        await self.db.commit()

    async def get(self, name) -> Tag | TagNotFound:
        await self.exists(name, TagNotFound, should=True)
        async with self.db.execute("SELECT * FROM tags WHERE tag_id= ?", [name]) as cur:
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
        await self.exists(name, TagNotFound, should=True)
        self.names.remove(name)
        map(await self.get_aliases(name), self.names.remove)  # todo test this
        await self.remove_aliases(name)
        await self.db.execute("DELETE FROM tags WHERE tag_id = ?", [name])
        await self.db.commit()

    async def update(self, name, param, new_value):
        await self.exists(name, TagNotFound, should=True)
        # todo update aliases if param is name
        async with self.db.execute(f"UPDATE tags SET {param} = ? WHERE tag_id = ?", [new_value, name]):
            await self.db.commit()

    async def transfer(self, name, new_owner: int):
        await self.exists(name, TagNotFound, should=True)
        await self.update(name, "owner", new_owner)

    async def increment_views(self, name):
        await self.exists(name, TagNotFound, should=True)
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

    async def count(self) -> int:
        async with self.db.execute("SELECT COUNT(*) FROM tags") as cur:
            return int(tuple(await cur.fetchone())[0])

    async def add_alias(self, name, alias):
        await self.exists(name, TagNotFound, should=True)
        if alias in (await self.get_aliases(name)):
            raise AliasAlreadyExists
        await self.db.execute("INSERT INTO tag_relations (tag_id, alias) VALUES (?, ?)", [name, alias])
        await self.db.commit()

    async def remove_alias(self, name, alias):
        await self.exists(name, TagNotFound, should=True)
        if alias not in (await self.get_aliases(name)):
            raise AliasNotFound
        await self.db.execute("DELETE FROM tag_relations WHERE tag_id = ? AND alias = ?", [name, alias])
        await self.db.commit()

    async def remove_aliases(self, name):
        await self.exists(name, TagNotFound, should=True)
        await self.db.execute("DELETE FROM tag_relations WHERE tag_id = ?", [name])
        await self.db.commit()

    async def get_aliases(self, name: Optional = None) -> List[str] | TagNotFound:
        if not name:
            async with self.db.execute("SELECT * FROM tag_relations") as cur:
                content = (await cur.fetchall())
                if content is None:
                    return []
                return [row[1] for row in content]
        await self.exists(name, TagNotFound, should=True)
        async with self.db.execute("SELECT * FROM tag_relations WHERE tag_id = ?", [name]) as cur:
            content = (await cur.fetchall())
            if content is None:
                return []
        return [alias for tag_id, alias in list(set(content))]


class Tags(commands.Cog, name="Tags"):
    """Everything Tag related"""

    def __init__(self, bot: OGIROID):
        self.tags: TagManager = None
        self.bot: OGIROID = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.tags: TagManager = TagManager(self.bot, self.bot.db)
        await self.tags.startup()

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
    # @commands.has_permissions(manage_messages=True)
    async def edittag(self, inter, name, *, content):
        try:
            if (inter.author.id != (await self.tags.get(name)).owner) and not manage_messages_perms(inter):
                return await QuickEmb(inter, "You do not have permission to edit this tag").error().send()
            await self.tags.update(name, "content", content)
            await QuickEmb(inter,
                           f"I have successfully updated **{name}**. \n\n **{name}**\n__{content}__").success().send()
        except TagNotFound:
            return await QuickEmb(inter, f"tag {name} does not exist").error().send()

    @commands.slash_command(name="transfertag", description="Transfers the tag's owner")
    @commands.guild_only()
    async def transfertag(self, inter, name, new_owner: disnake.Member):
        try:
            if new_owner.bot:
                return await QuickEmb(inter, "You can't transfer a tag to a bot!").error().send()
            elif (inter.author.id != (await self.tags.get(name)).owner) and not manage_messages_perms(inter):
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
            return (await QuickEmb(inter,
                                   f"You have now claimed this tag because the previous owner of the tag is no longer in {inter.guild.name}", ).success().send())
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
            emb.add_field(name="Aliases", value=', '.join(tag for tag in (await self.tags.get_aliases(name))))
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
            return await QuickEmb(ctx, "wait for the bot to load").error().send()
        if tag_count == 0:
            return await QuickEmb(ctx, "There are no tags").error().send()

        tags = await self.tags.all(limit=0)
        tag_embs = []
        nested_tags = [[]]
        nested_count = 0
        tag_content_count = 0
        for tag in tags:
            # print(f'{tag.name}' + '      ' + f'{(len(tag.content) + tag_content_count) <= 1000}' + '     ' + str(tag_content_count + len(tag.content)))
            if (len(tag.content) + tag_content_count) <= 1989 and len(tag.content) <= 500:
                tag_content_count += len(tag.content)
                if isinstance(nested_tags[nested_count], Tag):
                    nested_count += 1
                    nested_tags.append([])
                nested_tags[nested_count].append(tag)
            else:
                tag_content_count = 0
                nested_tags.append(tag)
                nested_count += 1

        for tag_list in nested_tags:
            if not tag_list:
                continue

            if isinstance(tag_list, list):
                emb = Embed(color=self.bot.config.colors.invis, description="")
                for tag in tag_list:
                    emb.add_field(name=f"**{tag.name}**", value=tag.content)

                tag_embs.append(emb)
            elif isinstance(tag_list, Tag):
                emb = Embed(color=self.bot.config.colors.invis, description="")
                emb.title = f"**{tag_list.name}**"
                emb.description = tag_list.content
                tag_embs.append(emb)

        tag_embs.append(Embed(color=self.bot.config.colors.invis, description="The end ;D"))
        start_emb = Embed(title="Tags", color=self.bot.config.colors.invis)
        start_emb.description = f"There are currently {tag_count:,d} tags, use the arrows below to navigate through them"
        tag_embs.insert(0, start_emb)
        await ctx.send(embed=tag_embs[0], view=CreatePaginator(tag_embs, ctx.author.id))

    # add alias to tag command
    @commands.slash_command(name="tagalias-add", description="Adds an alias to a tag")
    @commands.guild_only()
    async def add_alias(self, inter, name, alias):
        try:
            if not inter.author.id == (await self.tags.get(name)).owner and not manage_messages_perms(inter):
                return await QuickEmb(inter, "You must be the owner of the tag to delete it!").error().send()
            await self.tags.add_alias(name, alias)
            await inter.send(f"I have successfully added **{alias}** as an alias for **{name}**")
        except TagNotFound:
            return await QuickEmb(inter, f"tag {name} does not exist").error().send()
        except AliasAlreadyExists:
            return await QuickEmb(inter, f"tag {alias} already exists").error().send()

    @commands.slash_command(name="tagalias-remove", description="Removes an alias from a tag")
    @commands.guild_only()
    async def remove_alias(self, inter, name, alias):
        try:
            if not inter.author.id == (await self.tags.get(name)).owner and not manage_messages_perms(inter):
                return await QuickEmb(inter, "You must be the owner of the tag to delete it!").error().send()
            await self.tags.remove_alias(name, alias)
            await inter.send(f"I have successfully removed **{alias}** from **{name}**")
        except TagNotFound:
            return await QuickEmb(inter, f"tag {name} does not exist").error().send()
        except AliasNotFound:
            return await QuickEmb(inter, f"alias {alias} does not exist").error().send()

    @commands.slash_command(name="taghelp", description="Help for the tag system")
    @commands.guild_only()
    async def tag_help(self, ctx):
        emb = Embed(title="Tag Help", color=self.bot.config.colors.invis)
        general_cmds = ''
        owner_cmds = ''

        for cmd, desc in tag_help['public'].items():
            general_cmds += f"**/{cmd}** *~~* {desc}\n\t"
        for cmd, desc in tag_help['owner_only'].items():
            owner_cmds += f"**/{cmd}** *~~* {desc} (only usable by the tag's owner)\n"

        emb.add_field(name=f"General commands", value=general_cmds + '\n\n', inline=False)
        emb.add_field(name=f"Owner only commands", value=owner_cmds, inline=False)
        emb.set_footer(text="Tag system made by @JasonLovesDoggo & @FreebieII",
                       icon_url=self.bot.user.display_avatar.url)
        await ctx.send(embed=emb)


def setup(bot):
    bot.add_cog(Tags(bot))

# todo when you delete a tag it should also delete all aliases
# todo make a rename tag command and an alias command
# todo cache the tags
# todo go through all self.exists() calls and see if they are called more then once
