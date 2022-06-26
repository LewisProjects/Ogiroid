import disnake
from disnake.ext import commands


class Tickets(commands.Cog):
        """🎫 Ticketing system commands (Staff)"""
        def __init__(self, client):
            self.client = client

        @commands.Cog.listener()
        async def on_ready(self):
            channel = self.client.get_channel(int(990679557596135475))
            message = await channel.fetch_message(int(990679907795349554))
            emoji = self.client.get_emoji(990310706874290216)
            await message.add_reaction(emoji)


"""
        @commands.Cog.listener()
        async def on_raw_reaction_add(self, payload):
            reaction_message = await self.client.get_channel(990679557596135475).fetch_message(990679907795349554)
            if payload.message_id == reaction_message.id:
                user = self.client.get_user(payload.user_id)
                if user.id == 984802008403959879:
                    return print('Added reaction from bot')
                guild = self.client.get_guild(payload.guild_id)
                role = await guild.create_role(
                    name=f"{user.id}",hoist=False,colour=int("FFFFFF", 16), mentionable=False, reason="Tickets"
                    )
                await self.client.add_roles(user, role)
                staff = self.client.get_guild(985234686878023730).get_role(985943266115584010)
                emoji = self.client.get_emoji(990310706874290216)
                ticket_channel = await reaction_message.guild.create_text_channel(f"ticket-{user.name}")
                await ticket_channel.set_permissions(reaction_message.guild.get_role(reaction_message.guild.id), read_messages=False)
                await ticket_channel.set_permissions(user, send_messages=True, read_messages=True, add_reactions=True, embed_links=True, attach_files=True, read_message_history=True, external_emojis=True)
                await ticket_channel.set_permissions(staff, send_messages=True, read_messages=True, add_reactions=True, embed_links=True, attach_files=True, read_message_history=True, external_emojis=True)
                message_content = "Thank you for contacting support! A staff member will be here shortly!"
                em = disnake.Embed(title=f"Ticket made by {user.name}#{user.discriminator}", description= f"{message_content}", color=0x26ff00)
                em.set_footer(text="ticket", icon_url=user.avatar.url)
                await ticket_channel.send(embed=em + f"Thank you for contacting support! A staff member will be here shortly!\n `Ticket ID`:{role.mention}")
                await ticket_channel.send(f"{user.mention} I have already pinged the `@Staff` team. No need for you to ping them.")
                await reaction_message.remove_reaction(emoji, user)

        @commands.command()
        @commands.has_role("Staff")
        async def close(self, ctx):
            await ctx.channel.delete()

        @commands.command()
        @commands.has_role('Staff')
        async def adduser(self, ctx, member: disnake.Member):
            await ctx.message.delete()
            await ctx.channel.set_permissions(member, send_messages=True, read_messages=True, add_reactions=True, embed_links=True, attach_files=True, read_message_history=True, external_emojis=True)
            em = disnake.Embed(title="Add", description=f'{ctx.author.mention} has added {member.mention} to {ctx.channel.mention}')
            await ctx.send(embed=em)

        @commands.command()
        @commands.has_permissions(manage_messages=True)
        async def removeuser(self, ctx, member: disnake.Member):
            await ctx.message.delete()
            await ctx.channel.set_permissions(member, overwrite=None)
            em = disnake.Embed(title="Remove", description=f'{ctx.author.mention} has removed {member.mention} to {ctx.channel.mention}')
            await ctx.send(embed=em)
    """
def setup(client):
    client.add_cog(Tickets(client))
