import disnake
from disnake import Message
from disnake.ext import commands
import random

from utils.bot import OGIROID
from utils.rankcard import Rankcard
from utils.shortcuts import sucEmb, errorEmb, QuickEmb
from utils.CONSTANTS import xp_needed, xp_probability

class LevelsController:
    def __init__(self, bot: OGIROID, db):
        self.bot = bot
        self.db = db

    async def add_xp(self, user_id: int, xp: int):
        return self.db.add_xp(user_id, xp)

    async def handle_message(self, message):
        pass

    async def get_user(self, user_id: int):
        return self.db.get_user(user_id)

class Level(commands.Cog):
    def __init__(self, bot: OGIROID):
        self.bot = bot
        self.levels = xp_needed
        self.controller: LevelsController = None

    async def generate_image_card(self, msg):#, user_id, lvl):
        """generates an image card for the user"""
        #user = self.get_user(user_id)
        user = msg.author
        username = msg.author.name + "#" + msg.author.discriminator
        currentxp = 1
        lastxp = 0
        lvlxp = 2
        current_level = 1
        current_rank = 1
        background = None
        image = await Rankcard().create_img(user=user, xp=(currentxp, lvlxp), level=current_level, rank=current_rank)
        file = disnake.File(filename="rankcard.png", fp=image)
        await msg.channel.send(file=file)


    def cog_unload(self) -> None:
        pass

    @commands.Cog.listener()
    async def on_rankup(self, msg: Message):#, user_id: int, level: int):
        await self.generate_image_card(msg)#user_id, level)
        #await msg.channel.send(embed=image_card)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        self.bot.dispatch("rankup", message)
        await self.controller.handle_message(message)

    @commands.Cog.listener()
    async def on_ready(self):
        self.controller = LevelsController(self.bot, self.bot.db)

    @staticmethod
    async def random_xp():
        return random.choice(xp_probability)

    def get_user(self, user_id: int):
        return self.controller.get_user(user_id)





def setup(bot: OGIROID):
    bot.add_cog(Level(bot))
