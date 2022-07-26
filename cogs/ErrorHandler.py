from disnake.ext import commands
import disnake
import asyncio
import traceback
from pathlib import Path
from disnake.ext.commands import CommandNotFound
from disnake.ext.commands.errors import CommandOnCooldown, NotOwner
from datetime import datetime


class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        try:
            if hasattr(ctx.command, "on_error"):
                return
            else:
                errchan = self.get_channel(986531210283069450)
                embed = disnake.Embed(
                    title="See below for more information!",
                    description=f"`Error:` \n{error}\n\n Something not right?  **[Placeholder](https://google.com)**",
                    colour=disnake.Color.blurple(),
                    timestamp=datetime.utcnow(),
                )
                embed.set_author(name=f"❌ An error occured while executing: {ctx.command}")
                embed.set_footer(
                    text=f"{ctx.command}",
                    icon_url="https://www.collinsdictionary.com/images/full/lo_163792823.jpg",
                )
                x = await ctx.send(embed=embed)
                await asyncio.sleep(10)
                await x.delete()
                boterrors = traceback.format_exception(type(error), error, error.__traceback__)
                # print(boterrors)
                errchan = self.get_channel(856925899337105448)
                errembed = disnake.Embed(
                    title="Error Traceback",
                    description=f"See below!\n\n{boterrors}",
                    timestamp=datetime.utcnow(),
                )
                await errchan.send(embed=errembed)

                traceback_nice = "".join(traceback.format_exception(type(error), error, error.__traceback__, 4)).replace(
                    "```", "```"
                )

                debug_info = (
                    f"```\n{ctx.author} {ctx.author.id}: {ctx.message.content}"[:200]
                    + "```"
                    + f"```py\n{traceback_nice}"[: 2000 - 206]
                    + "```"
                )
                await errchan.send(debug_info)

        except:
            embed = disnake.Embed(
                title=f"❌An error occured while executing: {ctx.command}",
                description=f"{error}",
                colour=disnake.Color.blurple(),
                timestamp=datetime.utcnow(),
            )
            embed.add_field(
                name="Something not right?",
                value="\n**[Placeholder](https://google.com)**",
            )
            embed.set_footer(
                text=f"Executed by {ctx.author}",
                icon_url="https://www.collinsdictionary.com/images/full/lo_163792823.jpg",
            )
            x = await ctx.send(embed=embed)
            await asyncio.sleep(10)
            await x.delete()


def setup(bot):
    bot.add_cog(ErrorHandler(bot))
