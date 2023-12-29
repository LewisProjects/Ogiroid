import asyncio
from datetime import datetime

import disnake
from disnake.ext import commands

from utils.CONSTANTS import TICKET_PERMS
from utils.bot import OGIROID
from utils.shortcuts import errorEmb, sucEmb


class Tickets(commands.Cog):
    """🎫 Ticketing system commands (Staff)"""

    def __init__(self, bot: OGIROID):
        self.message = None
        self.bot = bot
        self.ticket_channel = self.bot.config.channels.tickets

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.bot.ready_:
            ticket_channel = self.bot.get_channel(self.ticket_channel)

            exists = False
            async for channel_message in ticket_channel.history(limit=100):
                if channel_message.author.id == self.bot.application_id:
                    self.message = channel_message
                    exists = True
                    break

            if not exists:
                await self.send_message()

    async def send_message(self):
        ticket_channel = self.bot.get_channel(self.ticket_channel)
        await ticket_channel.send(
            "Create a Ticket.",
            components=disnake.ui.Button(
                emoji=disnake.PartialEmoji.from_str("📩"),
                label="Create a Ticket",
                custom_id="ticket_button",
            ),
        )

    @commands.slash_command(
        name="edit-ticket-message", description="Update the ticket message."
    )
    @commands.guild_only()
    @commands.has_role("Staff")
    async def edit_ticket_message(self, inter):
        await inter.send("Please send the new message", ephemeral=True)

        def check(m):
            return m.author == inter.author and m.channel == inter.channel

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=300.0)
        except asyncio.exceptions.TimeoutError:
            return await errorEmb(
                inter, "Due to no response the operation was canceled"
            )

        await msg.delete()

        text = msg.content

        try:
            await self.message.edit(content=text)
        except disnake.errors.Forbidden or disnake.errors.HTTPException:
            return await errorEmb(
                inter, "I do not have permission to edit this message."
            )

        await sucEmb(inter, "Edited!")

    @commands.Cog.listener("on_button_click")
    async def on_button_click(self, inter):
        ticket_channel = self.bot.get_channel(self.ticket_channel)
        category = ticket_channel.category
        guild = self.bot.get_guild(inter.guild_id)
        user = guild.get_member(inter.author.id)
        if user.id == self.bot.application_id:
            return print("Added reaction from bot")
        if not inter.component.custom_id == "ticket_button":
            return

        staff = guild.get_role(self.bot.config.roles.staff)

        # checks if user has a ticket already open
        for channel in guild.channels:
            try:
                if int(channel.name.strip().replace("ticket-", "")) == int(user.id):
                    await errorEmb(
                        inter,
                        "You already have a ticket open. Please close it before opening a new one",
                    )
                    return
            except ValueError:
                pass

        ticket = await category.create_text_channel(f"ticket-{user.id}")
        await ticket.edit(topic=f"Ticket opened by {user.name}.")
        await ticket.set_permissions(
            inter.guild.get_role(inter.guild.id), read_messages=False
        )
        await ticket.set_permissions(user, **TICKET_PERMS)
        await ticket.set_permissions(staff, **TICKET_PERMS)
        message_content = "Thank you for contacting support! A staff member will be here shortly!\nTo close the the ticket use ``/close``"
        em = disnake.Embed(
            title=f"Ticket made by {user.name}",
            description=f"{message_content}",
            color=0x26FF00,
        )
        em.set_footer(text=f"{user}")
        em.timestamp = datetime.now()
        await ticket.send(embed=em)
        await inter.send(
            f"Created Ticket. Your ticket: {ticket.mention}", ephemeral=True
        )

    @commands.slash_command(description="Close ticket")
    async def close(self, inter):
        await inter.response.defer()
        if self.check_if_ticket_channel(inter):
            # send log of chat in ticket to log channel
            log_channel = self.bot.get_channel(self.bot.config.channels.logs)
            log_emb = disnake.Embed(
                title=f"Ticket closed by {inter.author.name}",
                description=f"Ticket closed by {inter.author.mention}",
                color=self.bot.config.colors.white,
            )
            # get all users in ticket channel
            user_text = ""
            for user in inter.channel.members:
                user_text += f"{user.mention} "

            log_emb.add_field(name="Users in Channel", value=user_text, inline=False)

            # get all messages in ticket channel
            fields = 2
            async for message in inter.channel.history(limit=100, oldest_first=True):
                if fields == 25:
                    await log_channel.send(embed=log_emb)
                    log_emb = disnake.Embed(
                        color=self.bot.config.colors.white,
                    )
                    fields = 0
                log_emb.add_field(
                    name=f"{message.author.name}",
                    value=message.content[:1024],
                    inline=False,
                )
                if len(message.content) > 1024:
                    log_emb.add_field(
                        name=f"{message.author.name} (cont.)",
                        value=message.content[1024:2048],
                        inline=False,
                    )
                fields += 1
            log_emb.set_footer(text=f"{inter.author}")
            log_emb.timestamp = datetime.now()
            await log_channel.send(embed=log_emb)
            await inter.channel.delete()
        else:
            await errorEmb(inter, "This is not a ticket channel.")

    @commands.slash_command(name="adduser", description="Add user to channel")
    @commands.has_role("Staff")
    async def add_user(self, inter, member: disnake.Member):
        if self.check_if_ticket_channel(inter):
            await inter.channel.set_permissions(
                member,
                send_messages=True,
                read_messages=True,
                add_reactions=True,
                embed_links=True,
                attach_files=True,
                read_message_history=True,
                external_emojis=True,
            )
            em = disnake.Embed(
                title="Add",
                description=f"{inter.author.mention} has added {member.mention} to {inter.channel.mention}",
            )
            await inter.send(embed=em)
        else:
            await errorEmb(inter, "This is not a ticket channel.")

    @commands.slash_command(name="removeuser", description="Remove user from channel")
    @commands.has_role("Staff")
    async def remove_user(self, inter, member: disnake.Member):
        if self.check_if_ticket_channel(inter):
            await inter.channel.set_permissions(member, overwrite=None)
            em = disnake.Embed(
                title="Remove",
                description=f"{inter.author.mention} has removed {member.mention} from {inter.channel.mention}",
            )
            await inter.send(embed=em)
        else:
            await errorEmb(inter, "This is not a ticket channel.")

    @staticmethod
    def check_if_ticket_channel(inter):
        if (
            "ticket-" in inter.channel.name
            and len(inter.channel.name) > 10
            and any(char.isdigit() for char in inter.channel.name)
        ):
            return True
        else:
            return False


def setup(bot: OGIROID):
    bot.add_cog(Tickets(bot))
