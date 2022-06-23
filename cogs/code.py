import re

from datetime import datetime
from disnake.ext.commands import Cog
from disnake.ext.commands import command
from disnake import Color, Embed
from disnake.ext import commands
from disnake.ext.commands import Cog


class CodeExec(Cog):
    """
    💻 Run code and get results instantly! \n**Note**: You must use codeblocks around the code
    """

    def __init__(self, bot):
        self.bot = bot
        self.regex = re.compile(r"(\w*)\s*(?:```)(\w*)?([\s\S]*)(?:```$)")

    async def _run_code(self, *, lang: str, code: str):
        res = await self.session.post(
            "https://emkc.org/api/v1/piston/execute",
            json={"language": lang, "source": code},
        )
        return await res.json()

    @property
    def session(self):
        return self.bot.http._HTTPClient__session  # type: ignore

    async def _send_result(self, ctx: commands.Context, result: dict):
        if "message" in result:
            return await ctx.reply(
                embed=Embed(
                    title="Uh-oh", description=result["message"], color=Color.red()
                )
            )
        output = result["output"]
        # if len(output) > 2000: HAVE TO FIX THIS!!!!
        # url = await create_guest_paste_bin(self.session, output)
        # return await ctx.reply("Your output was too long, so here's the pastebin link " + url)
        embed = Embed(title=f"Ran your {result['language']} code", color=0xFFFFFF)
        output = output[:500].strip()
        shortened = len(output) > 500
        lines = output.splitlines()
        shortened = shortened or (len(lines) > 15)
        output = "\n".join(lines[:15])
        output += shortened * "\n\n**Output shortened**"
        embed.add_field(name="Output", value=output or "**<No output>**")

        await ctx.reply(embed=embed)

    @command(
        name="code",
        description="Run code and get results instantly **Note**: You must use codeblocks around the code",
        aliases=["runcode"],
    )
    async def code(self, ctx: commands.Context, *, codeblock: str):
        """
        Run code and get results instantly
        **Note**: You must use codeblocks around the code
        """
        matches = self.regex.findall(codeblock)
        if not matches:
            return await ctx.reply(
                embed=Embed(
                    title="Uh-oh", description="Couldn't quite see your codeblock"
                )
            )
        lang = matches[0][0] or matches[0][1]
        if not lang:
            return await ctx.reply(
                embed=Embed(
                    title="Uh-oh!",
                    description="Couldn't find the language hinted in the codeblock or before it",
                )
            )
        code = matches[0][2]
        result = await self._run_code(lang=lang, code=code)
        await self._send_result(ctx, result)


def setup(bot: commands.Bot):
    bot.add_cog(CodeExec(bot))
