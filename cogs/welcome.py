import random
from datetime import datetime

import disnake
from disnake.ext.commands import Cog

from utils.bot import OGIROID


class Welcome(Cog):
    def __init__(self, bot: OGIROID):
        self.bot = bot
        self.get_channel = self.bot.get_channel

    @Cog.listener()
    async def on_member_join(self, member: disnake.Member):
        if member.dm_channel is None:
            introduction = self.bot.get_channel(self.bot.config.channels.introduction)
            general = self.bot.get_channel(self.bot.config.channels.general)
            roles = self.bot.get_channel(self.bot.config.channels.roles)
            reddit_bot = self.bot.get_channel(self.bot.config.channels.reddit_bot)
            rules = self.bot.get_channel(self.bot.config.channels.rules)

            await member.create_dm()
            embed = disnake.Embed(
                title="Welcome to Lewis Menelaws' Official Discord Server",
                description=f"Welcome to the official Discord server {member.name},"
                f" please checkout the designated channels.We hope you have a great time here.",
                color=0xFFFFFF,
            )
            embed.add_field(name="Chat with other members:", value=f"Chat with the members, {general.mention}", inline=True)
            embed.add_field(name="Introductions:", value=f"Introduce yourself, {introduction.mention}", inline=True)
            embed.add_field(name="Roles:", value=f"Select some roles, {roles.mention}", inline=True)
            embed.add_field(
                name="Reddit Bot Related:", value=f"Here for the Reddit bot? Checkout {reddit_bot.mention}", inline=True
            )
            embed.add_field(name="Rules:", value=f"Checkout the rules, {rules.mention}", inline=True)
            embed.set_thumbnail(url=member.display_avatar)
            await member.dm_channel.send(embed=embed)
        else:
            pass

        greetings = ["Hello", "Hi", "Greetings", "Hola", "Bonjour"]
        chan = self.get_channel(self.bot.config.channels.welcome)
        embed = disnake.Embed(
            title="Welcome to the server.",
            description=f"You are the {len(member.guild.members)}th member of the server.\nMake sure to checkout the rules {self.bot.config.emojis.rules}!\nGet yourself a custom role {self.bot.config.emojis.roles}!\nWe'd love it if you could introduce yourself!",
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
        channel = self.get_channel(self.bot.config.channels.goodbye)
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
