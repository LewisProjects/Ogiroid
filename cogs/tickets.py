import disnake
from disnake.ext import commands
from utils.bot import OGIROID
from utils.CONSTANTS import TICKET_MESSAGE, TICKET_EMOJI, STAFF_ROLE, TICKET_PERMS
from utils.exceptions import TicketAlreadyExists, TicketNotFound
from utils.models import *


class TicketManager:
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        self.session = self.bot.session

    async def exists(self, channel_id):
        async with self.db.execute("SELECT * FROM tickets WHERE channel_id = ?", [channel_id]) as cur:
            if await cur.fetchone() is not None:
                return True
            return False

    async def create(self, channel_id, user_id):
        if await self.get_tickets_by_owner(user_id):
            raise TicketAlreadyExists
        await self.db.execute(
            "INSERT INTO tickets (channel_id, user_id) VALUES (?, ?)",
            [channel_id, user_id],
        )
        await self.db.commit()

    async def get(self, channel_id) -> Ticket | TicketNotFound:
        if not await self.exists(channel_id):
            raise TicketNotFound
        async with self.db.execute("SELECT * FROM tickets WHERE channel_id = ?", [channel_id]) as cur:
            async for row in cur:
                return Ticket(*row)

    async def delete(self, channel_id):
        if not await self.exists(channel_id):
            raise TicketNotFound
        await self.db.execute("DELETE FROM tickets WHERE channel_id = ?", [channel_id])
        await self.db.commit()

    async def get_tickets_by_owner(self, user_id: int, limit=10):
        tickets = []
        async with self.db.execute(
            f"SELECT channel_id FROM tickets WHERE user_id = {user_id}"
        ) as cur:
            async for row in cur:
                tickets.append(Ticket(*row, user_id))
        return tickets

    # get amount of tags in database
    async def count(self) -> int:
        async with self.db.execute("SELECT COUNT(*) FROM tickets") as cur:
            return int(tuple(await cur.fetchone())[0])


class Tickets(commands.Cog):
    """🎫 Ticketing system commands (Staff)"""

    def __init__(self, bot: OGIROID):
        self.tickets: TicketManager = None
        self.bot: OGIROID = bot
        self.ticket_channel = self.bot.config.channels.tickets

    @property
    def db(self):
        return self.bot.db

    @commands.Cog.listener()
    async def on_ready(self):
        self.tickets: TicketManager = TicketManager(self.bot, self.bot.db)
        channel = self.bot.get_channel(self.ticket_channel)
        message = await channel.fetch_message(TICKET_MESSAGE)
        emoji = self.bot.get_emoji(TICKET_EMOJI)
        await message.add_reaction(emoji)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        reaction_message = await self.bot.get_channel(self.ticket_channel).fetch_message(TICKET_MESSAGE)
        if payload.message_id == reaction_message.id:
            guild = self.bot.get_guild(payload.guild_id)
            user = guild.get_member(payload.user_id)
            if user.id == self.bot.application_id:
                return print("Added reaction from bot")
            # role = await guild.create_role(
            #     name=f"{user.id}",
            #     hoist=False,
            #     colour=int("FFFFFF", 16),
            #     mentionable=False,
            #     reason="Tickets",
            # )
            # await user.add_roles(role)
            staff = guild.get_role(STAFF_ROLE)
            emoji = self.bot.get_emoji(TICKET_EMOJI)

            user_tickets = await self.tickets.get_tickets_by_owner(user.id)
            if user_tickets:
                await reaction_message.remove_reaction(emoji, user)
                return

            ticket_channel = await reaction_message.guild.create_text_channel(f"ticket-{user.name}")
            await ticket_channel.set_permissions(reaction_message.guild.get_role(reaction_message.guild.id), read_messages=False)
            await ticket_channel.set_permissions(user, **TICKET_PERMS)
            await ticket_channel.set_permissions(staff, **TICKET_PERMS)

            try:
                await self.tickets.create(ticket_channel.id, user.id)
            except TicketAlreadyExists:
                await reaction_message.remove_reaction(emoji, user)
                return

            message_content = "Thank you for contacting support! A staff member will be here shortly!"
            em = disnake.Embed(
                title=f"Ticket made by {user.name}#{user.discriminator}",
                description=f"{message_content}",
                color=0x26FF00,
            )
            em.set_footer(text="ticket", icon_url=user.avatar.url)

            await ticket_channel.send(f"Thank you for contacting support! A staff member will be here shortly!\n")
            await ticket_channel.send(f"{user.mention} I have already pinged the `@Staff` team. No need for you to ping them.")
            await reaction_message.remove_reaction(emoji, user)

    @commands.slash_command(description="Close ticket")
    @commands.has_role("Staff")
    async def close(self, ctx):
        try:
            await self.tickets.delete(ctx.channel.id)
            await ctx.channel.delete()
        except TicketNotFound:
            await ctx.send("This is not a ticket.", delete_after=5)

    @commands.slash_command(name="adduser", description="Add user to channel")
    @commands.has_role("Staff")
    async def add_user(self, ctx, member: disnake.Member):
        await ctx.channel.set_permissions(
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
            description=f"{ctx.author.mention} has added {member.mention} to {ctx.channel.mention}",
        )
        await ctx.send(embed=em)

    @commands.slash_command(name="removeuser", description="Remove user from channel")
    @commands.has_role("Staff")
    async def remove_user(self, ctx, member: disnake.Member):
        await ctx.channel.set_permissions(member, overwrite=None)
        em = disnake.Embed(
            title="Remove",
            description=f"{ctx.author.mention} has removed {member.mention} from {ctx.channel.mention}",
        )
        await ctx.send(embed=em)


def setup(bot: OGIROID):
    bot.add_cog(Tickets(bot))
