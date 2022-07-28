from disnake import TextInputStyle, Color
import disnake
from disnake import Embed
from disnake.ext import commands
from disnake.ext.commands import Cog

from utils.CONSTANTS import VALID_CODE_LANGUAGES
from utils.http import session
from utils.bot import OGIROID


class CodeExec(Cog, name="Code"):
    """
    💻 Run code and get results instantly!
    """

    def __init__(self, bot: OGIROID):
        self.bot = bot

    @commands.slash_command(name="code", description="Run code and get results instantly. Window for code will pop up.")
    async def code(self, ctx):
        """
        Run code and get results instantly
        """
        await ctx.response.send_modal(modal=CodeModal())


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
        if not self._check_valid_lang(inter.text_values["language"]):
            embed = disnake.Embed(title=f"{inter.text_values['language']} is not a valid language", colour=Color.red())
            return await inter.response.send_message(embed=embed)

        embed = disnake.Embed(title="Running Code")
        embed.add_field(
            name="Language",
            value=inter.text_values["language"].capitalize(),
            inline=False,
        )
        embed.add_field(
            name="Code",
            value=f"```{inter.text_values['language']}\n" f"{inter.text_values['code'][:999]}\n" f"```",
            inline=False,
        )
        await inter.response.send_message(embed=embed)
        result = await self.run_code(lang=inter.text_values["language"], code=inter.text_values["code"])
        await self._send_result(inter, result)

    async def run_code(self, *, lang: str, code: str):
        code = await session.post("https://emkc.org/api/v1/piston/execute", json={"language": lang, "source": code})
        return await code.json()

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

    @staticmethod
    def _check_valid_lang(param):
        if str(param).casefold() not in VALID_CODE_LANGUAGES:
            return False
        return True


def setup(bot: OGIROID):
    bot.add_cog(CodeExec(bot))
