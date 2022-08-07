import os
from dotenv import load_dotenv
from utils.bot import OGIROID

load_dotenv("secrets.env")
TOKEN = os.getenv("TOKEN")

bot = OGIROID()

def main():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            bot.load_extension(f"cogs.{filename[:-3]}")
    bot.run(TOKEN)


if __name__ == "__main__":
    main()
