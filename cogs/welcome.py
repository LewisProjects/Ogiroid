from disnake.ext.commands import Cog
import aiohttp
from datetime import datetime
import io
import disnake


class Welcome(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.get_channel = bot.get_channel

    @Cog.listener()
    async def on_member_join(self, member):
        #   await member.add_roles(member.guild.get_role(768476148237336576), member.guild.get_role(770253516324732963)) #ROLE ON JOIN
        chan = self.get_channel(905183354930995320)
        embed = disnake.Embed(
            title="Welcome!",
            description=f"{member.mention}, you are the `{member.guild.member_count}th` member!\n\n 📑**__RULES:__** <#905182869410955355>\n ➰**__ROLES:__** <#933102052173828136>\n 👋**__INTRODUCTION__**: <#980049243236597780>\n\n",
            color=0xFFFFFF,
            timestamp=datetime.utcnow(),
        )
        embed.set_author(
            name=f"Welcome, {member.name}",
            url=f"{member.avatar.url}",
            icon_url=f"{member.avatar.url}",
        )
        embed.add_field(
            name="\n> Here for the Reddit Bot?\n",
            value="\n\n**_Read the <#985908874362093620> channel!_**\n Ask TikTokRedditBot related questions in <#981613938166890556>!",
            inline=False,
        )
        embed.set_thumbnail(url=member.avatar.url)
        embed.set_footer(text="Member Joined")
        await chan.send(f"{member.mention}, Welcome to Lewis' Coding Server!", embed=embed)

    @Cog.listener()
    async def on_member_remove(self, member):
        chan = self.get_channel(905183354930995320)
        embed = disnake.Embed(
            title="Goodbye :(",
            description=f"{member.mention} has left the server. There are now `{member.guild.member_count}` members",
            color=0xFF0000,
            timestamp=datetime.utcnow(),
        )
        embed.set_author(
            name="Member Left!",
            url=f"{member.avatar.url}",
            icon_url=f"{member.avatar.url}",
        )
        embed.set_image(url=member.avatar.url)
        embed.set_footer(text="Member Left")
        await chan.send(f"{member.mention} has left!", embed=embed)


def setup(bot):
    bot.add_cog(Welcome(bot))
