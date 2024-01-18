from io import BytesIO

import disnake
import expr
from PIL import Image
from disnake import TextInputStyle
from disnake.ext import commands
import urllib.parse

from utils.http import session
from utils.bot import OGIROID
from utils.shortcuts import QuickEmb, errorEmb


class Math(commands.Cog):
    """Do Math"""

    def __init__(self, bot: OGIROID):
        self.bot = bot

    @commands.slash_command(description="Evaluates a math equation.")
    async def math(self, inter, equation):
        """Evaluates a math equation"""
        equation = equation.replace("×", "*")
        try:
            answer = expr.evaluate(equation)
        except expr.errors.InvalidSyntax:
            await errorEmb(
                inter,
                "You used invalid syntax in your equation.\n"
                "If you need help use the ``/mathhelp`` command.\n"
                "If this is a bug report it with the ``/reportbug`` command.",
            )
        except expr.errors.DivisionByZero:
            await errorEmb(inter, "You know that you can't divide by zero.")
        except expr.errors.Gibberish:
            await errorEmb(
                inter,
                "Are you sure that is a valid equation?\n"
                "If you need help use the ``/mathhelp`` command.\n"
                "If this is a bug report it with the ``/reportbug`` command.",
            )
        except Exception as e:
            await errorEmb(
                inter,
                f"{e}\n"
                f"If you need help use the ``/mathhelp`` command."
                "If this is a bug report it with the ``/reportbug`` command.",
            )
        else:
            await QuickEmb(inter, f"Result: ```{answer}```").success().send()

    @commands.slash_command(
        name="mathhelp", description="Help for the ``/math`` command"
    )
    async def math_help(self, inter):
        await QuickEmb(
            inter,
            "The following operations are supported:\n"
            " `+` (addition)\n `-` (subtraction)\n `*` (multiplication)\n `/` (division) \n"
            "`//` (floor division)\n `%` (modulo)\n `^` (exponentation)\n `!` (factorial)\n"
            "Aswell as these:\n"
            " `sqrt` | `cbrt` | `log` | `log10` | `ln` | `rad` | `sin` | `cos` | `tan` | `asin` | `acos` | `atan`",
        ).send()

    @commands.slash_command(description="Latex to Image")
    async def latex(self, inter):
        """Latex to Image"""
        await inter.response.send_modal(modal=LatexModal())


class LatexModal(disnake.ui.Modal):
    def __init__(self):
        # The details of the modal, and its components
        components = [
            disnake.ui.TextInput(
                label="Latex",
                placeholder="Latex format here",
                custom_id="latex",
                style=TextInputStyle.paragraph,
                max_length=4000,
            ),
        ]
        super().__init__(
            title="Convert",
            custom_id="convert",
            components=components,
        )

    # The callback received when the user input is completed.
    async def callback(self, inter: disnake.ModalInteraction):
        try:
            print(1)
            await inter.response.defer()
            latex = inter.text_values["latex"].strip()
            async with session.post(
                r"https://latex.codecogs.com/png.latex?\dpi{180}\bg_white\large"
                + urllib.parse.quote(" " + latex)
            ) as resp:
                # Read the content from the response
                image_data = await resp.read()

                # Open the image using PIL
                with Image.open(BytesIO(image_data)) as image:
                    # Add 5 pixels of padding on all sides
                    padding_size = 5
                    padded_image = Image.new(
                        "RGB",
                        (
                            image.width + 2 * padding_size,
                            image.height + 2 * padding_size,
                        ),
                        "white",
                    )
                    padded_image.paste(image, (padding_size, padding_size))

                    # Save the image to a BytesIO buffer
                    image_buffer = BytesIO()
                    padded_image.save(image_buffer, "png")
                    image_buffer.seek(0)

                # Send the image
                await inter.send(file=disnake.File(image_buffer, filename="latex.png"))

        except Exception as e:
            print(e)
            await errorEmb(inter, f"Error: {e}")


def setup(bot: OGIROID):
    bot.add_cog(Math(bot))
