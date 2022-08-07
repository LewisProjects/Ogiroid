import disnake
from disnake.ext import commands

from utils.bot import OGIROID


class Staff(commands.Cog):
    """Commands for the staff team!\n\n"""

    def __init__(self, bot: OGIROID):
        self.bot = bot

    @commands.slash_command(name="faq")
    @commands.guild_only()
    @commands.has_role("Staff")
    async def faq(self, ctx, person: disnake.Member):
        """FAQ command for the staff team"""
        channel = self.bot.get_channel(self.bot.config.channels.reddit_faq)
        await channel.send(f"{person.mention}", delete_after=2)
        # Sending Done so this Application didn't respond error can be avoided
        await ctx.send("Done", delete_after=1)

    @commands.slash_command(name="prune")
    @commands.guild_only()
    @commands.has_role("Staff")
    async def prune(self, ctx, amount: int):
        """Delete messages, max limit set to 25."""
        # Checking if amount > 25:
        if amount > 25:
            await ctx.send("Amount is too high, please use a lower amount")
            return
        await ctx.channel.purge(limit=amount)
        await ctx.send(f"Deleted {amount} messages successfully!", ephemeral=True)

    @commands.slash_command(name="channellock")
    @commands.guild_only()
    @commands.has_role("Staff")
    async def channellock(self, ctx, channel: disnake.TextChannel):
        """Lock a channel"""
        # Lock's a channel by not letting anyone send messages to it
        await channel.set_permissions(ctx.guild.default_role, send_messages=False)
        await ctx.send(f"🔒 Locked {channel.mention} successfully!")

    @commands.slash_command(name="channelunlock")
    @commands.guild_only()
    @commands.has_role("Staff")
    async def channelunlock(self, ctx, channel: disnake.TextChannel):
        """Unlock a channel"""
        # Unlock's a channel by letting everyone send messages to it
        await channel.set_permissions(ctx.guild.default_role, send_messages=True)
        await ctx.send(f"🔓 Unlocked {channel.mention} successfully!")

    """#Reaction Roles with buttons:
    @commands.slash_command(name="reactionrole")
    @commands.guild_only()
    @commands.has_role("Staff")
    async def reactionrole(self, ctx, message_id: str, button_name: str, emoji: str, role: disnake.Role):
        # Reaction Role command for the staff team
        # Checking if the message exists:
        message = await ctx.channel.fetch_message(message_id)
        if message is None:
            await ctx.send("Message not found!")
            return
        # Creating a button class for the message:
        button = disnake.Button(button_name, emoji, role)
        # Adding the button to the message:
        self.bot.buttons.append(button)
        await ctx.send(f"Added!")"""
    
    @commands.slash_command(name="staffvote")
    @commands.guild_only()
    @commands.has_role("Staff")
    async def staffvote(self, ctx, title:str, proposition:str):
        """Staff vote command"""
        channel = self.bot.get_channel(1002132747441152071)
        #We will change the channel ID later to "1005741491861344286".
        #Creating an Embed!
        embed = disnake.Embed(title=f"Title: {title}", description=f"Proposition: {proposition}")
        embed.set_footer(text="Started by: {}".format(ctx.author.name))
        #Sending the Embed to the channel.
        embed_msg = await channel.send(embed=embed)
        reactions = ["✅", "❌"]
        for reaction in reactions: #adding reactions to embed_msg
            await embed_msg.add_reaction(reaction)
        await ctx.send("Your vote has been started successfully!", delete_after=3)

        


def setup(bot):
    bot.add_cog(Staff(bot))
