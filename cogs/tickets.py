import disnake
from disnake.ext import commands
from utils.bot import OGIROID
from utils.CONSTANTS import STAFF_ROLE, TICKET_PERMS
from utils.shortcuts import errorEmb


class Tickets(commands.Cog):
    """🎫 Ticketing system commands (Staff)"""

    def __init__(self, bot: OGIROID):
        self.bot = bot
        self.ticket_channel = self.bot.config.channels.tickets

    @commands.Cog.listener()
    async def on_ready(self):
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
            "Create a Ticket.", components=disnake.ui.Button(label="Create a Ticket✉", custom_id="ticket_button")
        )

    @commands.Cog.listener("on_button_click")
    async def on_button_click(self, inter):
        ticket_channel = self.bot.get_channel(self.ticket_channel)
        guild = self.bot.get_guild(inter.guild_id)
        user = guild.get_member(inter.author.id)
        if user.id == self.bot.application_id:
            return print("Added reaction from bot")
        if not inter.component.custom_id == "ticket_button":
            return

        staff = guild.get_role(STAFF_ROLE)

        # checks if user has a ticket already open
        for channel in guild.channels:
            try:
                if int(channel.name.strip().replace("ticket-", "")) == int(user.id):
                    await errorEmb(inter, "You already have a ticket open. Please close it before opening a new one")
                    return
            except ValueError:
                pass

        ticket = await inter.guild.create_text_channel(f"ticket-{user.id}")
        await ticket.set_permissions(inter.guild.get_role(inter.guild.id), read_messages=False)
        await ticket.set_permissions(user, **TICKET_PERMS)
        await ticket.set_permissions(staff, **TICKET_PERMS)
        message_content = "Thank you for contacting support! A staff member will be here shortly!"
        em = disnake.Embed(
            title=f"Ticket made by {user.name}#{user.discriminator}",
            description=f"{message_content}",
            color=0x26FF00,
        )
        em.set_footer(text="ticket", icon_url=user.avatar.url)
        await ticket.send(f"Thank you for contacting support! A staff member will be here shortly!\n")
        await ticket.send(f"{user.mention} I have already pinged the `@Staff` team. No need for you to ping them.")
        await inter.send(f"Created Ticket. Your ticket: {ticket.mention}", ephemeral=True)

    @commands.slash_command(description="Close ticket")
    @commands.has_role("Staff")
    async def close(self, inter):
        if "ticket-" in inter.channel.name:
            await inter.channel.delete()
        else:
            await errorEmb(inter, "This is not a ticket channel.")

    @commands.slash_command(name="adduser", description="Add user to channel")
    @commands.has_role("Staff")
    async def add_user(self, inter, member: disnake.Member):
        if "ticket-" in inter.channel.name:
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
        if "ticket-" in inter.channel.name:
            await inter.channel.set_permissions(member, overwrite=None)
            em = disnake.Embed(
                title="Remove",
                description=f"{inter.author.mention} has removed {member.mention} from {inter.channel.mention}",
            )
            await inter.send(embed=em)
        else:
            await errorEmb(inter, "This is not a ticket channel.")


def setup(bot: OGIROID):
    bot.add_cog(Tickets(bot))
