import disnake
from disnake.ext import commands
import aiohttp
from disnake.ext.commands.cooldowns import BucketType
from disnake.ext.commands import Cog


class Utilities(commands.Cog):
    def __init__(self, bot: commands.Bot):
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

    @commands.slash_command(name="snipe", description="Get the most recently deleted message in a channel")
    async def snipe_group(self, ctx):
        """Get the most recently deleted message in a channel"""

        try:
            sniped_message = self.delete_snipes[ctx.channel]
        except KeyError:
            await ctx.send("There are no deleted messages in this channel to snipe!")
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
                result.set_image(url=self.delete_snipes_attachments[ctx.channel][0].url)
            except:
                pass
            await ctx.send(embed=result)

    @commands.slash_command(
        name="editsnipe",
        description="Get the most recently edited message in the channel, before and after.",
    )
    async def editsnipe(self, ctx):
        try:
            before, after = self.edit_snipes[ctx.channel]
        except KeyError:
            await ctx.send("There are no message edits in this channel to snipe!")
        else:
            result = disnake.Embed(color=disnake.Color.red(), timestamp=after.edited_at)
            result.add_field(name="Before", value=before.content, inline=False)
            result.add_field(name="After", value=after.content, inline=False)
            result.set_author(name=after.author.display_name, icon_url=after.author.avatar.url)
            await ctx.send(embed=result)


def setup(bot: commands.Bot):
    bot.add_cog(Utilities(bot))
