from __future__ import annotations

import re

import disnake
from disnake import Embed, ApplicationCommandInteraction
from disnake.ext import commands

from utils.CONSTANTS import tag_help
from utils.DBhandlers import TagManager
from utils.bot import OGIROID
from utils.exceptions import *
from utils.models import *
from utils.pagination import CreatePaginator
from utils.shortcuts import QuickEmb, manage_messages_perms, errorEmb


class Tags(commands.Cog, name="Tags"):
    """Everything Tag related"""

    def __init__(self, bot: OGIROID):
        self.tags: TagManager = None
        self.bot: OGIROID = bot

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.bot.ready_:
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

    @commands.slash_command()
    @commands.guild_only()
    async def tag(self, inter):
        pass

    @commands.slash_command(name="t", aliases=["tg"], description="Get a tag", hidden=True)
    async def get_tag(self, inter: ApplicationCommandInteraction, *, name: str, embeded: bool = False):
        return await self.get(inter, name, embeded)

    @tag.sub_command(name="get", description="Gets you the tags value")
    @commands.guild_only()
    async def get(self, inter, name: str, embeded: bool = False):
        name = name.casefold()
        try:
            tag = await self.tags.get(name)
            await self.tags.increment_views(name)
            if embeded:
                owner = self.bot.get_user(tag.owner)
                emb = Embed(color=disnake.Color.random(seed=hash(tag.name)), title=f"{tag.name}")
                emb.set_footer(text=f'{f"Tag owned by {owner.display_name}" if owner else ""}    -    Views: {tag.views + 1}')
                emb.description = tag.content
                await inter.send(embed=emb)
            else:
                content = str(tag.content)
                await inter.send(content, allowed_mentions=disnake.AllowedMentions.none())
        except TagNotFound:
            await errorEmb(inter, f"tag {name} does not exist")

    @tag.sub_command(name="random", description="Gets a random tag")
    async def random(self, inter):
        tag = await self.tags.random()
        return await self.get(inter, tag)

    @tag.sub_command(name="create", description="Creates a tag")
    @commands.guild_only()
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def create(self, inter, name, *, content: str = commands.Param(le=1900)):
        name = name.casefold()
        await self.tags.exists(name, TagAlreadyExists, should=False)
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
    @commands.cooldown(1, 5, commands.BucketType.user)
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
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def transfer(self, inter, name, new_owner: disnake.Member):
        try:
            name = name.casefold()
            await self.tags.exists(name, TagNotFound, should=True)
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
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def claim(self, inter, name):
        try:
            name = name.casefold()
            await self.tags.exists(name, TagNotFound, should=True)
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
    @commands.cooldown(1, 180, commands.BucketType.user)
    async def deltag(self, inter, name):
        try:
            name = name.casefold()
            await self.exists(name, TagNotFound, should=True)
            if not inter.author.id == (await self.tags.get(name)).owner and not manage_messages_perms(inter):
                return await errorEmb(inter, "You must be the owner of the tag to delete it!")
            await self.tags.delete(name)
            await QuickEmb(inter, f"I have successfully deleted **{name}**.").success().send()
        except TagNotFound:
            return await errorEmb(inter, f"tag {name} does not exist")

    @tag.sub_command(name="info", description="Gives you the tags info")
    @commands.guild_only()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def info(self, inter, name):
        name = name.casefold()
        await self.tags.exists(name, TagNotFound, should=True)
        try:
            tag = await self.tags.get(name)
            await self.tags.increment_views(name)
            owner = self.bot.get_user(tag.owner)
            emb = Embed(color=disnake.Color.random(seed=hash(tag.name)))  # hash -> seed makes the color the same for the tag
            emb.add_field(name="Name", value=tag.name)
            emb.add_field(name="Owner", value=owner.mention)
            aliases = await self.tags.get_aliases(name)
            if aliases:
                emb.add_field(name="Aliases", value=", ".join(tag for tag in aliases))
            emb.add_field(name="Created At", value=f"<t:{tag.created_at}:R>")
            emb.add_field(name="Times Called", value=abs(tag.views))
            await inter.send(embed=emb)
        except TagNotFound:
            return await errorEmb(inter, f"tag {name} does not exist")

    @tag.sub_command(name="list", description="Lists tags")
    @commands.guild_only()
    @commands.cooldown(1, 15, commands.BucketType.channel)
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
            if (len(tag.content) + tag_content_count) <= 1989:
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
            await self.tags.exists(name, TagNotFound, should=True)  # if the tag doesn't exist, it will raise TagNotFound
            await self.tags.exists(new_name, TagAlreadyExists, should=False)
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
        except TagAlreadyExists:
            return await errorEmb(inter, f"A tag with the name {new_name} already exists")

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
            await self.exists(name, TagNotFound, should=True)
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
        except AliasLimitReached:
            return await errorEmb(inter, "You can only have 10 aliases per tag")

    @alias.sub_command(name="remove", description="Removes an alias from a tag")
    @commands.guild_only()
    async def remove_alias(self, inter, name, alias):
        try:
            name = name.casefold()
            alias = alias.casefold()
            await self.tags.exists(name, TagNotFound, should=True)
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
