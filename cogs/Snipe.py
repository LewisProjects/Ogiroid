import disnake
from disnake import ApplicationCommandInteraction
from disnake.ext import commands
from disnake.ext.commands import Cog

from utils.bot import OGIROID


class Utilities(commands.Cog):
    def __init__(self, bot: OGIROID):
        """Utility Commands"""
        self.bot = bot
        self.delete_snipes = dict()
        self.edit_snipes = dict()
        self.delete_snipes_attachments = dict()

    @Cog.listener()
    async def on_message_delete(self, message):
        self.delete_snipes[message.channel] = message
        self.delete_snipes_attachments[message.channel] = message.attachments

    @Cog.listener()
    async def on_message_edit(self, before, after):
        self.edit_snipes[after.channel] = (before, after)

    @commands.slash_command(
        name="snipe", description="Get the most recently deleted message in a channel"
    )
    async def snipe_group(self, inter: ApplicationCommandInteraction):
        """Get the most recently deleted message in a channel"""

        try:
            sniped_message = self.delete_snipes[inter.channel]
        except KeyError:
            await inter.send("There are no deleted messages in this channel to snipe!")
        else:
            result = disnake.Embed(
                color=disnake.Color.red(),
                description=sniped_message.content,
                timestamp=sniped_message.created_at,
            )
            result.set_author(
                name=sniped_message.author.display_name,
                icon_url=sniped_message.author.avatar.url,
            )
            try:
                result.set_image(
                    url=self.delete_snipes_attachments[inter.channel][0].url
                )
            except:
                pass
            is_staff = disnake.utils.find(
                lambda r: r.name.lower() == "staff", inter.guild.roles
            )
            if is_staff in inter.author.roles:
                await inter.send(embed=result)
            else:
                await inter.send(embed=result, delete_after=15)

    @commands.slash_command(
        name="editsnipe",
        description="Get the most recently edited message in the channel, before and after.",
    )
    async def editsnipe(self, inter: ApplicationCommandInteraction):
        try:
            before, after = self.edit_snipes[inter.channel]
        except KeyError:
            await inter.send("There are no message edits in this channel to snipe!")
        else:
            result = disnake.Embed(color=disnake.Color.red(), timestamp=after.edited_at)
            result.add_field(name="Before", value=before.content, inline=False)
            result.add_field(name="After", value=after.content, inline=False)
            result.set_author(
                name=after.author.display_name, icon_url=after.author.avatar.url
            )
            is_staff = disnake.utils.find(
                lambda r: r.name.lower() == "staff", inter.guild.roles
            )
            if is_staff in inter.author.roles:
                await inter.send(embed=result)
            else:
                await inter.send(embed=result, delete_after=15)


def setup(bot: commands.Bot):
    bot.add_cog(Utilities(bot))
