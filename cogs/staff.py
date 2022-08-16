import asyncio

import disnake
from disnake import TextInputStyle, PartialEmoji
from disnake.ext import commands
from disnake.ext.commands import ParamInfo

from utils.DBhandlers import RolesHandler
from utils.bot import OGIROID
from utils.exceptions import ReactionAlreadyExists, ReactionNotFound
from utils.shortcuts import sucEmb, errorEmb


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

    # callback recieved when the user input is completed
    async def callback(self, inter: disnake.ModalInteraction):
        embed = disnake.Embed(
            title=(inter.text_values["staff_vote_title"]),
            description=(inter.text_values["staff_vote_proposition"]),
            color=0xFFFFFF,
        )
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

    @commands.slash_command(name="ban", description="Bans a user from the server.")
    @commands.has_permissions(ban_members=True)
    @commands.guild_only()
    async def ban(self, inter, member: disnake.Member, reason: str = None):
        """Bans a user from the server."""
        await member.ban(reason=reason)
        await sucEmb(inter, "User has been banned successfully!")

    @commands.slash_command(name="kick", description="Kicks a user from the server.")
    @commands.has_permissions(kick_members=True)
    @commands.guild_only()
    async def kick(self, inter, member: disnake.Member, reason: str = None):
        """Kicks a user from the server."""
        await member.kick(reason=reason)
        await sucEmb(inter, "User has been kicked successfully!")

    @commands.slash_command(name="unban", description="Unbans a user from the server.")
    @commands.has_permissions(ban_members=True)
    @commands.guild_only()
    async def unban(self, inter, user_id, reason: str = None):
        """Unbans a user from the server."""
        try:
            await inter.guild.unban(disnake.Object(id=int(user_id)), reason=reason)
        except ValueError:
            return await errorEmb(inter, "Invalid user ID!")
        except disnake.errors.NotFound:
            return await errorEmb(inter, "User not found or not banned!")

        await sucEmb(inter, "User has been unbanned successfully!")

    @commands.slash_command(name="faq")
    @commands.guild_only()
    @commands.has_role("Staff")
    async def faq(self, inter, person: disnake.Member):
        """FAQ command for the staff team"""
        channel = self.bot.get_channel(self.bot.config.channels.reddit_faq)
        await channel.send(f"{person.mention}", delete_after=2)
        # Sending Done so this Application didn't respond error can be avoided
        await inter.send("Done", delete_after=1)

    @commands.slash_command(name="prune")
    @commands.guild_only()
    @commands.has_role("Staff")
    async def prune(self, inter, amount: int):
        """Delete messages, max limit set to 25."""
        # Checking if amount > 25:
        if amount > 25:
            await inter.send("Amount is too high, please use a lower amount")
            return
        await inter.channel.purge(limit=amount)
        await inter.send(f"Deleted {amount} messages successfully!", ephemeral=True)

    @commands.slash_command(name="channellock")
    @commands.guild_only()
    @commands.has_role("Staff")
    async def channellock(self, inter, channel: disnake.TextChannel):
        """Lock a channel"""
        # Lock's a channel by not letting anyone send messages to it
        await channel.set_permissions(inter.guild.default_role, send_messages=False)
        await inter.send(f"🔒 Locked {channel.mention} successfully!")

    @commands.slash_command(name="channelunlock")
    @commands.guild_only()
    @commands.has_role("Staff")
    async def channelunlock(self, inter, channel: disnake.TextChannel):
        """Unlock a channel"""
        # Unlock's a channel by letting everyone send messages to it
        await channel.set_permissions(inter.guild.default_role, send_messages=True)
        await inter.send(f"🔓 Unlocked {channel.mention} successfully!")

    # Reaction Roles with buttons:
    @commands.slash_command(name="addreactionrole", description="Add a reaction based role to a message")
    @commands.guild_only()
    @commands.has_role("Staff")
    async def add_reaction_role(self, inter, message_id, emoji: str, role: disnake.Role):
        # Checking if the message exists:
        message_id = int(message_id)
        message = await inter.channel.fetch_message(message_id)
        if message is None:
            return await errorEmb(inter, "Message not found!")
        emoji = PartialEmoji.from_str(emoji)

        try:
            await self.reaction_roles.create_message(message_id, role.id, str(emoji))
        except ReactionAlreadyExists:
            return await errorEmb(inter, "Reaction already exists!")

        await message.add_reaction(emoji)

        await sucEmb(inter, f"Added!")

    @commands.slash_command(name="removereactionrole", description="Remove a reaction based role from a message")
    @commands.guild_only()
    @commands.has_role("Staff")
    async def remove_reaction_role(self, inter, message_id, emoji: str, role: disnake.Role):
        # Checking if the message exists:
        message_id = int(message_id)
        message = await inter.channel.fetch_message(message_id)
        if message is None:
            return await errorEmb(inter, "Message not found!")
        emoji = PartialEmoji.from_str(emoji)

        await message.remove_reaction(emoji, inter.author)

        try:
            await self.reaction_roles.remove_message(message_id, str(emoji), role.id)
        except ReactionNotFound:
            return await errorEmb(inter, "Reaction does not exist!")

        await sucEmb(inter, f"Removed!")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        emoji = PartialEmoji(name=payload.emoji.name, id=payload.emoji.id)
        for message in self.reaction_roles.messages:
            if payload.message_id == message.message_id and emoji == PartialEmoji.from_str(message.emoji):
                await self.reaction_roles.increment_roles_given(payload.message_id, message.emoji)
                guild = self.bot.get_guild(payload.guild_id)
                await guild.get_member(payload.user_id).add_roles(guild.get_role(message.role_id))

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        emoji = PartialEmoji(name=payload.emoji.name, id=payload.emoji.id)
        for message in self.reaction_roles.messages:
            if payload.message_id == message.message_id and emoji == PartialEmoji.from_str(message.emoji):
                guild = self.bot.get_guild(payload.guild_id)
                await guild.get_member(payload.user_id).remove_roles(guild.get_role(message.role_id))

    @commands.slash_command(
        name="initialise-message", description="Create a Message with Buttons where users click them and get roles."
    )
    @commands.guild_only()
    @commands.has_role("Staff")
    async def initialise_message(
        self,
        inter: disnake.ApplicationCommandInteraction,
        emoji: str = ParamInfo(description="The emoji to be on the button. You can add more later."),
        role: disnake.Role = ParamInfo(description="The role to be given when clicked."),
        channel: disnake.TextChannel = ParamInfo(
            channel_types=[disnake.ChannelType.text], description="The channel where the message is sent."
        ),
    ):
        def check(m):
            return m.author == inter.author and m.channel == inter.channel

        await inter.send("Please send the message", ephemeral=True)

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=300.0)
        except asyncio.exceptions.TimeoutError:
            return await errorEmb(inter, "Due to no response the operation was canceled")

        await msg.delete()

        text = msg.content

        emoji = PartialEmoji.from_str(emoji.strip())

        if emoji is None:
            return await errorEmb(inter, "The emoji is invalid")

        button = disnake.ui.Button(emoji=emoji, custom_id=f"{role.id}-{emoji.name if emoji.is_unicode_emoji() else emoji.id}")
        view = disnake.ui.View()
        view.add_item(button)
        msg = await channel.send(text, view=view)

        await self.reaction_roles.create_message(msg.id, role.id, str(emoji))

        await sucEmb(inter, "Successfully created message. To add more buttons use `/add_button`")

    @commands.slash_command(
        name="add-button", description="Add a button to a previously created message." " Use /initialise-message for that."
    )
    @commands.guild_only()
    @commands.has_role("Staff")
    async def add_button(
        self,
        inter,
        message_id,
        new_emoji: str,
        role: disnake.Role,
        channel: disnake.TextChannel = ParamInfo(
            channel_types=[disnake.ChannelType.text], description="The channel where the message is sent."
        ),
    ):

        emoji = PartialEmoji.from_str(new_emoji.strip())
        message_id = int(message_id)

        if emoji is None:
            return await errorEmb(inter, "The emoji is invalid")

        exists = False
        for message in self.reaction_roles.messages:
            if message.message_id == message_id and PartialEmoji.from_str(message.emoji) == emoji and message.role_id == role.id:
                return await errorEmb(inter, "Such a button already exists on the message.")
            elif message.message_id == message_id:
                exists = True

        if not exists:
            return await errorEmb(inter, "The message does not exist.")

        message = await channel.fetch_message(message_id)
        if message is None:
            return await errorEmb(inter, "The message does not exist.")

        components = disnake.ui.View.from_message(message)

        custom_id = f"{role.id}-{emoji.name if emoji.is_unicode_emoji() else emoji.id}"

        new_button = disnake.ui.Button(emoji=emoji, custom_id=custom_id)

        components.add_item(new_button)
        try:
            await self.reaction_roles.create_message(message.id, role.id, str(emoji))
        except ReactionAlreadyExists:
            return await errorEmb(inter, "This Reaction already exists")

        await message.edit(view=components)

        await sucEmb(inter, "Added Button")

    @commands.slash_command(name="edit-message", description="Edit a message the bot sent(Role messages with buttons only).")
    @commands.guild_only()
    @commands.has_role("Staff")
    async def edit_message(self, inter, message_id, channel: disnake.TextChannel):
        exists = False
        message_id = int(message_id)
        for message in self.reaction_roles.messages:
            if message_id == message.message_id:
                exists = True

        if not exists:
            return await errorEmb(
                inter, "The message does not exist in the Database to initialise a message use" " ``/initialise-message``."
            )

        message = await channel.fetch_message(message_id)
        if message is None:
            return await errorEmb(inter, "Message not found!")

        def check(m):
            return m.author == inter.author and m.channel == inter.channel

        await inter.send("Please send the new message", ephemeral=True)

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=300.0)
        except asyncio.exceptions.TimeoutError:
            return await errorEmb(inter, "Due to no response the operation was canceled")

        await msg.delete()

        text = msg.content

        try:
            await message.edit(content=text)
        except disnake.errors.Forbidden or disnake.errors.HTTPException:
            return await errorEmb(inter, "I do not have permission to edit this message.")

        await sucEmb(inter, "Edited!")

    @commands.slash_command(name="delete-message", description="Delete a message the bot sent(Role messages with buttons only).")
    @commands.guild_only()
    @commands.has_role("Staff")
    async def delete_message(self, inter, message_id, channel: disnake.TextChannel):
        exists = False
        message_id = int(message_id)
        for message in self.reaction_roles.messages:
            if message_id == message.message_id:
                exists = True

        if not exists:
            return await errorEmb(
                inter, "The message does not exist in the Database to initialise a message use" " ``/initialise-message``."
            )

        await self.reaction_roles.remove_messages(message_id)

        message = await channel.fetch_message(message_id)
        if message is None:
            return await errorEmb(inter, "Message not found!")

        try:
            await message.delete()
        except disnake.errors.Forbidden or disnake.errors.HTTPException:
            return await errorEmb(inter, "I do not have permission to delete this message.")

        await sucEmb(inter, "Deleted!")

    @commands.slash_command(name="remove-button", description="Remove a button from a message.")
    @commands.guild_only()
    @commands.has_role("Staff")
    async def remove_button(self, inter, message_id, emoji: str, channel: disnake.TextChannel, role: disnake.Role):
        message_id = int(message_id.strip())
        emoji = PartialEmoji.from_str(emoji.strip())

        button = await self.reaction_roles.exists(message_id, str(emoji), role.id)
        if not button:
            return await errorEmb(inter, "The button does not exist.")

        await self.reaction_roles.remove_message(message_id, str(emoji), role.id)

        message = await channel.fetch_message(message_id)

        if message is None:
            return await errorEmb(inter, "Message not found!")

        message_components = disnake.ui.View.from_message(message)

        for button in message_components.children:
            if button.custom_id == f"{role.id}-{emoji.name if emoji.is_unicode_emoji() else emoji.id}":
                message_components.remove_item(button)
                break

        await message.edit(view=message_components)
        await sucEmb(inter, "Removed Button")

    @commands.Cog.listener("on_button_click")
    async def button_click(self, inter):
        message = inter.message
        emoji = inter.component.emoji

        try:
            role_id = int(inter.component.custom_id.split("-")[0])
        except ValueError:
            return

        if not await self.reaction_roles.exists(message.id, str(emoji), role_id):
            return await errorEmb(inter, "This doesnt exists in the database")

        await self.reaction_roles.increment_roles_given(message.id, str(emoji))
        guild = inter.guild

        member = guild.get_member(inter.user.id)
        role = guild.get_role(role_id)

        if member.get_role(role_id) is None:
            await member.add_roles(role, reason=f"Clicked button to get role. gave {role.name}")
            await self.reaction_roles.increment_roles_given(message.id, str(emoji))
            return await sucEmb(inter, "Added Role")
        else:
            await member.remove_roles(role, reason=f"Clicked button while already having the role. removed {role.name}")
            return await sucEmb(inter, "Removed Role")

    @commands.slash_command(name="staffvote", description="Propose a Staff Vote.")
    @commands.guild_only()
    @commands.has_role("Staff")
    async def staffvote(self, inter):
        """Propose a Staff Vote."""
        await inter.response.send_modal(modal=StaffVote(self.bot))


def setup(bot):
    bot.add_cog(Staff(bot))
