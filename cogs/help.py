from disnake.ext import commands
import disnake


class HelpCommand(commands.Cog, name="Help"):
    """Help Command"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.COLOUR = 0xFFFFFF

    @commands.slash_command(name="help", description="Lists all commands")
    async def help(self, inter):
        """Lists all commands"""
        embed = disnake.Embed(title="Bot Commands", colour=self.COLOUR)
        embed.set_author(
            name="Ogiroid's help menu!",
            url="https://freebie.codes",
            icon_url="https://cdn.discordapp.com/avatars/984802008403959879/7016c34bd6bce62f9b0f2534f8918c49.png?size=1024",
        )

        cogs = self.bot.cogs.items()
        for cog_name, cog in cogs:
            if cog is None:
                continue
            cmds = cog.get_slash_commands()
            name = cog.qualified_name

            value = " ".join(f"`/{cmd.name}`" for cmd in cmds)

            if value == "":
                continue

            if name == "Tickets":
                continue

            if cog and cog.description:
                value = "{0}\n{1}".format(cog.description, value)

            embed.add_field(name=name, value=value)

        embed.set_footer(text="If you want more information on a particular command start typing out the command "
                              "and a description will show up")
        await inter.send(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(HelpCommand(bot))
