from turtle import title
import disnake
from disnake.ext import commands
from disnake import TextInputStyle, Color
from disnake.ext import commands

from utils.bot import OGIROID
from utils.shortcuts import sucEmb, errorEmb
from utils.DBhandelers import RolesHandler
from utils.exceptions import ReactionAlreadyExists


class StaffVote(disnake.ui.Modal):
    def __init__(self, bot: OGIROID):
        # The details of the modal, and its components
        self.bot = bot
        components = [
            disnake.ui.TextInput(
                label="Title of the vote:",
                placeholder="This vote is about...",
                custom_id="staff_vote_title",
                style=TextInputStyle.short,
                max_length=16,
            ),
            disnake.ui.TextInput(
                label="Proposition of the vote:",
                placeholder="I propose to...",
                custom_id="staff_vote_proposition",
                style=TextInputStyle.paragraph,
                max_length=512,
            ),
        ]
        super().__init__(
            title="Staff Vote",
            custom_id="staff_vote",
            components=components,
        )

    #callback recieved when the user input is completed
    async def callback(self, inter: disnake.ModalInteraction):
        embed = disnake.Embed(title=(inter.text_values["staff_vote_title"]), description=(inter.text_values["staff_vote_proposition"]), color=0xFFFFFF)
        embed.set_footer(text="Started by: {}".format(inter.author.name))
        # Sending the Embed to the channel.
        staff_vote = self.bot.get_channel(self.bot.config.channels.staff_vote)
        embed_msg = await staff_vote.send(embed=embed)
        reactions = ["✅", "❌"]
        for reaction in reactions:  # adding reactions to embed_msg
            await embed_msg.add_reaction(reaction)
        await sucEmb(inter, "Your vote has been started successfully!")


class Staff(commands.Cog):
    """Commands for the staff team!\n\n"""

    def __init__(self, bot: OGIROID):
        self.bot = bot
        self.reaction_roles: RolesHandler = None

    @commands.Cog.listener()
    async def on_ready(self):
        self.reaction_roles: RolesHandler = RolesHandler(self.bot, self.bot.db)
        await self.reaction_roles.startup()

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

    #Reaction Roles with buttons:
    @commands.slash_command(name="addreactionrole", description="Add a reaction based role to a message")
    @commands.guild_only()
    @commands.has_role("Staff")
    async def add_reaction_role(self, inter, message_id, emoji: str, role: disnake.Role):
        # Reaction Role command for the staff team
        # Checking if the message exists:
        message_id = int(message_id)
        message = await inter.channel.fetch_message(message_id)
        if message is None:
            return await errorEmb(inter, "Message not found!")

        try:
            await self.reaction_roles.create_message(message_id, role.id, emoji)
        except ReactionAlreadyExists:
            return await errorEmb(inter, "Reaction already exists!")

        await message.add_reaction(emoji)

        await sucEmb(inter, f"Added!")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        for message in self.reaction_roles.messages:
            if payload.message_id == message.message_id and payload.emoji.name == message.emoji:
                await self.reaction_roles.increment_roles_given(payload.message_id, message.emoji)
                guild = self.bot.get_guild(payload.guild_id)
                await guild.get_member(payload.user_id).add_roles(guild.get_role(message.role_id))

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        for message in self.reaction_roles.messages:
            if payload.message_id == message.message_id and payload.emoji.name == message.emoji:
                guild = self.bot.get_guild(payload.guild_id)
                await guild.get_member(payload.user_id).remove_roles(guild.get_role(message.role_id))

    @commands.slash_command(name="staffvote", description="Propose a Staff Vote.")
    @commands.guild_only()
    @commands.has_role("Staff")
    async def staffvote(self, ctx):
        """Propose a Staff Vote."""
        await ctx.response.send_modal(modal=StaffVote(self.bot))


def setup(bot):
    bot.add_cog(Staff(bot))
