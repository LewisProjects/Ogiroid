from datetime import datetime

import disnake
from disnake import Embed
from disnake.ext.commands import Cog

from utils.bot import OGIROID

import typing as t

MAIN_COLOR = 0x5E7BDD
POSITIVE_COLOR = 0x309C41
NEGATIVE_COLOR = 0xCC0202


class Log(Cog):
    def __init__(self, bot: OGIROID):
        self.bot = bot
        self.log_channel = None

    @Cog.listener()
    async def on_ready(self):
        self.log_channel = self.bot.get_channel(self.bot.config.channels.logs)

    @Cog.listener()
    async def on_user_update(self, before, after):
        if before.name != after.name:
            embed = Embed(
                title="Username change",
                colour=after.colour,
                timestamp=datetime.now(),
            )

            fields = [("Before", before.name, False), ("After", after.name, False)]

            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)

            await self.log_channel.send(embed=embed)

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

            await self.log_channel.send(embed=embed)

        embed = Embed(
            title="Avatar change",
            description="New image is below, old to the right.",
            colour=self.log_channel.guild.get_member(after.id).colour,
            timestamp=datetime.now(),
        )

        if before.display_avatar.url != after.display_avatar.url:
            embed.set_thumbnail(url=before.display_avatar.url)
            embed.set_image(url=after.display_avatar.url)
            embed.set_footer(
                text=f"{after.name}#{after.discriminator}",
                icon_url=after.display_avatar.url,
            )
            await self.log_channel.send(embed=embed)

        if before.display_avatar.url is None:
            embed.set_thumbnail(url=before.display_avatar.url)
            embed.set_image(url=after.display_avatar.url)
            embed.set_footer(
                text=f"{after.name}#{after.discriminator}",
                icon_url=after.display_avatar.url,
            )
            await self.log_channel.send(embed=embed)

    @Cog.listener()
    async def on_member_update(self, before, after):
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
            embed.set_footer(
                text=f"{after.name}#{after.discriminator}",
                icon_url=after.display_avatar.url,
            )
            await self.log_channel.send(embed=embed)

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
            await self.log_channel.send(embed=embed)

    @Cog.listener()
    async def on_message_edit(self, before, after):
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
                embed.set_footer(
                    text=f"{after.author.name}#{after.author.discriminator}"
                )
                await self.log_channel.send(embed=embed)

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

            embed.set_footer(
                text=f"{message.author.name}#{message.author.discriminator}"
            )
            await self.log_channel.send(embed=embed)

    @Cog.listener()
    async def on_slash_command(self, inter):
        ogiroid_log_channel = self.bot.get_channel(
            self.bot.config.channels.ogiroid_logs
        )
        embed = Embed(
            colour=inter.author.colour,
            timestamp=datetime.now(),
        )

        embed.set_author(name=inter.author, icon_url=inter.author.display_avatar.url)

        options = " ".join(
            [f"{name}: {value}" for name, value in inter.options.items()]
        )

        embed.description = (
            f"`/{inter.data['name']}{' ' + options if options != '' else options}`"
        )

        embed.set_footer(text=f"{inter.author.name}#{inter.author.discriminator}")
        await ogiroid_log_channel.send(embed=embed)

    @Cog.listener()
    async def on_guild_role_create(self, role: disnake.Role):
        """Sends a message in log channel when role is created."""
        title = "Role created"
        content = f"{role.mention}(``{role.id}``) has been created."

        embed = Embed(
            title=title,
            description=content,
            colour=self.bot.config.colors.white,
            timestamp=datetime.now(),
        )

        await self.log_channel.send(embed=embed)

    @Cog.listener()
    async def on_guild_role_delete(self, role: disnake.Role):
        """Sends a message in log channel when role gets deleted."""
        embed = Embed(
            title="Role deleted",
            description=f"**{role.name}**(``{role.id}``) has been deleted.",
            colour=disnake.Color.red(),
            timestamp=datetime.now(),
        )

        await self.log_channel.send(embed=embed)

    @Cog.listener()
    async def on_guild_role_update(self, before: disnake.Role, after: disnake.Role):
        """Sends a message in log channel when role edites in the server."""

        title = "Role edited"

        if before.name != after.name:
            content = f"**{before.name}** has been named to **{after.name}**"
        else:  # needs to check perms aswell
            return

        embed = Embed(
            title=title,
            description=content,
            colour=self.bot.config.colors.white,
            timestamp=datetime.now(),
        )

        await self.log_channel.send(embed=embed)

    @Cog.listener()
    async def on_guild_update(self, before: disnake.Guild, after: disnake.Guild):
        """Sends a message in log channel when guild updates."""
        if before.name != after.name:
            message = (
                f"Server name has been changed:\n"
                f"Before: `{before.name}`\n"
                f"After: `{after.name}`"
            )
        elif before.afk_channel != after.afk_channel:
            message = (
                f"Server AFK channel has been edited:\n"
                f"Before: {before.afk_channel.mention}\n"
                f"After: {after.afk_channel.mention}"
            )
        elif before.afk_timeout != after.afk_timeout:
            message = (
                f"Server AFK timeout has been edited:\n"
                f"Before: `{before.afk_timeout}`\n"
                f"After: `{after.afk_timeout}`"
            )

        embed = Embed(
            title="Server edited",
            description=message,
            colour=self.bot.config.colors.white,
            timestamp=datetime.now(),
        )

        await self.log_channel.send(embed=embed)

    @Cog.listener()
    async def on_thread_create(self, thread: disnake.Thread):
        """Sends a message in log channel when thread creates."""

        embed = Embed(
            title="Thread created",
            description=f"Thread {thread.mention} (`{thread.id}`) has been created.",
            colour=disnake.Color.green(),
            timestamp=datetime.now(),
        )

        await self.log_channel.send(embed=embed)

    @Cog.listener()
    async def on_thread_update(self, before: disnake.Thread, after: disnake.Thread):
        """Sends a message in log channel when thread updates."""
        embed = Embed(
            title="Thread name edited",
            description=(
                f"Thread {after.mention} (`{after.id}`) in {after.parent.mention} (`{after.parent.id}`)\n"
                f"Before: `{before.name}`\n"
                f"After: `{after.name}`"
            ),
            colour=self.bot.config.colors.white,
            timestamp=datetime.now(),
        )

        await self.log_channel.send(embed=embed)

    @Cog.listener()
    async def on_thread_delete(self, thread: disnake.Thread):
        """Sends a message in log channel when thread deletes."""
        embed = Embed(
            title="Thread deleted",
            description=f"Thread **{thread.name}** (`{thread.id}`) in {thread.parent.mention} (`{thread.parent.id}`) deleted.",
            colour=disnake.Color.red(),
            timestamp=datetime.now(),
        )

        await self.log_channel.send(embed=embed)

    @Cog.listener()
    async def on_member_ban(
        self, guild: disnake.Guild, user: t.Union[disnake.User, disnake.Member]
    ):
        """Sends a message in log channel if member gets banned from the server."""

        ban = await guild.fetch_ban(user)

        embed = Embed(
            title="Member banned",
            description=f"{user.mention}(``{user.id}``) has been banned. \n Reason: {ban.reason}",
            colour=disnake.Color.red(),
            timestamp=datetime.now(),
        )

        await self.log_channel.send(embed=embed)

    @Cog.listener()
    async def on_member_unban(self, guild: disnake.Guild, user: disnake.User):
        """Sends a message in log channel if member gets unbanned from the server."""
        embed = Embed(
            title="Member unbanned",
            description=f"{user.mention}(``{user.id}``) has been unbanned.",
            colour=disnake.Color.green(),
            timestamp=datetime.now(),
        )

        await self.log_channel.send(embed=embed)


def setup(bot):
    bot.add_cog(Log(bot))
