import aiosqlite
import disnake
from disnake.ext import commands

from utils.http import HTTPSession
from utils.config import Config
with open("setup.sql", "r") as sql_file:
    SETUP_SQL = sql_file.read()


class OGIROID(commands.Bot):
    def __init__(self, *args, **kwargs):
        self.db = None
        super().__init__(*args, **kwargs)
        self.config = Config()
        self.session = HTTPSession(loop=self.loop)

    async def on_ready(self):
        await self.wait_until_ready()
        await self.change_presence(activity=disnake.Activity(type=disnake.ActivityType.listening, name="the users!"))
        print("--------------------------------------------------------------------------------")
        print("Bot is ready! Logged in as: " + self.user.name)
        print("Bot author: HarryDaDev | FreebieII")
        print("Bot version: 1.3")
        print("--------------------------------------------------------------------------------")

    async def start(self, *args, **kwargs):
        async with aiosqlite.connect("data.db") as self.db:
            await self.db.executescript(SETUP_SQL)
            await super().start(*args, **kwargs)
