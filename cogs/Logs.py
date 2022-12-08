from datetime import datetime

from disnake import Embed
from disnake.ext.commands import Cog


class Log(Cog):
    def __init__(self, bot):
        self.bot = bot

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


def setup(bot):
    bot.add_cog(Log(bot))
