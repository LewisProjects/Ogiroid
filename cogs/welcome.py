import random
from datetime import datetime

import disnake
from disnake.ext.commands import Cog

from utils.bot import OGIROID


# I have made the basic welcome command for the bot with the formatting & the emoji's but for some reason the "avatar" part is not working, I'd appreciate any help with this.


class Welcome(Cog):
    def __init__(self, bot: OGIROID):
        self.bot = bot
        self.get_channel = bot.get_channel

    @Cog.listener()
    async def on_member_join(self, member):
        #   await member.add_roles(member.guild.get_role(768476148237336576), member.guild.get_role(770253516324732963)) #ROLE ON JOIN
        greetings = ["Hello", "Hi", "Greetings", "Hola", "Bonjour"]
        chan = self.get_channel(self.bot.config.channels.welcome)
        embed = disnake.Embed(
            title="Welcome to the server.",
            description=f"You are the {len(member.guild.members)}th member of the server <:welcome:990315913280647218>.\nMake sure to checkout the rules <:rules:990316233956130817>!\nGet yourself a custom role <:roles:990316847670919239>!\nWe'd love it if you could introduce yourself!",
            color=0xFFFFFF,
            timestamp=datetime.utcnow(),
        )
        embed.set_author(
            name=f"{random.choice(greetings)}, {member.name}",
            icon_url=f"{member.display_avatar}",
        )
        embed.set_thumbnail(url=member.display_avatar)
        await chan.send(f"{member.mention}, Welcome to Coding w/ Lewis' official Discord Server!", embed=embed)

    @Cog.listener()
    async def on_member_remove(self, member):
        channel = self.get_channel(985961186107461673)
        embed = disnake.Embed(
            title="Goodbye :(",
            description=f"{member.mention} has left the server. There are now `{member.guild.member_count}` members",
            color=0xFF0000,
            timestamp=datetime.utcnow(),
        )
        embed.set_author(
            name="Member Left!",
            url=f"{member.display_avatar}",
            icon_url=f"{member.display_avatar}",
        )
        embed.set_image(url=member.display_avatar)
        embed.set_footer(text="Member Left")
        await channel.send(f"{member.mention} has left!", embed=embed)


def setup(bot):
    bot.add_cog(Welcome(bot))
