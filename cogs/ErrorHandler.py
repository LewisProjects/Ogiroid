from __future__ import annotations

from disnake import Embed
from disnake.ext import commands
import disnake
import traceback
from datetime import datetime

from utils.CONSTANTS import IGNORE_EXCEPTIONS
from utils.bot import OGIROID


class ErrorHandler(commands.Cog):
    def __init__(self, bot: OGIROID):
        self.bot = bot
        self.debug_mode = self.bot.config.debug

    @commands.Cog.listener()
    async def on_slash_command_error(self, inter, error):
        try:
            if hasattr(inter.application_command, "on_error"):
                return
            elif error.__class__.__name__ in IGNORE_EXCEPTIONS:
                return
            else:
                error_channel = self.bot.get_channel(self.bot.config.channels.errors)

                embed: Embed = await self.create_error_message(inter, error)
                await inter.send(embed=embed, ephemeral=True)
                bot_errors = traceback.format_exception(type(error), error, error.__traceback__)
                if self.bot.config.debug:
                    print(bot_errors)

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
    async def create_error_message(inter, error):
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
