import expr
from disnake.ext import commands

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


def setup(bot: OGIROID):
    bot.add_cog(Math(bot))
