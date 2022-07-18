import disnake
from disnake.ext import commands
import aiosqlite
import os
from disnake.ext.commands import when_mentioned_or


GUILD_ID = 985234686878023730  # 897666935708352582
BUG_CHAN = 985554459948122142  # 982669110926250004
SUGG_CHAN = 985554479405490216  # 982353129913851924

with open("setup.sql", "r") as sql_file:
    SETUP_SQL = sql_file.read()


class OGIROID(commands.Bot):
    def __init__(self, *args, **kwargs):
        self.db = None
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        await self.wait_until_ready()
        await self.change_presence(
            activity=disnake.Activity(
                type=disnake.ActivityType.listening, name="the users!"
            )
        )
        print(
            "--------------------------------------------------------------------------------"
        )
        print("Bot is ready! Logged in as: " + self.user.name)
        print("Bot author: HarryDaDev | FreebieII")
        print("Bot version: 1.3")
        print(
            "--------------------------------------------------------------------------------"
        )

    async def start(self, *args, **kwargs):
        async with aiosqlite.connect("data.db") as self.db:
            await self.db.executescript(SETUP_SQL)
            await super().start(*args, **kwargs)


async def get_prefix(bot, message):
    prefix = "!!"
    return when_mentioned_or(prefix)(bot, message)


client = OGIROID(
    command_prefix=get_prefix,
    intents=disnake.Intents.all(),
    help_command=None,
    sync_commands_debug=True,
    case_insensitive=True,
)

"""
@client.event
async def on_command_error(ctx, error):
	if isinstance(error, commands.CommandOnCooldown):
		await ctx.send(f"**Slow down there!** \n{round(error.retry_after, 2)} seconds left.")
"""



def main():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            client.load_extension(f"cogs.{filename[:-3]}")
     client.run(
        "ODYyMzU5NDIyNTY3NTc5NzA4.GUc6gD.gRe0vE8eL0UqzF_wTuQ80oAoFm7aZf1ilqfWY0"
     )  # MESSING AROUNDS TOKEN



if __name__ == "__main__":
    main()
