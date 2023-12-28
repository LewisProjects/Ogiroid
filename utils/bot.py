import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

import asyncpg
import disnake
from disnake import ApplicationCommandInteraction, OptionType
from disnake.ext import commands

from utils.db_models import Base
from utils.CONSTANTS import __VERSION__
from utils.DBhandlers import BlacklistHandler
from utils.cache import async_cache
from utils.config import Config
from utils.exceptions import UserBlacklisted
from utils.http import HTTPSession
from utils.shortcuts import errorEmb

with open("setup.sql", "r") as sql_file:
    SETUP_SQL = sql_file.read()


class OGIROID(commands.InteractionBot):
    def __init__(self, *args, **kwargs):
        super().__init__(
            intents=disnake.Intents.all(),
            command_sync_flags=commands.CommandSyncFlags(sync_commands_debug=True),
            *args,
            **kwargs,
        )
        self._ready_ = False
        self.uptime = datetime.now()
        self.session = HTTPSession(loop=self.loop)
        self.config = Config()
        self.commands_ran = {}
        self.total_commands_ran = {}
        self.db = None
        self.blacklist: BlacklistHandler = None
        self.add_app_command_check(
            self.blacklist_check, slash_commands=True, call_once=True
        )

    async def blacklist_check(self, ctx):
        try:
            await self.wait_until_ready()
            if await self.blacklist.blacklisted(ctx.author.id):
                await errorEmb(ctx, "You are blacklisted from using this bot!")
                raise UserBlacklisted
            return True
        except AttributeError:
            pass  # DB hasn't loaded yet

    @async_cache(maxsize=0)
    async def on_slash_command(self, inter: ApplicationCommandInteraction):
        COMMAND_STRUCT = [inter.data]
        do_break = False
        while True:
            COMMAND = COMMAND_STRUCT[-1]
            if not COMMAND.options:
                if inter.data == COMMAND:
                    COMMAND_STRUCT = [inter.data]
                    break
                COMMAND_STRUCT = [inter.data, COMMAND]
                break
            for option in COMMAND.options:
                if option.options:
                    COMMAND_STRUCT.append(option)
                    do_break = False
                elif option.type in [
                    OptionType.sub_command_group,
                    OptionType.sub_command,
                ]:
                    COMMAND_STRUCT.append(option)
                else:
                    do_break = True
                    break
            if do_break:
                break

        COMMAND_NAME = " ".join([command.name for command in COMMAND_STRUCT])

        try:
            self.total_commands_ran[inter.guild.id] += 1
        except KeyError:
            self.total_commands_ran[inter.guild.id] = 1

        if self.commands_ran.get(inter.guild.id) is None:
            self.commands_ran[inter.guild.id] = {}

        try:
            self.commands_ran[inter.guild.id][COMMAND_NAME] += 1
        except KeyError:
            self.commands_ran[inter.guild.id][COMMAND_NAME] = 1

    async def on_ready(self):
        if not self._ready_:
            await self.wait_until_ready()
            await self._setup()
            await self.change_presence(
                activity=disnake.Activity(
                    type=disnake.ActivityType.listening, name="the users!"
                )
            )
            print(
                "--------------------------------------------------------------------------------"
            )
            print("Bot is ready! Logged in as: " + self.user.name)
            print("Bot devs: HarryDaDev | FreebieII | JasonLovesDoggo | Levani")
            print(f"Bot version: {__VERSION__}")
            print(
                "--------------------------------------------------------------------------------"
            )
            await asyncio.sleep(
                5
            )  # Wait 5 seconds for the bot to load the database and setup
            self._ready_ = True

        else:
            print("Bot reconnected")

    async def _setup(self):
        # for command in self.application_commands:
        #     self.commands_ran[f"{command.qualified_name}"] = 0
        self.blacklist: BlacklistHandler = BlacklistHandler(self, self.db)
        await self.blacklist.startup()

    async def load_db(self):
        pass

    async def start(self, *args, **kwargs):

        engine = create_async_engine(
            self.config.Database.connection_string, pool_pre_ping=True
        )
        self.db = async_sessionmaker(engine, expire_on_commit=False)
        await super().start(*args, **kwargs)

    @property
    def ready_(self):
        return self._ready_
