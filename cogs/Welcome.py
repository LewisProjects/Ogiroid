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
        if member.guild.id != self.bot.config.guilds.main_guild:
            return
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
            embed.add_field(
                name="Chat with other members:",
                value=f"Chat with the members, {general.mention}",
                inline=True,
            )
            embed.add_field(
                name="Introductions:",
                value=f"Introduce yourself, {introduction.mention}",
                inline=True,
            )
            embed.add_field(
                name="Roles:", value=f"Select some roles, {roles.mention}", inline=True
            )
            embed.add_field(
                name="Reddit Bot Related:",
                value=f"Here for the Reddit bot? Checkout {reddit_bot.mention}",
                inline=True,
            )
            embed.add_field(
                name="Rules:", value=f"Checkout the rules, {rules.mention}", inline=True
            )
            embed.set_thumbnail(url=member.display_avatar)
            try:
                await member.dm_channel.send(embed=embed)
            except disnake.Forbidden:
                pass  # DMs are closed or something else went wrong so we just ignore it and move on with our lives :D
        else:
            pass

        greetings = ["Hello", "Hi", "Greetings", "Hola", "Bonjour", "Konnichiwa"]
        secondary_greeting = [
            "Welcome to Lewis Menelaws' Official Discord Server! Feel free to look around & introduce yourself.",
            "Welcome to the server! We wish you have a great time here, make sure you tell us a little bit about yourself.",
            "Hope you are doing well! Welcome to the server. How about start by introducing yourself?",
            "It's great to have you here, please feel free to look around & introduce yourself.",
            "Woohoo! You have made it, please introduce yourself.",
            "You have arrived! Feels great to have you here, maybe look around & introduce yourself?",
        ]
        greeting_emojis = ["👋", "🎊", "🎉", "💻", "🙏", "🤝"]
        chan = self.get_channel(self.bot.config.channels.welcome)

        welcome_msg = f"{random.choice(greetings)} {member.mention}! {random.choice(secondary_greeting)}\nWe are now at: {len(member.guild.members)} members!"
        msg = await chan.send(welcome_msg)

        await msg.add_reaction(random.choice(greeting_emojis))

    @Cog.listener()
    async def on_member_remove(self, member):
        if member.guild.id != self.bot.config.guilds.main_guild:
            return
        channel = self.get_channel(self.bot.config.channels.logs)
        embed = disnake.Embed(
            title="Goodbye :(",
            description=f"{member.mention} has left the server. There are now `{member.guild.member_count}` members",
            color=0xFF0000,
            timestamp=datetime.now(),
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
