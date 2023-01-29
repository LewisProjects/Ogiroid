import asyncio
import datetime as dt

import disnake
from disnake import (
    TextInputStyle,
    PartialEmoji,
    Color,
    ApplicationCommandInteraction,
    Option,
)
from disnake.ext import commands
from disnake.ext.commands import ParamInfo

from utils.DBhandlers import RolesHandler, WarningHandler
from utils.bot import OGIROID
from utils.exceptions import ReactionAlreadyExists, ReactionNotFound
from utils.shortcuts import sucEmb, errorEmb, warning_embed, QuickEmb, warnings_embed


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
        self.warning: WarningHandler = None

    @commands.Cog.listener()
    async def on_ready(self):
        self.reaction_roles: RolesHandler = RolesHandler(self.bot, self.bot.db)
        self.warning: WarningHandler = WarningHandler(self.bot, self.bot.db)
        await self.reaction_roles.startup()

    @commands.slash_command(name="ban", description="Bans a user from the server.")
    @commands.has_permissions(ban_members=True)
    @commands.guild_only()
    async def ban(
        self,
        inter: ApplicationCommandInteraction,
        user: disnake.User,
        reason: str = None,
        delete_messages: int = ParamInfo(
            description="How many days of messages to delete.",
            default=0,
            choices=[0, 1, 2, 3, 4, 5, 6, 7],
        ),
    ):
        """Bans a user from the server."""
        await inter.guild.ban(
            user=user,
            reason=reason,
            clean_history_duration=dt.timedelta(days=delete_messages),
        )
        await sucEmb(inter, "User has been banned successfully!")

    @commands.slash_command(
        name="softban", description="Softbans a user from the server."
    )
    @commands.has_permissions(ban_members=True)
    @commands.guild_only()
    async def softban(
        self,
        inter: ApplicationCommandInteraction,
        user: disnake.User,
        reason: str = None,
    ):
        """Bans a user from the server."""
        await inter.guild.ban(
            user=user,
            reason=reason or "softban",
            clean_history_duration=dt.timedelta(days=7),
        )
        await sucEmb(inter, "User has been softbanned successfully!")
        await asyncio.sleep(5)
        await inter.guild.unban(user=user, reason="softban unban")

    @commands.slash_command(name="kick", description="Kicks a user from the server.")
    @commands.has_permissions(kick_members=True)
    @commands.guild_only()
    async def kick(
        self,
        inter: ApplicationCommandInteraction,
        member: disnake.Member,
        reason: str = None,
    ):
        """Kicks a user from the server."""
        await member.kick(reason=reason)
        await sucEmb(inter, "User has been kicked successfully!")

    @commands.slash_command(name="unban", description="Unbans a user from the server.")
    @commands.has_permissions(ban_members=True)
    @commands.guild_only()
    async def unban(
        self, inter: ApplicationCommandInteraction, user_id, reason: str = None
    ):
        """Unbans a user from the server."""
        try:
            await inter.guild.unban(disnake.Object(id=int(user_id)), reason=reason)
        except ValueError:
            return await errorEmb(inter, "Invalid user ID!")
        except disnake.errors.NotFound:
            return await errorEmb(inter, "User not found or not banned!")

        await sucEmb(inter, "User has been unbanned successfully!")

    @commands.slash_command(
        name="mute", description="'timeout's a user from the server."
    )
    @commands.has_permissions(moderate_members=True)
    @commands.guild_only()
    async def mute(
        self,
        inter: ApplicationCommandInteraction,
        member: disnake.Member,
        duration: str = ParamInfo(description="Format: 1s, 1m, 1h, 1d, max: 28d"),
        reason: str = None,
    ):
        """Mutes a user from the server."""
        if duration.lower() == "max":
            duration = "28d"

        try:
            if "d" in duration:
                duration = dt.timedelta(days=float(duration.split("d")[0]))
                if duration > dt.timedelta(days=28):
                    return await errorEmb(inter, "Duration is too long!")
            elif "h" in duration:
                duration = dt.timedelta(hours=float(duration.split("h")[0]))
            elif "m" in duration:
                duration = dt.timedelta(minutes=float(duration.split("m")[0]))
            elif "s" in duration:
                duration = dt.timedelta(seconds=float(duration.split("s")[0]))
        except ValueError:
            return await errorEmb(inter, "Invalid duration!")

        try:
            await member.timeout(reason=reason, duration=duration)
        except ValueError:
            return await errorEmb(inter, "Invalid duration!")
        except disnake.errors.NotFound:
            return await errorEmb(inter, "User not found or not banned!")
        except disnake.HTTPException as e:
            return await errorEmb(inter, e.text)

        await sucEmb(inter, "User has been muted successfully!")

    @commands.slash_command(
        name="unmute", description="Unmutes a user from the server."
    )
    @commands.has_permissions(moderate_members=True)
    @commands.guild_only()
    async def unmute(
        self,
        inter: ApplicationCommandInteraction,
        member: disnake.Member,
        reason: str = None,
    ):
        """Unmutes a user from the server."""
        try:
            await member.timeout(reason=reason, duration=None)
        except disnake.errors.NotFound:
            return await errorEmb(inter, "User not found or not muted!")
        except disnake.HTTPException as e:
            return await errorEmb(inter, e.text)

        await sucEmb(inter, "User has been unmuted successfully!")

    @commands.slash_command(name="warn", description="Warns a user from the server.")
    @commands.has_permissions(manage_roles=True)
    @commands.guild_only()
    async def warn(
        self,
        inter: ApplicationCommandInteraction,
        member: disnake.Member,
        reason: str = None,
    ):
        """Warns a user from the server."""
        await self.warning.create_warning(
            member.id, reason, moderator_id=inter.author.id, guild_id=inter.guild.id
        )
        await warning_embed(inter, user=member, reason=reason)

    @commands.slash_command(
        name="removewarning",
        description="Removes a warning from a user from the server.",
    )
    @commands.has_permissions(manage_roles=True)
    @commands.guild_only()
    async def remove_warning(
        self, inter: ApplicationCommandInteraction, member: disnake.Member
    ):
        """Removes a warning from a user from the server."""
        warnings = await self.warning.get_warnings(member.id, inter.guild.id)
        if len(warnings) == 0:
            return await errorEmb(inter, "User has no warnings!")
        elif len(warnings) == 1:
            status = await self.warning.remove_warning(
                warnings[0].warning_id, inter.guild.id
            )
            if status:
                await sucEmb(inter, "Warning has been removed successfully!")
            else:
                await errorEmb(inter, "Warning could not be removed!")
        else:
            await warnings_embed(inter, member=member, warnings=warnings)
            temp_msg = await inter.channel.send(
                embed=disnake.Embed(
                    title="Reply with the index of the warning to remove",
                    color=0x00FF00,
                )
            )

            def check(m):
                return m.author == inter.author and m.channel == inter.channel

            try:
                msg = await self.bot.wait_for("message", check=check, timeout=60)
            except asyncio.TimeoutError:
                return await errorEmb(inter, "Timed out!")

            id = int(msg.content)
            if id > len(warnings) or id < 1:
                return await errorEmb(inter, "Invalid warning index!")

            status = await self.warning.remove_warning(
                warnings[id - 1].warning_id, inter.guild.id
            )
            if status:
                await sucEmb(inter, "Warning has been removed successfully!")
            else:
                await errorEmb(inter, "Warning could not be removed!")

            # Delete the messages
            await temp_msg.delete()
            original_message = await inter.original_message()
            await original_message.delete()
            await msg.delete()

    @commands.slash_command(
        name="warnings", description="Shows the warnings of a user from the server."
    )
    @commands.has_permissions(manage_roles=True)
    @commands.guild_only()
    async def warnings(
        self, inter: ApplicationCommandInteraction, member: disnake.Member
    ):
        """Shows the warnings of a user from the server."""
        warnings = await self.warning.get_warnings(member.id, inter.guild.id)
        if not warnings:
            return await QuickEmb(inter, "User has no warnings!").send()

        await warnings_embed(inter, member=member, warnings=warnings)

    @commands.slash_command(description="Steals an emoji from a different server.")
    @commands.guild_only()
    @commands.has_permissions(manage_emojis=True)
    async def stealemoji(
        self,
        inter: ApplicationCommandInteraction,
        emoji: disnake.PartialEmoji,
        name=Option(name="name", required=False, description="Name of the emoji"),
    ):
        """This clones a specified emoji that optionally only specified roles
        are allowed to use.
        """
        # fetch the emoji asset and read it as bytes.
        # the key parameter here is `roles`, which controls
        # what roles are able to use the emoji.
        try:
            emoji_bytes = await emoji.read()
            await inter.guild.create_custom_emoji(
                name=name if name else emoji.name,
                image=emoji_bytes,
                reason=f"Emoji yoinked by {inter.author} VIA {inter.guild.me.name}",
            )
            await inter.send(
                embed=disnake.Embed(
                    description=f"emoji successfully stolen", color=Color.random()
                ).set_image(url=emoji.url)
            )
        except Exception as e:
            await inter.send(str(e))

    @commands.slash_command(description="Adds an image to the server emojis")
    @commands.guild_only()
    @commands.has_permissions(manage_emojis=True)
    async def addemoji(
        self,
        inter: ApplicationCommandInteraction,
        name: str,
        input_type: str = commands.Param(
            choices=["file(image)", "url(image)"], description="What you will input."
        ),
    ):
        """Adds an image to the server emojis"""
        await inter.send(f"Please send the {input_type} now")
        try:
            msg = await self.bot.wait_for(
                "message",
                check=lambda m: m.author == inter.author and m.channel == inter.channel,
            )
        except asyncio.TimeoutError:
            return await inter.send("Timed out!")

        image = None

        if input_type == "url(image)":
            response = await self.bot.session.get(
                msg.content.strip().replace("webp", "png")
            )
            response_bytes = await response.read()
            image = response_bytes

        elif input_type == "file(image)":
            image = await msg.attachments[0].read()

        try:
            await inter.guild.create_custom_emoji(
                name=name,
                image=image,
                reason=f"Emoji added by {inter.author}",
            )
            await sucEmb(inter, "Emoji added successfully!", ephemeral=False)
        except ValueError:
            pass

    @commands.slash_command(name="prune")
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def prune(self, inter: ApplicationCommandInteraction, amount: int):
        """Delete messages, max limit set to 25."""
        # Checking if amount > 25:
        if amount > 25:
            await inter.send("Amount is too high, please use a lower amount")
            return
        await inter.channel.purge(limit=amount)
        await inter.send(f"Deleted {amount} messages successfully!", ephemeral=True)

    @commands.slash_command(name="channellock")
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    async def channellock(
        self, inter: ApplicationCommandInteraction, channel: disnake.TextChannel = None
    ):
        """Lock a channel"""
        # Lock's a channel by not letting anyone send messages to it
        if channel is None:
            channel = inter.channel
        await channel.set_permissions(
            inter.guild.default_role,
            send_messages=False,
            create_public_threads=False,
            create_private_threads=False,
            send_messages_in_threads=False,
        )
        await inter.send(f"🔒 Locked {channel.mention} successfully!")

    @commands.slash_command(name="channelunlock")
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    async def channelunlock(
        self, inter: ApplicationCommandInteraction, channel: disnake.TextChannel = None
    ):
        """Unlock a channel"""
        # Unlock's a channel by letting everyone send messages to it
        if channel is None:
            channel = inter.channel
        await channel.set_permissions(
            inter.guild.default_role,
            send_messages=True,
            create_public_threads=True,
            create_private_threads=True,
            send_messages_in_threads=True,
        )
        await inter.send(f"🔓 Unlocked {channel.mention} successfully!")

    # Reaction Roles with buttons:
    @commands.slash_command(
        name="addreactionrole", description="Add a reaction based role to a message"
    )
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    async def add_reaction_role(
        self,
        inter: ApplicationCommandInteraction,
        message_id,
        emoji: str,
        role: disnake.Role,
    ):
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

    @commands.slash_command(
        name="removereactionrole",
        description="Remove a reaction based role from a message",
    )
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    async def remove_reaction_role(
        self, inter, message_id, emoji: str, role: disnake.Role
    ):
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
            if (
                payload.message_id == message.message_id
                and emoji == PartialEmoji.from_str(message.emoji)
            ):
                await self.reaction_roles.increment_roles_given(
                    payload.message_id, message.emoji
                )
                guild = self.bot.get_guild(payload.guild_id)
                await guild.get_member(payload.user_id).add_roles(
                    guild.get_role(message.role_id)
                )

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        emoji = PartialEmoji(name=payload.emoji.name, id=payload.emoji.id)
        for message in self.reaction_roles.messages:
            if (
                payload.message_id == message.message_id
                and emoji == PartialEmoji.from_str(message.emoji)
            ):
                guild = self.bot.get_guild(payload.guild_id)
                await guild.get_member(payload.user_id).remove_roles(
                    guild.get_role(message.role_id)
                )

    @commands.slash_command(
        name="initialise-message",
        description="Create a Message with Buttons where users click them and get roles.",
    )
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    async def initialise_message(  # todo create better cmd and clean this section up.
        self,
        inter: disnake.ApplicationCommandInteraction,
        emoji: str = ParamInfo(
            description="The emoji to be on the button. You can add more later."
        ),
        color=ParamInfo(
            choices=["blurple", "grey", "red", "green"],
            description="Color of the button.",
        ),
        role: disnake.Role = ParamInfo(
            description="The role to be given when clicked."
        ),
        channel: disnake.TextChannel = ParamInfo(
            channel_types=[disnake.ChannelType.text],
            description="The channel where the message is sent.",
        ),
    ):
        def check(m):
            return m.author == inter.author and m.channel == inter.channel

        await inter.send("Please send the message", ephemeral=True)

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=300.0)
        except asyncio.exceptions.TimeoutError:
            return await errorEmb(
                inter, "Due to no response the operation was canceled"
            )

        await msg.delete()

        text = msg.content

        emoji = PartialEmoji.from_str(emoji.strip())

        if emoji is None:
            return await errorEmb(inter, "The emoji is invalid")

        button = disnake.ui.Button(
            emoji=emoji,
            custom_id=f"{role.id}-{emoji.name if emoji.is_unicode_emoji() else emoji.id}",
            style=disnake.ButtonStyle[color],
        )
        view = disnake.ui.View()
        view.add_item(button)
        msg = await channel.send(text, view=view)

        await self.reaction_roles.create_message(msg.id, role.id, str(emoji))

        await sucEmb(
            inter, "Successfully created message. To add more buttons use `/add_button`"
        )

    @commands.slash_command(
        name="add-button",
        description="Add a button to a previously created message."
        " Use /initialise-message for that.",
    )
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    async def add_button(
        self,
        inter,
        message_id,
        new_emoji: str,
        role: disnake.Role,
        color=ParamInfo(
            choices=["blurple", "grey", "red", "green"],
            description="Color of the button.",
        ),
        channel: disnake.TextChannel = ParamInfo(
            channel_types=[disnake.ChannelType.text],
            description="The channel where the message is sent.",
        ),
    ):

        emoji = PartialEmoji.from_str(new_emoji.strip())
        message_id = int(message_id)

        if emoji is None:
            return await errorEmb(inter, "The emoji is invalid")

        exists = False
        for message in self.reaction_roles.messages:
            if (
                message.message_id == message_id
                and PartialEmoji.from_str(message.emoji) == emoji
                and message.role_id == role.id
            ):
                return await errorEmb(
                    inter, "Such a button already exists on the message."
                )
            elif message.message_id == message_id:
                exists = True

        if not exists:
            return await errorEmb(inter, "The message does not exist.")

        message = await channel.fetch_message(message_id)
        if message is None:
            return await errorEmb(inter, "The message does not exist.")

        components = disnake.ui.View.from_message(message)

        custom_id = f"{role.id}-{emoji.name if emoji.is_unicode_emoji() else emoji.id}"

        new_button = disnake.ui.Button(
            emoji=emoji, custom_id=custom_id, style=disnake.ButtonStyle[color]
        )

        components.add_item(new_button)
        try:
            await self.reaction_roles.create_message(message.id, role.id, str(emoji))
        except ReactionAlreadyExists:
            return await errorEmb(inter, "This Reaction already exists")

        await message.edit(view=components)

        await sucEmb(inter, "Added Button")

    @commands.slash_command(
        name="edit-message",
        description="Edit a message the bot sent(Role messages with buttons only).",
    )
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    async def edit_message(self, inter, message_id, channel: disnake.TextChannel):
        exists = False
        message_id = int(message_id)
        for message in self.reaction_roles.messages:
            if message_id == message.message_id:
                exists = True

        if not exists:
            return await errorEmb(
                inter,
                "The message does not exist in the Database to initialise a message use"
                " ``/initialise-message``.",
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
            return await errorEmb(
                inter, "Due to no response the operation was canceled"
            )

        await msg.delete()

        text = msg.content

        try:
            await message.edit(content=text)
        except disnake.errors.Forbidden or disnake.errors.HTTPException:
            return await errorEmb(
                inter, "I do not have permission to edit this message."
            )

        await sucEmb(inter, "Edited!")

    @commands.slash_command(
        name="delete-message",
        description="Delete a message the bot sent(Role messages with buttons only).",
    )
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    async def delete_message(self, inter, message_id, channel: disnake.TextChannel):
        exists = False
        message_id = int(message_id)
        for message in self.reaction_roles.messages:
            if message_id == message.message_id:
                exists = True

        if not exists:
            return await errorEmb(
                inter,
                "The message does not exist in the Database to initialise a message use"
                " ``/initialise-message``.",
            )

        await self.reaction_roles.remove_messages(message_id)

        message = await channel.fetch_message(message_id)
        if message is None:
            return await errorEmb(inter, "Message not found!")

        try:
            await message.delete()
        except disnake.errors.Forbidden or disnake.errors.HTTPException:
            return await errorEmb(
                inter, "I do not have permission to delete this message."
            )

        await sucEmb(inter, "Deleted!")

    @commands.slash_command(
        name="remove-button", description="Remove a button from a message."
    )
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    async def remove_button(
        self,
        inter,
        message_id,
        emoji: str,
        channel: disnake.TextChannel,
        role: disnake.Role,
    ):
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
            if (
                button.custom_id
                == f"{role.id}-{emoji.name if emoji.is_unicode_emoji() else emoji.id}"
            ):
                message_components.remove_item(button)
                break

        await message.edit(view=message_components)
        await sucEmb(inter, "Removed Button")

    @commands.Cog.listener("on_button_click")
    async def button_click(self, inter):
        message = inter.message
        emoji = inter.component.emoji
        guild = inter.guild

        try:
            role_id = int(inter.component.custom_id.split("-")[0])
            role = guild.get_role(role_id)
            if role is None:
                return
            if "-" not in inter.component.custom_id:
                return
        except ValueError:
            return

        if not await self.reaction_roles.exists(message.id, str(emoji), role_id):
            return await errorEmb(inter, "This doesnt exists in the database")

        await self.reaction_roles.increment_roles_given(message.id, str(emoji))

        member = guild.get_member(inter.user.id)

        if member.get_role(role_id) is None:
            await member.add_roles(
                role, reason=f"Clicked button to get role. gave {role.name}"
            )
            await self.reaction_roles.increment_roles_given(message.id, str(emoji))
            return await sucEmb(inter, f"Added Role {role.mention}")
        else:
            await member.remove_roles(
                role,
                reason=f"Clicked button while already having the role. removed {role.name}",
            )
            return await sucEmb(inter, f"Removed Role {role.mention}")

    @commands.slash_command(name="staffvote", description="Propose a Staff Vote.")
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    async def staffvote(self, inter):  # todo remove
        """Propose a Staff Vote."""
        await inter.response.send_modal(modal=StaffVote(self.bot))

    @commands.slash_command(
        name="staffhelp", description="Get the help for the staff commands."
    )
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    async def staffhelp(self, inter):
        """Get the help for the staff commands."""
        staff_commands = commands.Cog.get_slash_commands(self)
        emb = disnake.Embed(
            title="Staff Commands", description="All staff commands", color=0xFFFFFF
        )
        for command in staff_commands:
            emb.add_field(
                name=f"/{command.qualified_name}",
                value=command.description,
                inline=False,
            )

        await inter.send(embed=emb)


def setup(bot):
    bot.add_cog(Staff(bot))
