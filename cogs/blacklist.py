from typing import List

from disnake import Member
from disnake.ext import commands
from disnake.ext.commands import Cog

from utils.bot import OGIROID
from utils.exceptions import BlacklistNotFound
from utils.models import BlacklistedUser
from utils.shortcuts import sucEmb


class BlacklistHandler:
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        self._blacklist: List[BlacklistedUser] = []

    async def startup(self):
        await self.bot.wait_until_ready()
        try:
            await self.load_blacklist()
        except BlacklistNotFound:
            print("[TAGS] No blacklisted users found")

    async def load_blacklist(self):
        blacklist = []
        async with self.db.execute(f"SELECT * FROM blacklist") as cur:
            async for row in cur:
                blacklist.append(BlacklistedUser(*row))
        if len(blacklist) == 0:
            raise BlacklistNotFound
        self._blacklist = blacklist

    async def add(self, user_id: int, reason: str, bot: bool, tickets: bool, tags: bool, expires: int):
        await self.db.execute(
            f"INSERT INTO blacklist (user_id, reason, bot, tickets, tags, expires) VALUES (?, ?, ?, ?, ?, ?)",
            [user_id, reason, bot, tickets, tags, expires],
        )
        await self.db.commit()
        self._blacklist.append(BlacklistedUser(user_id, reason, bot, tickets, tags, expires))


class Blacklist(Cog):
    def __init__(self, bot: OGIROID):
        self.bot = bot
        self.blacklist: BlacklistHandler = None

    @commands.Cog.listener()
    async def on_ready(self):
        self.blacklist: BlacklistHandler = BlacklistHandler(self.bot, self.bot.db)
        await self.blacklist.startup()

    @commands.slash_command(description="Blacklist base command", hidden=True)
    async def blacklist(self, inter):
        pass

    @blacklist.sub_command(name="add", description="Add a user to the blacklist")
    async def blacklist_add(self, inter, user: Member, reason: str, bot: bool, tickets: bool, tags: bool, expires: int):

        await self.blacklist.add(user.id, reason, bot, tickets, tags, expires)
        await sucEmb(inter, f"{user.mention} added to blacklist", ephemeral=False)
        print(self.blacklist._blacklist)


def setup(bot):
    bot.add_cog(Blacklist(bot))
