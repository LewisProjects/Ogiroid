import disnake
from disnake.ext import commands

from utils.bot import OGIROID
from utils.pagination import CreatePaginator


class HelpCommand(commands.Cog, name="Help"):
    """Help Command"""

    def __init__(self, bot: OGIROID):
        self.bot = bot
        self.COLOUR = 0xFFFFFF

    @commands.slash_command(name="help", description="Lists all commands")
    async def help(self, inter):
        """Lists all commands"""
        embeds = []

        cogs = self.bot.cogs.items()
        for cog_name, cog in cogs:
            embed = disnake.Embed(title=cog.qualified_name, colour=self.COLOUR)
            if cog is None:
                continue
            cmds = cog.get_slash_commands()
            name = cog.qualified_name

            value = ""
            for cmd in cmds:
                value += f"`/{cmd.qualified_name}` - {cmd.description}\n"
                if cmd.children:
                    for children, sub_command in cmd.children.items():
                        try:
                            value += f"`/{sub_command.qualified_name}` - {sub_command.description}\n"
                        except AttributeError:
                            pass

            if value == "":
                continue

            embed.description = f"{cog.description}\n\n{value}"
            embeds.append(embed)

        paginator = CreatePaginator(embeds, inter.author.id, timeout=300.0)
        await inter.send(embed=embeds[0], view=paginator)


def setup(bot: commands.Bot):
    bot.add_cog(HelpCommand(bot))
