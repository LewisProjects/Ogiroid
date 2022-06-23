from disnake.ext import commands
import disnake


class Tickets(commands.Cog):
    """🎫 Ticket Related Commands!"""

    def __init__(self, bot):
        self.bot = bot

    @property
    def db(self):
        return self.bot.db

    """
    async def check_if_user_id_is_in_db(self, user_id):
        ""Checks if a user_id is in the database""
        print(type(user_id))

        async with self.db.execute("SELECT * FROM tickets") as cur:
            async for user_id in cur:
                print(user_id)
                if user_id == cid:
                    return True
                else:
                    return False
                    print(data)
        return bool(data)
        async with self.db.execute("SELECT * FROM tags LIMIT 20") as cur:
            async for tags in cur:
                embed.add_field(
                    name="Showing all available tags", value=f" `{tags[0]}`"
                )
        await ctx.send(embed=embed)
"""

    @commands.command()
    @commands.guild_only()
    async def ticket(self, ctx):  # , *, message):
        """Create a ticket"""

        creator = ctx.message.author
        cid = creator.id
        staff = disnake.utils.get(ctx.guild.roles, name="Staff")
        # await ctx.send("You already have a ticket open!")

        async with self.db.execute("SELECT * FROM tickets") as cur:
            async for user_id in cur:
                print(user_id[0])
                if user_id == cid:
                    await ctx.send("You already have a ticket open!")
                    return True
                else:

                    # if await self.check_if_user_id_is_in_db(cid) == True:
                    #    await ctx.send("You already have a ticket open!")
                    # CHECK IF THERES A TICKET FOR THE  USER ALREADY
                    channel = await ctx.guild.create_text_channel(
                        name=f"ticket-{creator.name}", reason="Created a ticket"
                    )
                    await channel.set_permissions(
                        ctx.guild.default_role, send_messages=False
                    )
                    await channel.set_permissions(ctx.guild.me, send_messages=True)
                    await channel.set_permissions(creator, send_messages=True)
                    await channel.set_permissions(
                        staff, send_messages=True
                    )  # Broken? I don't know why it seems to be dead.
                    # Changing the channel Description:
                    await channel.edit(
                        topic=f"Created by: {creator.name}, ID: {creator.id}. Please use this channel to communicate with the staff team."
                    )

                    embed = disnake.Embed(
                        title="Ticket Created!",
                        description=f"{creator.mention}, a ticket has been created for you!",
                        color=0xFFFFFF,
                    )
                    await ctx.send(embed=embed)
                    await channel.send(
                        f"{creator.mention}, you can access your ticket here!"
                    )
                    user_id = ctx.author.id
                    await self.db.execute(
                        "INSERT INTO tickets (user_id, channel_id) VALUES (?, ?)",
                        [str(user_id), str(channel.id)],
                    )
                    await self.db.commit()
                    user_id = ctx.author.id

    """
        embed = disnake.Embed(title="USER_IDS", description="USER_IDS", color=0x00FF00)
        async with self.db.execute("SELECT user_id FROM tickets") as cur:
            async for user_id in cur:
                if user_id == ctx.author.id:
                    await ctx.send(f"<@{user_id}> You already have a ticket open!")
                    break
                else:
                    embed.add_field(name="USER_ID", value=f" `{user_id}`")
                    await ctx.send(f"{user_id}")
                    print(user_id)
        await ctx.send(embed=embed)
"""

    @commands.command()
    @commands.has_role("Staff")
    async def close(self, ctx):
        """Closes a ticket"""
        await ctx.channel.delete()

    """
        embed = disnake.Embed(title="CHANNEL_IDS", description="CHANNEL_IDS", color=0xff0000)
        #async with self.db.execute("SELECT * FROM tickets WHERE user_id = ?", [user_id]).fetchall()  as cur:
        async with self.db.execute("SELECT channel_id FROM tickets LIMIT 20") as cur:
            async for channel_id in cur:
                embed.add_field(name='CHANNEL_IDS', value=f" `{channel_id}`")
                await ctx.send(f"{channel_id}")
                print(channel_id)
        await ctx.send(embed=embed)
      #  check = await self.check_if_user_id_is_in_db(user_id)
"""


def setup(bot):
    bot.add_cog(Tickets(bot))
