from datetime import datetime

from disnake import Embed
from disnake.ext.commands import Cog

import discord
from discord.ext import commands
import typing as t

MAIN_COLOR = 0x5e7bdd
POSITIVE_COLOR = 0x309c41
NEGATIVE_COLOR = 0Xcc0202


class Log(Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    async def send_modlog(self,
        color: discord.Colour,
        title: t.Optional[str],
        text: str,
        member: t.Optional[discord.Member] = None,
        content: t.Optional[str] = None) -> Context:
    
        embed = discord.Embed(description=text[:4093] + '...' if len(text) > 4096 else text)

        if title:
            embed.set_author(name=title)

        embed.timestamp = datetime.utcnow()
        embed.color = color
        
        
        if content and len(content) > 2000:
            content = content[:2000 - 3] + '...'
        
        modlog_channel = self.bot.get_channel() # < - channel ID
        log_message = await modlog_channel.send(
            content=content,
            embed=embed
        )

        return log_message

    @Cog.listener()
    async def on_user_update(self, before, after):
        log_channel = self.bot.get_channel(self.bot.config.channels.logs)
        if before.name != after.name:
            embed = Embed(
                title="Username change",
                colour=after.colour,
                timestamp=datetime.now(),
            )

            fields = [("Before", before.name, False), ("After", after.name, False)]

            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)

            await log_channel.send(embed=embed)

        if before.discriminator != after.discriminator:
            embed = Embed(
                title="User discriminator changed",
                colour=after.colour,
                timestamp=datetime.now(),
            )

            fields = [
                ("Before", before.discriminator, False),
                ("After", after.discriminator, False),
            ]

            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)

            await log_channel.send(embed=embed)

        if before.display_avatar.url != after.display_avatar.url:
            embed = Embed(
                title="Avatar change",
                description="New image is below, old to the right.",
                colour=log_channel.guild.get_member(after.id).colour,
                timestamp=datetime.now(),
            )

            embed.set_thumbnail(url=before.display_avatar.url)
            embed.set_image(url=after.display_avatar.url)
            embed.set_footer(text=f"{after.name}#{after.discriminator}", icon_url=after.display_avatar.url)
            await log_channel.send(embed=embed)

        if before.display_avatar.url is None:
            embed = Embed(
                title="Avatar change",
                description="New image is below, old to the right.",
                colour=log_channel.guild.get_member(after.id).colour,
                timestamp=datetime.now(),
            )

            embed.set_thumbnail(url=before.display_avatar.url)
            embed.set_image(url=after.display_avatar.url)
            embed.set_footer(
                text=f"{after.name}#{after.discriminator}",
                icon_url=after.display_avatar.url,
            )
            await log_channel.send(embed=embed)

    @Cog.listener()
    async def on_member_update(self, before, after):
        log_channel = self.bot.get_channel(self.bot.config.channels.logs)
        if before.display_name != after.display_name:
            embed = Embed(
                title="Nickname change",
                colour=after.colour,
                timestamp=datetime.now(),
            )

            fields = [
                ("Before", before.display_name, False),
                ("After", after.display_name, False),
            ]

            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)
            embed.set_footer(text=f"{after.name}#{after.discriminator}", icon_url=after.display_avatar.url)
            await log_channel.send(embed=embed)

        elif before.roles != after.roles:
            embed = Embed(
                title=f"Role updates for {after.name}",
                colour=after.colour,
                timestamp=datetime.now(),
            )

            fields = [
                ("Before", ", ".join([r.mention for r in before.roles]), False),
                ("After", ", ".join([r.mention for r in after.roles]), False),
            ]

            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)
            embed.set_footer(
                text=f"{after.name}#{after.discriminator}",
                icon_url=after.display_avatar.url,
            )
            await log_channel.send(embed=embed)

    @Cog.listener()
    async def on_message_edit(self, before, after):
        log_channel = self.bot.get_channel(self.bot.config.channels.logs)
        if not after.author.bot:
            if before.content != after.content:
                embed = Embed(
                    title="Message edit",
                    description=f"Edit by {after.author.name}.",
                    colour=after.author.colour,
                    timestamp=datetime.now(),
                )

                fields = [
                    ("Before", before.content, False),
                    ("After", after.content, False),
                ]

                for name, value, inline in fields:
                    embed.add_field(name=name, value=value, inline=inline)
                embed.set_footer(text=f"{after.author.name}#{after.author.discriminator}")
                await log_channel.send(embed=embed)

    @Cog.listener()
    async def on_message_delete(self, message):
        if not message.author.bot:
            embed = Embed(
                title="Message deletion",
                description=f"Action by {message.author.name}.",
                colour=message.author.colour,
                timestamp=datetime.now(),
            )

            fields = [("Content", message.content, False)]

            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)

            embed.set_footer(text=f"{message.author.name}#{message.author.discriminator}")
            log_channel = self.bot.get_channel(self.bot.config.channels.logs)
            await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        """Sends a message in log channel when role is deleted."""
        title = 'Role deleted'
        content = f'**{role.name}**(``{role.id}``) has been deleted.'

        await self.send_modlog(NEGATIVE_COLOR, title, content)


    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):

        title = 'Role edited'
        after.permissions = []
        before.permissions = []
        
        if before.permissions == after.permissions:
            return

        if before.name != after.name: 
            content = f'**{before.name}** has been named to **{after.name}**'
        else: 
            return
        
        await self.send_modlog(MAIN_COLOR, title, content)

    
    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):

        title = 'Server edited'
        
        if before.name != after.name:
            message = (f'Server name has been changed:\n'
                       f'Before: `{before.name}`\n'
                       f'After: `{after.name}`')
        elif before.afk_channel != after.afk_channel:
            message = (f'Server AFK channel has been edited:\n'
                       f'Before: {before.afk_channel.mention}\n'
                       f'After: {after.afk_channel.mention}')
        elif before.afk_timeout != after.afk_timeout:
            message = (f'Server AFK timeout has been edited:\n'
                       f'Before: `{before.afk_timeout}`\n'
                       f'After: `{after.afk_timeout}`')

        await self.send_modlog(MAIN_COLOR, title, message)

    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread):

        title = 'Thread created'
        message = f'Thread {thread.mention} (`{thread.id}`) has been created.'

        await self.send_modlog(POSITIVE_COLOR, title, message)


    @commands.Cog.listener()
    async def on_thread_update(self, before: discord.Thread, after: discord.Thread):

        title = 'Thread name edited'
        message = (f'Thread {after.mention} (`{after.id}`) in {after.parent.mention} (`{after.parent.id}`)\n'
                   f'Before: `{before.name}`\n' 
                   f'After: `{after.name}`')

        await self.send_modlog(MAIN_COLOR, title, message)

    
    @commands.Cog.listener()
    async def on_thread_delete(self, thread: discord.Thread):

        title = 'Thread deleted'
        message = f'Thread **{thread.name}** (`{thread.id}`) in {thread.parent.mention} (`{thread.parent.id}`) deleted.'

        await self.send_modlog(NEGATIVE_COLOR, title, message)



def setup(bot):
    bot.add_cog(Log(bot))
