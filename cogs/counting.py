import asyncio
import os
import random
import time
from datetime import datetime, timezone

import akinator as ak
import disnake
import requests
from discord_together import DiscordTogether
from disnake import Embed, ApplicationCommandInteraction, Member
from disnake.ext import commands
from disnake.utils import utcnow
from dotenv import load_dotenv

from utils.CONSTANTS import morse
from utils.assorted import renderBar
from utils.bot import OGIROID
from utils.http import HTTPSession
from utils.shortcuts import errorEmb


class CountingGame(commands.Cog):
    # The idea of this game is that one user types 1 and the next user types 2 and so on.
    # If someone types a number that is not the next number in the sequence, they lose.
    # The game ends when someone types the wrong number or when the game is stopped with the stop command.
    # It's only in one channel, say for example #counting with the ID 1234567890.
    # The game is always started and no commands are needed to start it.
    # Also, the game is always running, so if someone types 1, the next person to type a number will be 2.

    def __init__(self, bot: OGIROID):
        self.bot = bot
        self.count = 1
        self.channel = None

    @commands.Cog.listener()
    async def on_ready(self):
        self.channel = self.bot.get_channel(986722646135824465)
        # Restore the history from the Discord channel
        async for message in self.channel.history(limit=10):
            if message.author.bot:
                continue
            if message.content.isdigit():
                self.count = int(message.content)

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if message.channel == self.channel:
            if message.author.bot or not message.content.isdigit():
                return
            messages = await self.channel.history(limit=1).flatten()
            last_message = messages[1]
            print(f"{last_message.author.name}: {last_message.content}")
            if last_message.author == message.author and last_message.content.isdigit():
                embed = Embed(
                    title="Counting Game",
                    description=f"{message.author.mention}, you can't do this alone!",
                    color=0xFF0000,
                )
                await self.channel.send(embed=embed)
                self.count = 1
            elif message.content == str(self.count):
                self.count += 1
                # Add checkmark reaction
                await message.add_reaction("✅")
            else:
                embed = Embed(
                    title="Counting Game",
                    description=f"{message.author.mention} lost the game! Someone type 1 to start a new game.",
                    color=0xFF0000,
                )
                await self.channel.send(embed=embed)
                self.count = 1
                # TODO Implement leaderboard with db


def setup(bot):
    bot.add_cog(CountingGame(bot))
