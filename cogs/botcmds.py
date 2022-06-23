from disnake.ext import commands
import disnake, datetime, time

global startTime
startTime = time.time()


class Commands(commands.Cog):
    """Common Bot Commands"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="Membercount", aliases=["mc", "totalmembers", "members", "people"]
    )
    async def membercount(self, ctx):
        """Count the members in the server"""
        member_count = len(ctx.guild.members)
        true_member_count = len([m for m in ctx.guild.members if not m.bot])
        bot_member_count = len([m for m in ctx.guild.members if m.bot])
        embed = disnake.Embed(title="Nember count", description=" ", color=0xFFFFFF)
        embed.add_field(
            name="Members of Coding With Lewis",
            value=f" \🌐  All members: **{member_count}**\n \👩‍👩‍👦‍👦 All Humans: **{true_member_count}**\n \🤖  All Bots: **{bot_member_count}**",
            inline=False,
        )
        await ctx.send(embed=embed)

    @commands.command(aliases=["latency"])
    async def ping(self, ctx):
        """Shows how fast the bot is replying to you!"""
        uptime = str(datetime.timedelta(seconds=int(round(time.time() - startTime))))
        embed = disnake.Embed(
            title="Pong! 🏓", description="Current ping of the bot!", colour=0xFFFFFF
        )
        ping = round(self.bot.latency * 1000)
        if ping < 50:
            emoji = "<:404:985939028597682216>"
        elif ping <= 100:
            emoji = "<:good:985939098567077888>"
        elif ping <= 200:
            emoji = "<:okay:985939033811193857>"
        elif ping >= 300:
            emoji = "<:bad:985939031449804850> "
        else:
            emoji = "🗼"
        embed.add_field(
            name=f"Latency {emoji} :", value=f"```>> {ping} ms```", inline=True
        )
        embed.add_field(
            name=f"Uptime <:uptime:986174741452824586>:",
            value=f"```>> {uptime}```",
            inline=True,
        )
        embed.set_footer(
            text=f"Command issued by: {ctx.message.author.name}",
            icon_url=ctx.message.author.avatar,
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def version(self, ctx):
        """Shows the version of the bot"""
        embed = disnake.Embed(title="Version", description=" ", color=0xFFFFFF)
        embed.add_field(name="Bot Version: ", value=f"```>> 1.3.0```", inline=False)
        embed.add_field(
            name="Disnake Version: ",
            value=f"```>> {disnake.__version__}```",
            inline=False,
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def info(self, ctx):
        """Shows the info of the bot"""
        embed = disnake.Embed(
            title="Ogiroid Information: ", description=" ", color=0xFFFFFF
        )
        embed.add_field(name="**Bot Name: **", value=f"Ogiroid", inline=False)
        embed.add_field(name="**Bot Version: **", value=f"1.3.0", inline=False)
        embed.add_field(
            name="**Bot Authors: **",
            value=f"[HarryDaDev](https://github.com/ImmaHarry) (@hrvyy#9677) | [FreebieII](https://github.com/FreebieII) (@Freebie#6429)",
            inline=False,
        )
        embed.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/985729550732394536/987287532146393109/discord-avatar-512-NACNJ.png"
        )
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Commands(bot))
