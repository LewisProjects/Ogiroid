import disnake
from disnake.ext import commands
import aiosqlite
import os
from disnake.ext.commands import when_mentioned_or

GUILD_ID = 897666935708352582 
BUG_CHAN = 982669110926250004  
SUGG_CHAN = 982353129913851924 

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
                type=disnake.ActivityType.listening, name="v2.0 | Beta! | !!help"
            )
        )
        print(
            "--------------------------------------------------------------------------------"
        )
        print("Bot is ready! Logged in as: " + self.user.name)
        print("Bot author: HarryDaDev  |  FreebieII")
        print("Bot version: 2.0 BETA")
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
    command_prefix=get_prefix, intents=disnake.Intents.all(), help_command=None
)


def main():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            client.load_extension(f"cogs.{filename[:-3]}")
    client.run(
        "OTg0ODAyMDA4NDAzOTU5ODc5.Gc9c9z.4lcYtBNVH7ZmJBAN7-vZ3F0mnMp6fNGShOj6gk"
    )  
if __name__ == "__main__":
    main()
