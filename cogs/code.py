import requests
from disnake import TextInputStyle
import disnake
from datetime import datetime
from disnake.ext.commands import Cog
from disnake.ext.commands import command
from disnake import Color, Embed
from disnake.ext import commands
from disnake.ext.commands import Cog


class CodeModal(disnake.ui.Modal):
    def __init__(self):
        # The details of the modal, and its components
        components = [
            disnake.ui.TextInput(
                label="Language",
                placeholder="Language",
                custom_id="language",
                style=TextInputStyle.short,
                max_length=15,
            ),
            disnake.ui.TextInput(
                label="Code",
                placeholder="Write your code here",
                custom_id="code",
                style=TextInputStyle.paragraph,
            ),
        ]
        super().__init__(
            title="Run Code",
            custom_id="run_code",
            components=components,
        )

    # The callback received when the user input is completed.
    async def callback(self, inter: disnake.ModalInteraction):
        embed = disnake.Embed(title="Running Code")
        embed.add_field(
            name="Language",
            value=inter.text_values["language"].capitalize(),
            inline=False,
        )
        embed.add_field(
            name="Code",
            value=f"```{inter.text_values['language']}\n"
                  f"{inter.text_values['code'][:1024]}\n"
                  f"```",
            inline=False,
        )
        await inter.response.send_message(embed=embed)
        result = await self._run_code(lang=inter.text_values["language"], code=inter.text_values["code"])
        await self._send_result(inter, result)

    async def _run_code(self, *, lang: str, code: str):
        res = requests.post(
            "https://emkc.org/api/v1/piston/execute",
            json={"language": lang, "source": code},
        )
        return res.json()

    async def _send_result(self, inter, result: dict):
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
        embed.add_field(name="Output", value=f"```\n{output}\n```" or "**<No output>**")

        await inter.send(embed=embed)


class CodeExec(Cog):
    """
    💻 Run code and get results instantly!
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(
        name="code",
        description="Run code and get results instantly. Window for code will pop up."
    )
    async def code(self, ctx):
        """
        Run code and get results instantly
        """
        await ctx.response.send_modal(modal=CodeModal())


def setup(bot: commands.Bot):
    bot.add_cog(CodeExec(bot))
