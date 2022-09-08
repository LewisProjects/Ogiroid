import importlib
import io
import os
import textwrap
import traceback
from contextlib import redirect_stdout

from disnake import ApplicationCommandInteraction
from disnake.ext import commands
from disnake.ext.commands import Cog, Param

from utils import checks
from utils.assorted import traceback_maker
from utils.checks import is_dev


class Dev(Cog):
    def __init__(self, bot):
        self.bot = bot

        self._last_result = None

    def cleanup_code(self, content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith("```") and content.endswith("```"):
            return "\n".join(content.split("\n")[1:-1])

        # remove `foo`
        return content.strip("` \n")

    @commands.slash_command()
    @checks.is_dev()
    async def pyeval(self, inter, *, body: str):
        """Evaluates a code"""
        await inter.response.defer()
        env = {
            "bot": self.bot,
            "inter": inter,
            "channel": inter.channel,
            "author": inter.author,
            "guild": inter.guild,
            "message": await inter.original_message(),
            "_": self._last_result,
        }

        env.update(globals())

        body = self.cleanup_code(body)
        stdout = io.StringIO()

        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

        try:
            exec(to_compile, env)
        except Exception as e:
            return await inter.send(f"```py\n{e.__class__.__name__}: {e}\n```")

        func = env["func"]
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception as e:
            value = stdout.getvalue()
            await inter.send(f"```py\n{value}{traceback.format_exc()}\n```")
        else:
            value = stdout.getvalue()
            try:
                await (await inter.original_message()).add_reaction("\u2705")
            except:
                pass

            if ret is None:
                if value:
                    await inter.send(f"```py\n{value}\n```")
            else:
                self._last_result = ret
                await inter.send(f"```py\n{value}{ret}\n```")

    @staticmethod
    def autocomplete(inter: ApplicationCommandInteraction, option_name: str):
        """Autocomplete for the reload command"""
        options = os.listdir("cogs")
        options = [option[:-3] for option in options if option.endswith(".py")]
        return [option for option in options if option.startswith(inter.data.options[0].value)]

    @staticmethod
    def autocomplete_util(inter: ApplicationCommandInteraction, option_name: str):
        """Autocomplete for the reload command"""
        options = os.listdir("utils")
        options = [option[:-3] for option in options if option.endswith(".py")]
        return [option for option in options if option.startswith(inter.data.options[0].value)]

    @commands.slash_command()
    @checks.is_dev()
    async def say(self, inter: ApplicationCommandInteraction, *, what_to_say: str):
        """says text"""
        await (await inter.original_message()).delete()
        await inter.send(f"{what_to_say}")

    @commands.slash_command()
    @checks.is_dev()
    async def load(self, inter: ApplicationCommandInteraction, name: str = Param(autocomplete=autocomplete)):
        """The command is used to load the Extensions into the Bot."""
        name = name.title()
        try:
            self.bot.load_extension(f"cogs.{name}")
        except Exception as e:
            return await inter.send(traceback_maker(e))
        await inter.send(f"Loaded extension **{name}.py**")

    @commands.slash_command()
    @checks.is_dev()
    async def unload(self, inter: ApplicationCommandInteraction, name: str = Param(autocomplete=autocomplete)):
        """Unloads an extension."""
        name = name.title()
        try:
            self.bot.unload_extension(f"cogs.{name}")
        except Exception as e:
            return await inter.send(traceback_maker(e))
        await inter.send(f"Unloaded extension **{name}.py**")

    @commands.slash_command()
    @checks.is_dev()
    async def reload(self, inter: ApplicationCommandInteraction, name: str = Param(autocomplete=autocomplete)):
        """Reloads an extension."""
        name = name.title()
        try:
            self.bot.reload_extension(f"cogs.{name}")
        except Exception as e:
            return await inter.send(traceback_maker(e))
        await inter.send(f"Reloaded extension **{name}.py**")

    @commands.slash_command()
    @checks.is_dev()
    async def reloadall(self, inter: ApplicationCommandInteraction):
        """Reloads all extensions."""
        error_collection = []
        for file in os.listdir("cogs"):
            if file.endswith(".py"):
                name = file[:-3]
                try:
                    self.bot.reload_extension(f"cogs.{name}")
                except Exception as e:
                    error_collection.append([file, traceback_maker(e, advance=False)])

        if error_collection:
            output = "\n".join([f"**{g[0]}** ```diff\n- {g[1]}```" for g in error_collection])
            return await inter.send(
                f"Attempted to reload all extensions, was able to reload, " f"however the following failed...\n\n{output}"
            )

        await inter.send("Successfully reloaded all extensions")

    @commands.slash_command()
    @checks.is_dev()
    async def reloadutils(self, inter: ApplicationCommandInteraction, name: str = Param(autocomplete=autocomplete_util)):
        """Reloads a utils module."""
        name_maker = f"utils/{name}.py"
        try:
            module_name = importlib.import_module(f"utils.{name}")
            importlib.reload(module_name)
        except ModuleNotFoundError:
            return await inter.send(f"Couldn't find module named **{name_maker}**")
        except Exception as e:
            error = traceback_maker(e)
            return await inter.send(f"Module **{name_maker}** returned error and was not reloaded...\n{error}")
        await inter.send(f"Reloaded module **{name_maker}**")


def setup(bot):
    bot.add_cog(Dev(bot))