from __future__ import annotations

import traceback
from datetime import datetime

import disnake
from disnake import Embed, ApplicationCommandInteraction, HTTPException
from disnake.ext.commands import *

from utils.CONSTANTS import IGNORE_EXCEPTIONS
from utils.assorted import traceback_maker
from utils.bot import OGIROID
from utils.shortcuts import errorEmb, permsEmb


class ErrorHandler(Cog):
    def __init__(self, bot: OGIROID):
        self.bot = bot
        self.debug_mode = self.bot.config.debug

    # noinspection PyUnboundLocalVariable
    @Cog.listener()
    async def on_slash_command_error(self, inter: ApplicationCommandInteraction, error):
        try:
            if hasattr(inter.application_command, "on_error"):
                return
            elif error.__class__.__name__ in IGNORE_EXCEPTIONS:
                return
            # non real error handling
            if isinstance(error, CommandNotFound):
                return await errorEmb(inter, "Command not found! use /help for a list of commands")
            elif isinstance(error, CommandInvokeError):
                error = traceback_maker(error.original)
                if "2000 or fewer" in str(error) and len(error.message.clean_content) > 1900:
                    return await errorEmb(
                        inter,
                        "You attempted to make the command display more than 2,000 characters...\nBoth error and command will be ignored.",
                    )
            elif isinstance(error, MissingRequiredArgument):
                missing = f"{str(error.param).split(':')[0]}"
                cmd = f"/{inter.application_command.name}"

                await errorEmb(
                    inter,
                    title=f"\N{WARNING SIGN} | MissingArguments",
                    text=f"You forgot the `{missing}` parameter when using   `{cmd}`!",
                )
            elif isinstance(error, BadArgument):
                return await errorEmb(inter, "Bad argument! Please retry with the correct type of argument")
            elif isinstance(error, NotOwner):
                await errorEmb(
                    inter, f"You must be the owner of {inter.me.display_name} to use `{inter.application_command.name}`"
                )
            elif isinstance(error, TooManyArguments):
                return await errorEmb(inter, f"You called the {inter.application_command.name} command with too many arguments.")
            elif isinstance(error, MissingPermissions):
                return await permsEmb(inter, permissions=f"{', '.join(error.missing_permissions)}")
            elif isinstance(error, CheckFailure):
                return await errorEmb(
                    inter,
                    f"One or more permission checks have failed\nif you think this is a bug please report it to the developers via /reportbug",
                )
            elif isinstance(error, MaxConcurrencyReached):
                return await errorEmb(
                    inter, "You've reached max capacity of command usage at once, please finish the previous one..."
                )
            elif isinstance(error, CommandOnCooldown):
                return await errorEmb(inter, f"This command is on cooldown... try again in {error.retry_after:.2f} seconds.")
            elif isinstance(error, HTTPException):
                return await errorEmb(inter, f"The returned message was too long")
            elif isinstance(error, GuildNotFound):
                return await errorEmb(error, f"You can only use this command in a server")
            elif self.debug_mode:
                traceback.print_exc()
                return await errorEmb(inter, "check console for error")

            else:  # actual error not just a check failure
                error_channel = self.bot.get_channel(self.bot.config.channels.errors)
                embed = await self.create_error_message(inter, error)
                await inter.send(embed=embed, ephemeral=True)
                bot_errors = traceback.format_exception(type(error), error, error.__traceback__)

                error_embed = disnake.Embed(
                    title="Error Traceback",
                    description=f"See below!\n\n{bot_errors}",
                    timestamp=datetime.utcnow(),
                )
                await error_channel.send(embed=error_embed)
                traceback_nice = "".join(traceback.format_exception(type(error), error, error.__traceback__, 4)).replace(
                    "```", "```"
                )

                debug_info = (
                    f"```\n{inter.author} {inter.author.id}: /{inter.application_command.name}"[:200]
                    + "```"
                    + f"```py\n{traceback_nice}"[: 2000 - 206]
                    + "```"
                )
                await error_channel.send(debug_info)

        except Exception as e:
            embed = await self.create_error_message(inter, e)
            await inter.send(embed=embed, ephemeral=True)
            e_traceback = traceback.format_exception(type(e), e, e.__traceback__)
            if self.debug_mode:
                print(e_traceback)
            e_embed = disnake.Embed(
                title="Error Traceback",
                description=f"See below!\n\n{e_traceback}",
                timestamp=datetime.utcnow(),
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

    @staticmethod
    async def create_error_message(inter, error) -> Embed:
        embed = disnake.Embed(
            title=f"❌An error occurred while executing: ``/{inter.application_command.name}``",
            description=f"{error}",
            colour=disnake.Color.blurple(),
            timestamp=datetime.utcnow(),
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
