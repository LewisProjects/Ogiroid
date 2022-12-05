import asyncio
import time
from typing import TYPE_CHECKING

import disnake
from disnake import Member, Embed, Option, OptionType
from disnake.ext import commands, tasks
from disnake.ext.commands import Cog

from utils import timeconversions
from utils.CONSTANTS import timings
from utils.DBhandlers import BlacklistHandler
from utils.models import BlacklistedUser
from utils.pagination import CreatePaginator
from utils.shortcuts import sucEmb, errorEmb, get_expiry, wait_until

if TYPE_CHECKING:
    from utils.bot import OGIROID


class Blacklist(Cog):
    def __init__(self, bot: "OGIROID"):
        self.bot = bot
        self.blacklist: BlacklistHandler = None
        self.del_que = []

    def get_user(self, user_id):
        return self.bot.get_user(user_id)

    async def run_at(self, dt, coro, _id):
        await wait_until(dt)
        self.del_que.remove(_id)
        await coro(_id)

    @tasks.loop(minutes=59)
    async def check_blacklist(self):
        await asyncio.sleep(5)  # ample time for other blacklist module to load
        for user in self.bot.blacklist.blacklist:
            await self.check_user_removal(user)

    async def check_user_removal(self, user: BlacklistedUser):
        if user.id in self.del_que:
            return  # already being removed
        elif user.is_expired():
            await self.blacklist.remove(user.id)
        elif int(time.time()) <= user.expires <= (int(time.time()) + timings.HOUR):
            self.del_que.append(user.id)
            await self.run_at(user.expires, self.blacklist.remove, user.id)

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.bot.ready_:
            await self.bot.wait_until_ready()
            self.blacklist: BlacklistHandler = self.bot.blacklist
            self.check_blacklist.start()

    @commands.slash_command(description="Blacklist base command", hidden=True)
    async def blacklist(self, inter):
        pass

    @commands.cooldown(1, 5, commands.BucketType.user)
    @blacklist.sub_command(name="info", description="Get info about a blacklisted user")
    async def blacklist_info(self, inter, user: Member):
        if not await self.blacklist.blacklisted(user.id):
            return await errorEmb(inter, f"{user.mention} is not in the blacklist")
        bl_user = await self.blacklist.get_user(user.id)
        embed = Embed(
            title=f"Blacklisted user: {user.name}",
            color=disnake.Color.random(seed=user.name),
        )
        embed.add_field(name="Reason", value=bl_user.reason, inline=False)
        embed.add_field(name="Expires", value=bl_user.get_expiry, inline=False)
        embed.add_field(name="Bot", value=bl_user.bot)
        embed.add_field(name="Tickets", value=bl_user.tickets)
        embed.add_field(name="Tags", value=bl_user.tags)
        await inter.send(embed=embed)

    @blacklist.sub_command_group(
        name="edit", description="Edit a user in the blacklist"
    )
    async def edit(self, inter):
        pass

    @commands.has_permissions(manage_messages=True)
    @edit.sub_command(
        name="flags", description="Edit the user's blacklist flags in the blacklist"
    )
    async def flags(self, inter, user: Member, bot: bool, tickets: bool, tags: bool):
        if not await self.blacklist.blacklisted(user.id):
            return await errorEmb(inter, f"{user.mention} is not in the blacklist")
        await self.blacklist.edit_flags(user.id, bot, tickets, tags)
        await sucEmb(
            inter,
            f"Edited {user.mention}'s blacklist flags to\nBot: {bot}, Tickets: {tickets}, Tags: {tags}",
        )

    @commands.has_permissions(manage_messages=True)
    @edit.sub_command(
        name="reason", description="Edit the user's blacklist reason in the blacklist"
    )
    async def reason(self, inter, user: Member, reason: str):
        if not await self.blacklist.blacklisted(user.id):
            return await errorEmb(inter, f"{user.mention} is not in the blacklist")
        await self.blacklist.edit_reason(user.id, reason)
        await sucEmb(
            inter,
            f"Edited {user.mention}'s reason in the blacklist to see the full reason use /blacklist info {user.mention}",
        )

    @commands.has_permissions(manage_messages=True)
    @edit.sub_command(
        name="expiry", description="Edit the user's blacklist expiry in the blacklist"
    )
    async def expiry(self, inter, user: Member, expires: str):
        if not await self.blacklist.blacklisted(user.id):
            return await errorEmb(inter, f"{user.mention} is not in the blacklist")
        expiry = int((await timeconversions.convert(expires)).dt.timestamp())
        await self.blacklist.edit_expiry(user.id, expiry)
        await sucEmb(
            inter,
            f"Edited the expiry of {user.mention}'s blacklist to expire {get_expiry(expiry)}",
        )
        await self.check_user_removal(await self.blacklist.get_user(user.id))

    @commands.has_permissions(manage_messages=True)
    @blacklist.sub_command(
        name="remove", description="Remove a user from the blacklist"
    )
    async def remove(self, inter, user: Member):
        if not await self.blacklist.blacklisted(user.id):
            return await errorEmb(inter, f"{user.mention} is not in the blacklist")
        await self.blacklist.remove(user.id)
        await sucEmb(
            inter, f"{user.mention} has been removed from blacklist", ephemeral=False
        )

    @commands.has_permissions(manage_messages=True)
    @blacklist.sub_command(
        name="add",
        description="Add a user to the blacklist",
        options=[
            Option(
                "user",
                description="User to blacklist",
                type=OptionType.user,
                required=True,
            ),
            Option(
                "bot",
                description="Whether to blacklist the user from using the entire bot",
                type=OptionType.boolean,
                required=True,
            ),
            Option(
                "tickets",
                description="Whether to blacklist the user from using tickets",
                type=OptionType.boolean,
                required=True,
            ),
            Option(
                "tags",
                description="Whether to blacklist the user from using tags",
                type=OptionType.boolean,
                required=True,
            ),
            Option(
                "expires",
                description="When the blacklist should expire (e.g. 1w, 5m, never)",
                type=OptionType.string,
                required=False,
            ),
            Option(
                "reason",
                description="Reason for blacklisting the user",
                type=OptionType.string,
                required=False,
            ),
        ],
    )
    async def blacklist_add(
        self,
        inter,
        user,
        bot,
        tickets,
        tags,
        reason="No Reason Specified",
        expires="never",
    ):
        if not any((bot, tickets, tags)):
            return await errorEmb(
                inter,
                "You can't blacklist a user without specifying either bot, tickets and/or tags",
            )
        elif len(reason) > 900:
            return await errorEmb(inter, "Reason must be under 900 chars")
        elif user.id == inter.author.id:
            return await errorEmb(inter, "You can't blacklist yourself")
        elif await self.blacklist.blacklisted(user.id):
            return await errorEmb(inter, f"{user.mention} is already in the blacklist")
        expires = (await timeconversions.convert(expires)).dt.timestamp()
        await self.blacklist.add(user.id, reason, bot, tickets, tags, expires)
        await sucEmb(
            inter,
            f"{user.mention} added to blacklist\nthe user's blacklist will {f'expire on <t:{int(expires)}:R>' if str(expires) != str(9999999999) else 'never expire'}",
            ephemeral=False,
        )
        await self.check_user_removal(await self.blacklist.get_user(user.id))

    @commands.cooldown(1, 30, commands.BucketType.user)
    @blacklist.sub_command(name="list", description="List all blacklisted users")
    async def blacklist_list(self, inter):
        try:
            blacklist_count = await self.blacklist.count()
        except AttributeError:
            return await errorEmb(inter, "wait for the bot to load")
        if blacklist_count == 0:
            return await errorEmb(inter, "There are no blacklisted users")
        blacklist_reason_count = 0
        nested_blacklisted = [[]]
        blacklist_embs = []
        nested_count = 0
        for user in self.blacklist.blacklist:
            if (len(user.reason) + blacklist_reason_count) <= 1990:
                blacklist_reason_count += len(user.reason)
                if isinstance(nested_blacklisted[nested_count], BlacklistedUser):
                    nested_count += 1
                    nested_blacklisted.append([])
                nested_blacklisted[nested_count].append(user)
            else:
                blacklist_reason_count = 0
                nested_blacklisted.append(user)
                nested_count += 1

        for blacklist_list in nested_blacklisted:
            if not blacklist_list:
                continue

            if isinstance(blacklist_list, list):
                emb = Embed(color=self.bot.config.colors.invis, description="")
                for user in blacklist_list:
                    emb.add_field(
                        name=f"**{self.get_user(user.id).name}**",
                        value=f"Expires: {user.get_expiry}\nReason: {user.reason}\n",
                    )

                blacklist_embs.append(emb)
            elif isinstance(blacklist_list, BlacklistedUser):
                emb = Embed(color=self.bot.config.colors.invis, description="")
                emb.title = f"**{self.get_user(blacklist_list.id).name}**"
                emb.description = f"Expires: {blacklist_list.get_expiry}\nReason: {blacklist_list.reason}\n"
                blacklist_embs.append(emb)

        blacklist_embs.append(
            Embed(color=self.bot.config.colors.invis, description="The end ;D")
        )
        start_emb = Embed(title="Blacklist", color=self.bot.config.colors.invis)
        start_emb.description = f"There are currently {blacklist_count:,d} blacklisted user{'s' if blacklist_count > 1 else ''}, use the arrows below to navigate through them"
        blacklist_embs.insert(0, start_emb)
        await inter.send(
            embed=blacklist_embs[0],
            view=CreatePaginator(blacklist_embs, inter.author.id),
        )


def setup(bot):
    bot.add_cog(Blacklist(bot))
