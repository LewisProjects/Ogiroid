import aiosqlite
import disnake
from disnake import ApplicationCommandInteraction
from disnake.ext import commands
from disnake.ext.commands import when_mentioned_or

from utils.CONSTANTS import __VERSION__
from utils.DBhandelers import BlacklistHandler
from utils.config import Config
from utils.exceptions import UserBlacklisted
from utils.http import HTTPSession
from utils.shortcuts import errorEmb

with open("setup.sql", "r") as sql_file:
    SETUP_SQL = sql_file.read()


async def get_prefix(bot, message):
    prefix = "!!"
    return when_mentioned_or(prefix)(bot, message)


class OGIROID(commands.Bot):
    def __init__(self, *args, **kwargs):

        super().__init__(
            command_prefix=get_prefix,
            intents=disnake.Intents.all(),
            help_command=None,
            sync_commands_debug=True,
            case_insensitive=True,
            *args,
            **kwargs,
        )
        self.session = HTTPSession(loop=self.loop)
        self.config = Config()
        self.commands_ran = {}
        self.total_commands_ran = 0
        self.db = None
        self.blacklist: BlacklistHandler = None
        self.add_check(self.blacklist_check)
        self.add_app_command_check(self.blacklist_check, slash_commands=True)

    async def blacklist_check(self, ctx):
        await self.wait_until_ready()
        if await self.blacklist.blacklisted(ctx.author.id):
            await errorEmb(ctx, "You are blacklisted from using this bot!")
            raise UserBlacklisted
        return True

    async def on_command(self, ctx):
        self.total_commands_ran += 1
        try:
            self.commands_ran[ctx.command.qualified_name] += 1
        except KeyError:
            self.commands_ran[ctx.command.qualified_name] = 1

    async def on_slash_command(self, inter: ApplicationCommandInteraction):
        self.total_commands_ran += 1
        try:
            self.commands_ran[inter.application_command.name] += 1
        except KeyError:
            self.commands_ran[inter.application_command.name] = 1

    async def on_ready(self):
        await self.wait_until_ready()
        await self._setup()
        await self.change_presence(activity=disnake.Activity(type=disnake.ActivityType.listening, name="the users!"))
        print("--------------------------------------------------------------------------------")
        print("Bot is ready! Logged in as: " + self.user.name)
        print("Bot devs: HarryDaDev | FreebieII | JasonLovesDoggo | Levani | DWAA")
        print(f"Bot version: {__VERSION__}")
        print("--------------------------------------------------------------------------------")

    async def _setup(self):
        for command in self.application_commands:
            self.commands_ran[f"{command.qualified_name}"] = 0
        self.blacklist: BlacklistHandler = BlacklistHandler(self, self.db)
        await self.blacklist.startup()

    async def start(self, *args, **kwargs):
        async with aiosqlite.connect("data.db") as self.db:
            await self.db.executescript(SETUP_SQL)
            await super().start(*args, **kwargs)
