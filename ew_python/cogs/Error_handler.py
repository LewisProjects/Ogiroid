from __future__ import annotations

import traceback
from datetime import datetime
import datetime as dt

import disnake
from disnake import Embed, ApplicationCommandInteraction, HTTPException
from disnake.ext.commands import *

from utils.CONSTANTS import IGNORE_EXCEPTIONS
from utils.bot import OGIROID
from utils.shortcuts import errorEmb, permsEmb


class ErrorHandler(Cog):
    def __init__(self, bot: OGIROID):
        self.bot = bot
        self.debug_mode = self.bot.config.debug
        self.waitTime = 25

    def TimeSinceStart(self) -> float:
        return round((datetime.now() - self.bot.uptime).total_seconds(), ndigits=1)

    # noinspection PyUnboundLocalVariable
    @Cog.listener()
    async def on_slash_command_error(self, inter: ApplicationCommandInteraction, error):
        try:
            if hasattr(inter.application_command, "on_error"):
                return
            elif error.__class__.__name__ in IGNORE_EXCEPTIONS:
                return

            # Databases and internal caches might not be fully loaded yet.
            # In debug mode we don't want to wait for them cause its fucking annoying.
            if self.TimeSinceStart() < self.waitTime and not self.debug_mode:
                return await errorEmb(
                    inter,
                    f"The bot just started, please wait {round(self.waitTime - self.TimeSinceStart(), ndigits=2)}s.",
                )

            # non real error handling
            if isinstance(error, CommandNotFound):
                return await errorEmb(inter, "Command not found! use /help for a list of commands")
            elif isinstance(error, NotOwner):
                await errorEmb(
                    inter,
                    f"You must be the owner of {inter.me.display_name} to use `{inter.application_command.name}`",
                )
            elif isinstance(error, HTTPException):
                await errorEmb(inter, error.text)
                return await self.send_traceback(inter, error)
            elif isinstance(error, MissingPermissions):
                return await permsEmb(inter, permissions=f"{', '.join(error.missing_permissions)}")
            elif isinstance(error, MissingRole):
                return await permsEmb(inter, permissions=f"Role: {error.missing_role}")
            elif isinstance(error, MaxConcurrencyReached):
                return await errorEmb(
                    inter, "You've reached max capacity of command usage at once, please finish the previous one..."
                )
            elif isinstance(error, CommandOnCooldown):
                return await errorEmb(inter, f"This command is on cooldown... try again in {error.retry_after:.2f} seconds.")
            elif isinstance(error, GuildNotFound):
                return await errorEmb(error, f"You can only use this command in a server")
            elif isinstance(error, CheckFailure):
                if self.bot.uptime - dt.timedelta(seconds=10) < datetime.now():
                    return await errorEmb(inter, "wait a few seconds before using this command again")
                return await errorEmb(inter, "You don't have permission to use this command")
            elif self.debug_mode:
                traceback_nice = "".join(traceback.format_exception(type(error), error, error.__traceback__, 4))
                print(traceback_nice)
                traceback.print_exc()
                return await errorEmb(inter, "check console for error")
            else:  # actual error not just a check failure
                embed = await self.create_error_message(inter, error)
                await inter.send(embed=embed, ephemeral=True)
                await self.send_traceback(inter, error)

        except Exception as e:
            error_channel = self.bot.get_channel(self.bot.config.channels.errors)
            embed = await self.create_error_message(inter, e)
            await inter.send(embed=embed, ephemeral=True)
            e_traceback = traceback.format_exception(type(e), e, e.__traceback__)
            if self.debug_mode:
                print(e_traceback)
            e_embed = disnake.Embed(
                title="Error Traceback",
                description=f"See below!\n\n{e_traceback}",
                timestamp=datetime.now(),
            )

            await error_channel.send(embed=e_embed)

            # Debug Info
            traceback_nice_e = "".join(traceback.format_exception(type(e), e, e.__traceback__, 4)).replace("```", "")

            debug_info_e = (
                f"```\n{inter.author} {inter.author.id}: /{inter.application_command.name}"[:200]
                + "```"
                + f"```py\n{traceback_nice_e}"[: 2000 - 206]
                + "```"
            )
            await error_channel.send(debug_info_e)

    async def send_traceback(self, inter, error):
        error_channel = self.bot.get_channel(self.bot.config.channels.errors)
        bot_errors = traceback.format_exception(type(error), error, error.__traceback__)

        error_embed = disnake.Embed(
            title="Error Traceback",
            description=f"See below!\n\n{bot_errors}",
            timestamp=datetime.now(),
        )
        await error_channel.send(embed=error_embed)
        traceback_nice = "".join(traceback.format_exception(type(error), error, error.__traceback__, 4)).replace("```", "```")

        debug_info = (
            f"```\n{inter.author} {inter.author.id}: /{inter.application_command.name}"[:200]
            + "```"
            + f"```py\n{traceback_nice}"[: 2000 - 206]
            + "```"
        )
        await error_channel.send(debug_info)

    @staticmethod
    async def create_error_message(inter, error) -> Embed:
        embed = disnake.Embed(
            title=f"❌An error occurred while executing: ``/{inter.application_command.qualified_name}``",
            description=f"{error}",
            colour=disnake.Color.blurple(),
            timestamp=datetime.now(),
        )
        embed.add_field(
            name="Something not right?",
            value="\nUse the ``/reportbug`` command to report a bug.",
        )
        embed.set_footer(
            text=f"Executed by {inter.author}",
            icon_url="https://www.collinsdictionary.com/images/full/lo_163792823.jpg",
        )
        return embed


def setup(bot):
    bot.add_cog(ErrorHandler(bot))
