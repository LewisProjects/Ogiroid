from __future__ import annotations

import re
from typing import List, Literal, Optional

from disnake import Embed
from disnake.ext import commands
import disnake

from utils.CONSTANTS import tag_help
from utils.bot import OGIROID
from utils.exceptions import *
from utils.models import *
from utils.pagination import CreatePaginator
from utils.shortcuts import QuickEmb, manage_messages_perms, errorEmb

""" note to any future contributors:
the self.exists() calls are very carefully used.
if you add a call to ANY of the functions in TagManager MAKE SURE it's called once
"""


class TagManager:
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        self.session = self.bot.session
        self.names = {"tags": [], "aliases": []}

    async def startup(self):
        await self.bot.wait_until_ready()
        print("[TAGS] Loading tags...")
        try:
            tags = await self.all()
            aliases = await self.get_aliases()
            for tag in tags:
                self.names["tags"].append(tag.name)
            for alias in aliases:
                self.names["aliases"].append(alias)
            print(f"Loaded {len(tags)} tags and {len(aliases)} aliases")
        except TagsNotFound:
            print("[TAGS] No tags found")

    async def exists(self, name, exception: TagException, should: bool) -> bool | TagException:
        full_list = self.names["tags"] + (self.names["aliases"])
        name = name.casefold()
        if should:
            if name in full_list:
                return True
            raise exception
        else:
            if name not in full_list:
                return True
            raise exception

    async def create(self, name, content, owner):
        await self.exists(name, TagAlreadyExists, should=False)
        self.names["tags"].append(name)
        await self.db.execute(
            "INSERT INTO tags (tag_id, content, owner, views, created_at) VALUES (?, ?, ?, 0, ?)",
            [name, content, owner, int(time.time())],
        )
        await self.db.commit()

    async def get(self, name) -> Tag | TagNotFound:
        await self.exists(name, TagNotFound, should=True)
        name = await self.get_name(name)
        async with self.db.execute("SELECT * FROM tags WHERE tag_id= ?", [name]) as cur:
            async for row in cur:
                return Tag(*row)

    async def all(self, orderby: Literal["views", "created_at"] = "views", limit=10) -> List[Tag]:
        tags = []
        async with self.db.execute(f"SELECT * FROM tags ORDER BY {orderby} DESC{f' LIMIT {limit}' if limit > 1 else ''}") as cur:
            async for row in cur:
                tags.append(Tag(*row))
        if len(tags) == 0:
            raise TagsNotFound
        return tags

    async def delete(self, name):
        await self.exists(name, TagNotFound, should=True)
        name = await self.get_name(name)
        for tag in await self.get_aliases(name):
            self.names["aliases"].remove(tag)
        await self.remove_aliases(name)
        self.names["tags"].remove(name)
        await self.db.execute("DELETE FROM tags WHERE tag_id = ?", [name])
        await self.db.commit()

    async def update(self, name, param, new_value):
        async with self.db.execute(f"UPDATE tags SET {param} = ? WHERE tag_id = ?", [new_value, name]):
            await self.db.commit()

    async def rename(self, name, new_name):
        await self.exists(name, TagNotFound, should=True)  # if the tag doesn't exist, it will raise TagNotFound
        await self.exists(
            new_name, TagAlreadyExists, should=False
        )  # if new tag's name already exists, it will raise TagAlreadyExists
        name = await self.get_name(name)
        await self.update(name, "tag_id", new_name)
        async with self.db.execute(f"UPDATE tag_relations SET tag_id = ? WHERE tag_id = ?", [new_name, name]):
            await self.db.commit()
        self.names["tags"].append(new_name)
        self.names["tags"].remove(name)

    async def transfer(self, name, new_owner: int):
        await self.exists(name, TagNotFound, should=True)
        name = await self.get_name(name)
        await self.update(name, "owner", new_owner)

    async def increment_views(self, name, tag: Tag = None):
        name = await self.get_name(name)
        if tag:
            current_views = tag.views
        else:
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
            f"SELECT tag_id, views FROM tags WHERE owner = {owner} ORDER BY {orderby} DESC LIMIT {limit}"
        ) as cur:
            async for row in cur:
                tags.append(Tag(*row))
        if len(tags) == 0:
            raise TagsNotFound
        return tags

    async def count(self) -> int:
        async with self.db.execute("SELECT COUNT(*) FROM tags") as cur:
            return int(tuple(await cur.fetchone())[0])

    async def get_name(self, name_or_alias):
        # await self.exists(name_or_alias, TagNotFound, should=True)
        if name_or_alias in self.names["tags"]:
            return name_or_alias  # it's  a tag
        async with self.db.execute("SELECT tag_id FROM tag_relations WHERE alias = ?", [name_or_alias]) as cur:
            async for row in cur:  # it's an alias
                return row[0]

    async def add_alias(self, name, alias):
        name = await self.get_name(name)
        await self.exists(name, TagNotFound, should=True)
        if alias in (await self.get_aliases(name)):
            raise AliasAlreadyExists
        self.names["aliases"].append(alias)
        await self.db.execute("INSERT INTO tag_relations (tag_id, alias) VALUES (?, ?)", [name, alias])
        await self.db.commit()

    async def remove_alias(self, name, alias):
        await self.exists(name, TagNotFound, should=True)
        name = await self.get_name(name)
        if alias not in (await self.get_aliases(name)):
            raise AliasNotFound
        await self.db.execute("DELETE FROM tag_relations WHERE tag_id = ? AND alias = ?", [name, alias])
        await self.db.commit()

    async def remove_aliases(self, name):
        await self.exists(name, TagNotFound, should=True)
        name = await self.get_name(name)
        await self.db.execute("DELETE FROM tag_relations WHERE tag_id = ?", [name])
        await self.db.commit()

    async def get_aliases(self, name: Optional = None) -> List[str] | TagNotFound:
        if not name:
            async with self.db.execute("SELECT * FROM tag_relations") as cur:
                content = await cur.fetchall()
                if content is None:
                    return []
                return [row[1] for row in content]
        await self.exists(name, TagNotFound, should=True)
        name = await self.get_name(name)
        async with self.db.execute("SELECT * FROM tag_relations WHERE tag_id = ?", [name]) as cur:
            content = await cur.fetchall()
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

    @staticmethod
    async def valid_name(name) -> bool:
        if bool(re.match(r"[a-z0-9_ -]+$", name)):
            if len(name) >= 25:
                return False
            return True
        return False

    @property
    def db(self):
        return self.bot.db

    @commands.slash_command(hidden=True)
    @commands.guild_only()
    async def tag(self, inter):
        pass

    @tag.sub_command(name="get", description="Gets you the tags value")
    @commands.guild_only()
    async def get(self, inter, name: str):
        name = name.casefold()
        try:
            tag = await self.tags.get(name)
            await self.tags.increment_views(name, tag)
            owner = self.bot.get_user(tag.owner)
            emb = Embed(color=disnake.Color.random(seed=hash(tag.name)), title=f"{tag.name}")
            emb.set_footer(text=f'{f"Tag owned by {owner.display_name}" if owner else ""}    -    Views: {tag.views + 1}')
            emb.description = tag.content
            await inter.send(embed=emb)
        except TagNotFound:
            await errorEmb(inter, f"tag {name} does not exist")

    @tag.sub_command(name="create", description="Creates a tag")
    @commands.guild_only()
    async def create(self, inter, name, *, content: str = commands.Param(le=1900)):
        name = name.casefold()
        if len(content) >= 1900:
            return await errorEmb(inter, "The tag's content must be under 1900 chars")
        elif not await self.valid_name(name):
            return (
                await QuickEmb(
                    inter,
                    "The tag's name must be under 26 chars & only contain numbers, lowercase letters, underscores or dashes",
                )
                .error()
                .send()
            )
        try:
            await self.tags.create(name, content, inter.author.id)
            return await QuickEmb(inter, f"I have successfully made **{name}**. To view it do /tag get {name}").success().send()
        except TagAlreadyExists:
            return await errorEmb(inter, f"tag {name} already exists")

    @tag.sub_command(name="edit", description="Edits the tag")
    @commands.guild_only()
    async def edit(self, inter, name, *, content: str = commands.Param(le=1900)):
        name = name.casefold()
        try:
            if (inter.author.id != (await self.tags.get(name)).owner) and not manage_messages_perms(inter):
                return await errorEmb(inter, "You do not have permission to edit this tag")
            if len(content) > 900:
                return await errorEmb(inter, "Reason must be under 900 chars")
            await self.tags.update(name, "content", content)
            await QuickEmb(
                inter, f"I have successfully updated **{name}**.\n\nuse /tag get {name} to access it."
            ).success().send()
        except TagNotFound:
            return await errorEmb(inter, f"tag {name} does not exist")

    @tag.sub_command(name="transfer", description="Transfers the tag's owner")
    @commands.guild_only()
    async def transfer(self, inter, name, new_owner: disnake.Member):
        try:
            name = name.casefold()
            if new_owner.bot:
                return await errorEmb(inter, "You can't transfer a tag to a bot!")
            elif (inter.author.id != (await self.tags.get(name)).owner) and not manage_messages_perms(inter):
                return await errorEmb(inter, "You must be the owner of the tag to transfer it!")
            await self.tags.transfer(name, new_owner.id)
            await QuickEmb(inter, f"I have successfully transferred **{name}** to {new_owner.display_name}").success().send()
        except TagNotFound:
            return await errorEmb(inter, f"tag {name} does not exist")

    @tag.sub_command(name="claim", description="Claims ownership of the tag if the owner isn't in the guild")
    @commands.guild_only()
    async def claim(self, inter, name):
        try:
            name = name.casefold()
            if (await self.tags.get(name)).owner == inter.author.id:
                return await errorEmb(inter, "You already own this tag!")
            elif inter.author.guild_permissions.manage_messages or inter.author.guild_permissions.administrator:
                await self.tags.transfer(name, inter.author.id)
                return await QuickEmb(inter, f"I have transferred **{name}** to you").success().send()
            elif (await self.tags.get(name)).owner in [member.id for member in inter.guild.members]:
                return await errorEmb(inter, "The owner of this tag is still in this guild!")
            await self.tags.transfer(name, inter.author.id)
            return (
                await QuickEmb(
                    inter,
                    f"You have now claimed this tag because the previous owner of the tag is no longer in {inter.guild.name}",
                )
                .success()
                .send()
            )
        except TagNotFound:
            return await errorEmb(inter, f"tag {name} does not exist")

    @tag.sub_command(name="delete", description="Deletes the tag")
    @commands.guild_only()
    async def deltag(self, inter, name):
        try:
            name = name.casefold()
            if not inter.author.id == (await self.tags.get(name)).owner and not manage_messages_perms(inter):
                return await errorEmb(inter, "You must be the owner of the tag to delete it!")
            await self.tags.delete(name)
            await QuickEmb(inter, f"I have successfully deleted **{name}**.").success().send()
        except TagNotFound:
            return await errorEmb(inter, f"tag {name} does not exist")

    @tag.sub_command(name="info", description="Gives you the tags info")
    @commands.guild_only()
    async def info(self, inter, name):
        name = name.casefold()
        try:
            tag = await self.tags.get(name)
            await self.tags.increment_views(name, tag)
            owner = self.bot.get_user(tag.owner)
            emb = Embed(color=disnake.Color.random(seed=hash(tag.name)))  # hash -> seed makes the color the same for the tag
            emb.add_field(name="Name", value=tag.name)
            emb.add_field(name="Owner", value=owner.mention)
            if await self.tags.get_aliases(name):
                emb.add_field(name="Aliases", value=", ".join(tag for tag in (await self.tags.get_aliases(name))))
            emb.add_field(name="Created At", value=f"<t:{tag.created_at}:R>")
            emb.add_field(name="Times Called", value=abs(tag.views))
            await inter.send(embed=emb)
        except TagNotFound:
            return await errorEmb(inter, f"tag {name} does not exist")

    @tag.sub_command(name="list", description="Lists tags")
    @commands.guild_only()
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def list_tags(self, ctx):
        try:
            tag_count = await self.tags.count()
        except AttributeError:
            return await errorEmb(ctx, "wait for the bot to load")
        if tag_count == 0:
            return await errorEmb(ctx, "There are no tags")

        tags = await self.tags.all(limit=0)
        tag_embs = []
        nested_tags = [[]]
        nested_count = 0
        tag_content_count = 0
        for tag in tags:
            if (len(tag.content) + tag_content_count) <= 1989 :
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
        start_emb.description = (
            f"There are currently {tag_count:,d} tag{'s' if tag_count > 1 else ''}, use the arrows below to navigate through them"
        )
        tag_embs.insert(0, start_emb)
        await ctx.send(embed=tag_embs[0], view=CreatePaginator(tag_embs, ctx.author.id))

    @tag.sub_command(name="rename", description="Renames a tag")
    @commands.guild_only()
    async def rename(self, inter, name, new_name):
        try:
            name = name.casefold()
            new_name = new_name.casefold()
            if not inter.author.id == (await self.tags.get(name)).owner and not manage_messages_perms(inter):
                return await errorEmb(inter, "You must be the owner of the tag to rename it!")
            elif not await self.valid_name(name):
                return (
                    await QuickEmb(
                        inter, "The tag's name must be only contain numbers, lowercase letters, spaces, underscores or dashes"
                    )
                    .error()
                    .send()
                )
            await self.tags.rename(name, new_name)
            await QuickEmb(inter, f"I have successfully renamed **{name}** to **{new_name}**.").success().send()
        except TagNotFound:
            return await errorEmb(inter, f"tag {name} does not exist")

    @tag.sub_command(name="help", description="Help for the tag system")
    @commands.guild_only()
    async def help(self, ctx):
        emb = Embed(title="Tag Help", color=self.bot.config.colors.invis)
        general_cmds = ""
        owner_cmds = ""

        for cmd, desc in tag_help["public"].items():
            general_cmds += f"**/{cmd}** *~~* {desc}\n\t"
        for cmd, desc in tag_help["owner_only"].items():
            owner_cmds += f"**/{cmd}** *~~* {desc} (only usable by the tag's owner)\n"

        emb.add_field(name=f"General commands", value=general_cmds + "\n\n", inline=False)
        emb.add_field(name=f"Owner only commands", value=owner_cmds, inline=False)
        emb.set_footer(text="Tag system made by @JasonLovesDoggo & @FreebieII", icon_url=self.bot.user.display_avatar.url)
        await ctx.send(embed=emb)

    @tag.sub_command_group(name="alias", description="Aliases a tag", hidden=True)
    @commands.guild_only()
    async def alias(self, inter):
        pass

    @alias.sub_command(name="add", description="Adds an alias to a tag")
    @commands.guild_only()
    async def add_alias(self, inter, name, alias):
        try:
            name = name.casefold()
            alias = alias.casefold()
            if not inter.author.id == (await self.tags.get(name)).owner and not manage_messages_perms(inter):
                return await errorEmb(inter, "You must be the owner of the tag to delete it!")
            elif not await self.valid_name(name):
                return (
                    await QuickEmb(
                        inter, "The tag's name must be only contain numbers, lowercase letters, spaces, underscores or dashes"
                    )
                    .error()
                    .send()
                )
            await self.tags.add_alias(name, alias)
            await QuickEmb(inter, f"I have successfully added **{alias}** as an alias for **{name}**").success().send()
        except TagNotFound:
            return await errorEmb(inter, f"tag {name} does not exist")
        except AliasAlreadyExists:
            return await errorEmb(inter, f"tag {alias} already exists")

    @alias.sub_command(name="remove", description="Removes an alias from a tag")
    @commands.guild_only()
    async def remove_alias(self, inter, name, alias):
        try:
            name = name.casefold()
            alias = alias.casefold()
            if name == alias:
                return await errorEmb(inter, "You can't remove the tag's name from itself")
            elif not inter.author.id == (await self.tags.get(name)).owner and not manage_messages_perms(inter):
                return await errorEmb(inter, "You must be the owner of the tag to delete it!")
            await self.tags.remove_alias(name, alias)
            await QuickEmb(inter, f"I have successfully removed **{alias}** from **{name}**").success().send()
        except TagNotFound:
            return await errorEmb(inter, f"tag {name} does not exist")
        except AliasNotFound:
            return await errorEmb(inter, f"alias {alias} does not exist")


def setup(bot):
    bot.add_cog(Tags(bot))


# todo go through all self.exists() calls and see if they are called more then once
