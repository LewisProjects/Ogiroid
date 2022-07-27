import disnake
import os
from disnake.ext.commands import when_mentioned_or
from dotenv import load_dotenv

from utils.bot import OGIROID

load_dotenv("secrets.env")

TOKEN = os.getenv("TOKEN")
GUILD_ID = 985234686878023730  # 897666935708352582
BUG_CHAN = 985554459948122142  # 982669110926250004
SUGG_CHAN = 985554479405490216  # 982353129913851924


async def get_prefix(bot, message):
    prefix = "!!"
    return when_mentioned_or(prefix)(bot, message)


client = OGIROID(
    command_prefix=get_prefix,
    intents=disnake.Intents.all(),
    help_command=None,
    sync_commands_debug=True, # todo change
    case_insensitive=True,
)


def main():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            client.load_extension(f"cogs.{filename[:-3]}")
    client.run(TOKEN)


if __name__ == "__main__":
    main()
