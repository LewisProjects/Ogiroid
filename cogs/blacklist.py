from typing import List

import disnake
from disnake import Member, Embed, Option, OptionType
from disnake.ext import commands, tasks
from disnake.ext.commands import Cog

from utils import timeconversions
from utils.exceptions import BlacklistNotFound
from utils.models import BlacklistedUser
from utils.pagination import CreatePaginator
from utils.shortcuts import sucEmb, errorEmb, get_expiry
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from utils.bot import OGIROID


class BlacklistHandler:
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        self._blacklist: List[BlacklistedUser] = []

    def get_user(self, user_id: int):
        return [user for user in self._blacklist if user.id == user_id][0]

    @property
    def blacklist(self):
        return self._blacklist

    async def startup(self):
        await self.bot.wait_until_ready()
        try:
            await self.load_blacklist()
        except BlacklistNotFound:
            print("[TAGS] No blacklisted users found")

    async def count(self):
        return len(self._blacklist)

    async def load_blacklist(self):
        blacklist = []
        async with self.db.execute(f"SELECT * FROM blacklist") as cur:
            async for row in cur:
                blacklist.append(BlacklistedUser(*row).fix_db_types())
        if len(blacklist) == 0:
            raise BlacklistNotFound
        self._blacklist = blacklist

    async def get(self, user_id: int):
        return self.get_user(user_id)

    async def add(self, user_id: int, reason: str, bot: bool, tickets: bool, tags: bool, expires: int):
        await self.db.execute(
            f"INSERT INTO blacklist (user_id, reason, bot, tickets, tags, expires) VALUES (?, ?, ?, ?, ?, ?)",
            [user_id, reason, bot, tickets, tags, expires], )
        await self.db.commit()
        self._blacklist.append(BlacklistedUser(user_id, reason, bot, tickets, tags, expires))

    async def remove(self, user_id: int):
        await self.db.execute(f"DELETE FROM blacklist WHERE user_id = ?", [user_id])
        await self.db.commit()
        self._blacklist.remove(self.get_user(user_id))

    async def blacklisted(self, user_id: int):
        return any(user.id == user_id for user in self._blacklist)

    async def edit_flags(self, user_id: int, bot: bool, tickets: bool, tags: bool):
        await self.db.execute(
            f"UPDATE blacklist SET bot = ?, tickets = ?, tags = ? WHERE user_id = ?",
            [bot, tickets, tags, user_id])
        await self.db.commit()
        self._blacklist[self._blacklist.index(self.get_user(user_id))].bot = bot
        self._blacklist[self._blacklist.index(self.get_user(user_id))].tickets = tickets  # todo simplify this
        self._blacklist[self._blacklist.index(self.get_user(user_id))].tags = tags

    async def edit_reason(self, user_id: int, reason: str):
        await self.db.execute(
            f"UPDATE blacklist SET reason = ? WHERE user_id = ?",
            [reason, user_id])
        await self.db.commit()
        self._blacklist[self._blacklist.index(self.get_user(user_id))].reason = reason

    async def edit_expiry(self, user_id: int, expires: int):
        await self.db.execute(
            f"UPDATE blacklist SET expires = ? WHERE user_id = ?",
            [expires, user_id])
        await self.db.commit()
        self._blacklist[self._blacklist.index(self.get_user(user_id))].expires = expires


