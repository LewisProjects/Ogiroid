import disnake
from disnake.ext import commands


class Tickets(commands.Cog):
    """🎫 Ticketing system commands (Staff)"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        channel = self.bot.get_channel(990679557596135475)
        message = await channel.fetch_message(990679907795349554)
        emoji = self.bot.get_emoji(990310706874290216)
        await message.add_reaction(emoji)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        reaction_message = await self.bot.get_channel(990679557596135475).fetch_message(
            990679907795349554
        )
        if payload.message_id == reaction_message.id:
            guild = self.bot.get_guild(payload.guild_id)
            user = guild.get_member(payload.user_id)
            if user.id == 984802008403959879:
                return print("Added reaction from bot")
            role = await guild.create_role(
                name=f"{user.id}",
                hoist=False,
                colour=int("FFFFFF", 16),
                mentionable=False,
                reason="Tickets",
            )
            await user.add_roles(role)
            staff = self.bot.get_guild(985234686878023730).get_role(985943266115584010)
            emoji = self.bot.get_emoji(990310706874290216)
            ticket_channel = await reaction_message.guild.create_text_channel(f"ticket-{user.name}")
            await ticket_channel.set_permissions(
                reaction_message.guild.get_role(reaction_message.guild.id), read_messages=False
            )
            await ticket_channel.set_permissions(
                user,
                send_messages=True,
                read_messages=True,
                add_reactions=True,
                embed_links=True,
                attach_files=True,
                read_message_history=True,
                external_emojis=True,
            )
            await ticket_channel.set_permissions(
                staff,
                send_messages=True,
                read_messages=True,
                add_reactions=True,
                embed_links=True,
                attach_files=True,
                read_message_history=True,
                external_emojis=True,
            )
            message_content = (
                "Thank you for contacting support! A staff member will be here shortly!"
            )
            em = disnake.Embed(
                title=f"Ticket made by {user.name}#{user.discriminator}",
                description=f"{message_content}",
                color=0x26FF00,
            )
            em.set_footer(text="ticket", icon_url=user.avatar.url)
            await ticket_channel.send(
                f"Thank you for contacting support! A staff member will be here shortly!\n `Ticket ID`:{role.mention}"
            )
            await ticket_channel.send(
                f"{user.mention} I have already pinged the `@Staff` team. No need for you to ping them."
            )
            await reaction_message.remove_reaction(emoji, user)

    @commands.slash_command(description="Close ticket")
    @commands.has_role("Staff")
    async def close(self, ctx):
        await ctx.channel.delete()

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
    @commands.has_permissions(manage_messages=True)
    async def remove_user(self, ctx, member: disnake.Member):
        await ctx.channel.set_permissions(member, overwrite=None)
        em = disnake.Embed(
            title="Remove",
            description=f"{ctx.author.mention} has removed {member.mention} to {ctx.channel.mention}",
        )
        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(Tickets(bot))
