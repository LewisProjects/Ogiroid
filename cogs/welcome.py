import random
from datetime import datetime
from sqlite3 import Timestamp

import disnake
from disnake.ext.commands import Cog

from utils.bot import OGIROID


class Welcome(Cog):
    def __init__(self, bot: OGIROID):
        self.bot = bot
        self.get_channel = self.bot.get_channel

    @Cog.listener()
    async def on_member_join(self, member):
        if member.dm_channel is None:
            await member.create_dm()
            embed = disnake.Embed(
                title="Welcome to Lewis Menelaws' Official Discord Server", 
                description=f"Welcome to the official Discord server {member.name}, please checkout the designated channels.We hope you have a great time here.", 
                color=0xFFFFFF)
            embed.add_field(name="Chat with other members:", value="Chat with the members, <#985729550732394536>", inline=True)
            embed.add_field(name="Introductions:", value="Introduce yourself, <#985554479405490216>", inline=True)
            embed.add_field(name="Roles:", value="Select some roles, <#985961186107461673>", inline=True)
            embed.add_field(name="Reddit Bot Related:", value="Here for the Reddit bot? Checkout <#986531210283069450>", inline=True)
            embed.add_field(name="Rules:", value="Checkout the rules, <#985936949581865030>", inline=True)
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
