import os

from dotenv import load_dotenv

from utils.leveling.leveling_system import LevelingSystem

load_dotenv('secrets.env')
from utils.bot import OGIROID

bot = OGIROID()
levels = LevelingSystem()
TOKEN = bot.config.tokens.bot


def main():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            bot.load_extension(f"cogs.{filename[:-3]}")
    bot.run(TOKEN)


if __name__ == "__main__":
    main()
