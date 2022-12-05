from datetime import datetime

import disnake
from disnake.ext import commands

from utils.bot import OGIROID


class Starboard(commands.Cog):
    def __init__(self, bot: OGIROID):
        self.bot = bot
        self.starboard_channel_id = self.bot.config.channels.starboard
        self.star_emoji = "⭐"
        self.num_of_stars = 4

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        channel = self.bot.get_channel(payload.channel_id)
        if (
            channel.guild.id != self.bot.config.guilds.main_guild
            or channel.id == self.starboard_channel_id
        ):
            return
        message = await channel.fetch_message(payload.message_id)
        starboard_channel = message.guild.get_channel(self.starboard_channel_id)
        if payload.emoji.name == self.star_emoji and not channel == starboard_channel:
            for reaction in message.reactions:
                if (
                    reaction.emoji == self.star_emoji
                    and reaction.count == self.num_of_stars
                ):
                    embed = disnake.Embed(
                        description=f"{message.content}\n\n**[Jump to message]({message.jump_url})**",
                        color=disnake.Color.gold(),
                        timestamp=datetime.now(),
                    )
                    embed.set_author(
                        name=message.author, icon_url=message.author.display_avatar.url
                    )
                    await starboard_channel.send(embed=embed)


def setup(bot):
    bot.add_cog(Starboard(bot))
