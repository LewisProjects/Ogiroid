from disnake.ext import commands
import disnake
from datetime import datetime


class Starboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.starboard_channel_id = 985936949581865030
        self.star_emoji = "⭐"
        self.num_of_stars = 3

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if reaction.emoji == self.star_emoji:
            message = reaction.message
            for reaction in message.reactions:
                if (
                    reaction.emoji == self.star_emoji
                    and reaction.count == self.num_of_stars
                ):
                    starboard_channel = message.guild.get_channel(
                        self.starboard_channel_id
                    )
                    embed = disnake.Embed(
                        description=f"{message.content}\n\n**[Jump to message!]({message.jump_url})**",
                        color=disnake.Color.gold(),
                        timestamp=datetime.utcnow(),
                    )
                    embed.set_author(
                        name=message.author, icon_url=message.author.avatar.url
                    )
                    await starboard_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        channel = self.bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        if payload.emoji.name == self.star_emoji:
            for reaction in message.reactions:
                if (
                    reaction.emoji == self.star_emoji
                    and reaction.count == self.num_of_stars
                ):
                    starboard_channel = message.guild.get_channel(
                        self.starboard_channel_id
                    )
                    embed = disnake.Embed(
                        description=f"{message.content}\n\n**[Jump to message]({message.jump_url})**",
                        color=disnake.Color.gold(),
                        timestamp=datetime.utcnow(),
                    )
                    embed.set_author(
                        name=message.author, icon_url=message.author.avatar.url
                    )
                    await starboard_channel.send(embed=embed)


def setup(bot):
    bot.add_cog(Starboard(bot))