class Blacklist(Cog):
    def __init__(self, bot: "OGIROID"):
        self.bot = bot
        self.blacklist: BlacklistHandler = None

    def get_user(self, user_id):
        return self.bot.get_user(user_id)

    @staticmethod
    def approve_expiry(expires: str):
        if expires == 'never':
            return True
        elif expires.isnumeric():
            pass  # todo

    @tasks.loop(minutes=10)
    async def check_blacklist(self):
        remove_que = []
        for user in self.bot.blacklist.blacklist:
            if user.is_expired():
                remove_que.append(user.id)
        for user_id in remove_que:
            await self.blacklist.remove(user_id)

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.wait_until_ready()
        self.blacklist: BlacklistHandler = self.bot.blacklist
        self.check_blacklist.start()

    @commands.slash_command(description="Blacklist base command", hidden=True)
    async def blacklist(self, inter):
        pass

    @commands.cooldown(1, 5, commands.BucketType.user)
    @blacklist.sub_command(name='info', description="Get info about a blacklisted user")
    async def blacklist_info(self, inter, user: Member):
        if not await self.blacklist.blacklisted(user.id):
            return await errorEmb(inter, f"{user.mention} is not in the blacklist")
        bl_user = self.blacklist.get_user(user.id)
        embed = Embed(title=f"Blacklisted user: {user.name}", color=disnake.Color.random(seed=user.name))
        embed.add_field(name="Reason", value=bl_user.reason, inline=False)
        embed.add_field(name="Expires", value=bl_user.get_expiry, inline=False)
        embed.add_field(name="Bot", value=bl_user.bot)
        embed.add_field(name="Tickets", value=bl_user.tickets)
        embed.add_field(name="Tags", value=bl_user.tags)
        await inter.send(embed=embed)

    @blacklist.sub_command_group(name="edit", description="Edit a user in the blacklist")
    async def edit(self, inter):
        pass

    @commands.has_permissions(manage_messages=True)
    @edit.sub_command(name="flags", description="Edit the user's blacklist flags in the blacklist")
    async def flags(self, inter, user: Member, bot: bool, tickets: bool, tags: bool):
        if not await self.blacklist.blacklisted(user.id):
            return await errorEmb(inter, f"{user.mention} is not in the blacklist")
        await self.blacklist.edit_flags(user.id, bot, tickets, tags)
        await sucEmb(inter, f"Edited {user.mention}'s blacklist flags to\nBot: {bot}, Tickets: {tickets}, Tags: {tags}")

    @commands.has_permissions(manage_messages=True)
    @edit.sub_command(name="reason", description="Edit the user's blacklist reason in the blacklist")
    async def reason(self, inter, user: Member, reason: str):
        if not await self.blacklist.blacklisted(user.id):
            return await errorEmb(inter, f"{user.mention} is not in the blacklist")
        await self.blacklist.edit_reason(user.id, reason)
        await sucEmb(inter,
                     f"Edited {user.mention}'s reason in the blacklist to see the full reason use /blacklist info {user.mention}")

    @commands.has_permissions(manage_messages=True)
    @edit.sub_command(name="expiry", description="Edit the user's blacklist expiry in the blacklist")
    async def expiry(self, inter, user: Member, expires: str):
        if not await self.blacklist.blacklisted(user.id):
            return await errorEmb(inter, f"{user.mention} is not in the blacklist")
        time = int((await timeconversions.convert(expires)).dt.timestamp())
        await self.blacklist.edit_expiry(user.id, time)
        await sucEmb(inter,
                     f"Edited the expiry of {user.mention}'s blacklist to expire {get_expiry(time)}")

    @commands.has_permissions(manage_messages=True)
    @blacklist.sub_command(name="remove", description="Remove a user from the blacklist")
    async def remove(self, inter, user: Member):
        if not await self.blacklist.blacklisted(user.id):
            return await errorEmb(inter, f"{user.mention} is not in the blacklist")
        await self.blacklist.remove(user.id)
        await sucEmb(inter, f"{user.mention} has been removed from blacklist", ephemeral=False)

    @commands.has_permissions(manage_messages=True)
    @blacklist.sub_command(name="add", description="Add a user to the blacklist",
                           options=[
                               Option("user", description="User to blacklist", type=OptionType.user, required=True),
                               Option("bot", description="Whether to blacklist the user from using the entire bot",
                                      type=OptionType.boolean,
                                      required=True),
                               Option("tickets", description="Whether to blacklist the user from using tickets",
                                      type=OptionType.boolean,
                                      required=True),
                               Option("tags", description="Whether to blacklist the user from using tags",
                                      type=OptionType.boolean,
                                      required=True),
                               Option("expires", description="When the blacklist should expire (e.g. 1w, 5m, never)",
                                      type=OptionType.string,
                                      required=False),
                               Option("reason", description="Reason for blacklisting the user", type=OptionType.string,
                                      required=False)
                           ])
    async def blacklist_add(self, inter, user, bot, tickets, tags,
                            reason='No Reason Specified', expires='never'):
        if not any((bot, tickets, tags)):  # todo check expiration format or never
            return await errorEmb(inter,
                                  "You can't blacklist a user without specifying either bot, tickets and/or tags")
        if len(reason) > 900:
            return await errorEmb(inter, "Reason must be under 900 chars")
        elif await self.blacklist.blacklisted(user.id):
            return await errorEmb(inter, f"{user.mention} is already in the blacklist")
        expires = ((await timeconversions.convert(expires)).dt.timestamp())
        await self.blacklist.add(user.id, reason, bot, tickets, tags, expires)
        await sucEmb(inter,
                     f"{user.mention} added to blacklist\nthe user's blacklist will {f'expire on <t:{expires}:R>' if str(expires) != str(9999999999) else 'never expire'}",
                     ephemeral=False)

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
                    emb.add_field(name=f"**{self.get_user(user.id).name}**",
                                  value=f'Expires: {user.get_expiry}\nReason: {user.reason}\n')

                blacklist_embs.append(emb)
            elif isinstance(blacklist_list, BlacklistedUser):
                emb = Embed(color=self.bot.config.colors.invis, description="")
                emb.title = f"**{self.get_user(blacklist_list.id).name}**"  # todo get user name
                emb.description = f'Expires: {blacklist_list.get_expiry}\nReason: {blacklist_list.reason}\n'
                blacklist_embs.append(emb)

        blacklist_embs.append(Embed(color=self.bot.config.colors.invis, description="The end ;D"))
        start_emb = Embed(title="Blacklist", color=self.bot.config.colors.invis)
        start_emb.description = f"There are currently {blacklist_count:,d} blacklisted user{'s' if blacklist_count > 1 else ''}, use the arrows below to navigate through them"
        blacklist_embs.insert(0, start_emb)
        await inter.send(embed=blacklist_embs[0], view=CreatePaginator(blacklist_embs, inter.author.id))


def setup(bot):
    bot.add_cog(Blacklist(bot))
