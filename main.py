import os

from dotenv import load_dotenv

load_dotenv("secrets.env")  # keep above OGIROID import
from utils.bot import OGIROID

bot = OGIROID()
TOKEN = bot.config.tokens.bot


def main():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            bot.load_extension(f"cogs.{filename[:-3]}")
    bot.run(TOKEN)


if __name__ == "__main__":
    main()
