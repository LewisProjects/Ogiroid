import datetime
import time
from collections import Counter

import disnake
from disnake.ext import commands

from utils.CONSTANTS import status, __VERSION__
from utils.bot import OGIROID
from utils.shortcuts import QuickEmb

global startTime
startTime = time.time()


class plural:
    def __init__(self, value):
        self.value = value

    def __format__(self, format_spec):
        v = self.value
        singular, sep, plural = format_spec.partition("|")
        plural = plural or f"{singular}s"
        if abs(v) != 1:
            return f"{v} {plural}"
        return f"{v} {singular}"


class Commands(commands.Cog):
    """Common Bot Commands"""

    def __init__(self, bot: OGIROID):
        self.bot = bot

    # Can be deprecated since there is a server info command now and its specific to the Lewis's Server
    @commands.slash_command(name="membercount", description="Get the member count of the server")
    async def membercount(self, inter):
        """Count the members in the server"""
        member_count = len(inter.guild.members)
        true_member_count = len([m for m in inter.guild.members if not m.bot])
        bot_member_count = len([m for m in inter.guild.members if m.bot])
        embed = disnake.Embed(title="Member count", description=" ", color=0xFFFFFF)
        embed.add_field(
            name="Members of Coding With Lewis",
            value=f" \🌐  All members: **{member_count}**\n \👩‍👩‍👦‍👦 All Humans: **{true_member_count}**\n \🤖  All Bots: **{bot_member_count}**",
            inline=False,
        )
        await inter.response.send_message(embed=embed)

    @commands.slash_command(name="ping", description="Shows how fast the bot is replying to you!")
    async def ping(self, inter):
        """Shows how fast the bot is replying to you!"""
        uptime = str(datetime.timedelta(seconds=int(round(time.time() - startTime))))
        embed = disnake.Embed(title="Pong! 🏓", description="Current ping of the bot!", colour=0xFFFFFF)
        ping = round(inter.bot.latency * 1000)
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
        embed.add_field(name=f"Latency {emoji} :", value=f"```>> {ping} ms```", inline=True)
        embed.add_field(
            name=f"Uptime <:uptime:986174741452824586>:",
            value=f"```>> {uptime}```",
            inline=True,
        )
        embed.set_footer(
            text=f"Command issued by: {inter.author.name}",
            icon_url=inter.author.avatar,
        )
        await inter.response.send_message(embed=embed)

    @commands.slash_command(name="botinfo", description="Shows info about the bot!")
    async def botinfo(self, inter):
        """Shows the info of the bot"""
        embed = disnake.Embed(title="Ogiroid Information: ", description=" ", color=0xFFFFFF)
        embed.add_field(name="**Bot Name: **", value=f"```>> Ogiroid```", inline=False)
        embed.add_field(name="**Bot Version: **", value=f"```>> {__VERSION__}```", inline=False)
        embed.add_field(
            name="**Disnake Version: **",
            value=f"```>> {disnake.__version__}```",
            inline=False,
        )
        embed.add_field(
            name="**Bot Developers: **",
            value=f"__Owners:__\n`>` **[FreebieII](https://github.com/FreebieII) (<@744998591365513227>)** \n"
            f"`>` **[HarryDaDev](https://github.com/ImmaHarry) (<@963860161976467498>) **\n\n"
            f"__Contributors:__\n**`>`[JasonLovesDoggo](https://github.com/JasonLovesDoggo) (<@511724576674414600>)\n"
            f"`>`[DWAA1660](https://github.com/DWAA1660) (<@491266830674034699>) \n"
            f"`>`[LevaniVashadze](https://github.com/LevaniVashadze) (<@662656158129192961>)\n"
            f"`>`[CordlessCoder](https://github.com/CordlessCoder) (<@577885109894512659>)**",
            inline=False,
        )
        embed.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/985729550732394536/987287532146393109/discord-avatar-512-NACNJ.png"
        )

        button = disnake.ui.Button(label="Source", style=disnake.ButtonStyle.url, url="https://github.com/LewisProjects/Ogiroid")
        await inter.send(embed=embed, components=button)

    @commands.slash_command()
    @commands.guild_only()
    async def serverinfo(self, inter, *, guild_id=None):
        """Shows info about the current server."""
        if guild_id is not None and await self.bot.is_owner(inter.author):
            guild = self.bot.get_guild(guild_id)
            if guild is None:
                await QuickEmb(inter, "Invalid Guild ID given or im not in that guild").error().send()
                return
        else:
            guild = inter.guild

        roles = [role.name.replace("@", "@\u200b") for role in guild.roles]

        if not guild.chunked:
            async with inter.typing():
                await guild.chunk(cache=True)

        # figure out what channels are 'secret'
        everyone = guild.default_role
        everyone_perms = everyone.permissions.value
        secret = Counter()
        totals = Counter()
        for channel in guild.channels:
            allow, deny = channel.overwrites_for(everyone).pair()
            perms = disnake.Permissions((everyone_perms & ~deny.value) | allow.value)
            channel_type = type(channel)
            if channel_type == disnake.channel.CategoryChannel:
                continue
            totals[channel_type] += 1
            if not perms.read_messages:
                secret[channel_type] += 1
            elif isinstance(channel, disnake.VoiceChannel) and (not perms.connect or not perms.speak):
                secret[channel_type] += 1
        e = disnake.Embed(colour=0xFFFFFF)
        e.title = guild.name
        e.description = f"**ID**: {guild.id}\n**Owner**: {guild.owner}"
        if guild.icon:
            e.set_thumbnail(url=guild.icon.url)
        if inter.guild.banner:
            e.set_image(url=inter.guild.banner.with_format("png").with_size(1024))
        channel_info = []
        for key, total in totals.items():
            secrets = secret[key]

            if secrets:
                channel_info.append(f"Text Channels: {total} ({secrets} locked)")
            else:
                channel_info.append(f"Voice Channels: {total}")

        info = []
        features = set(guild.features)
        all_features = {
            "PARTNERED": "Partnered",
            "VERIFIED": "Verified",
            "DISCOVERABLE": "Server Discovery",
            "COMMUNITY": "Community Server",
            "FEATURABLE": "Featured",
            "WELCOME_SCREEN_ENABLED": "Welcome Screen",
            "INVITE_SPLASH": "Invite Splash",
            "VIP_REGIONS": "VIP Voice Servers",
            "VANITY_URL": "Vanity Invite",
            "COMMERCE": "Commerce",
            "LURKABLE": "Lurkable",
            "NEWS": "News Channels",
            "ANIMATED_ICON": "Animated Icon",
            "BANNER": "Banner",
        }

        for feature, label in all_features.items():
            if feature in features:
                info.append(f"{inter.tick(True)}: {label}")

        if info:
            e.add_field(name="Features", value="\n".join(info))

        e.add_field(name="Channels", value="\n".join(channel_info))

        if guild.premium_tier != 0:
            boosts = f"Level {guild.premium_tier}\n{guild.premium_subscription_count} boosts"
            last_boost = max(guild.members, key=lambda m: m.premium_since or guild.created_at)
            if last_boost.premium_since is not None:
                boosts = f"{boosts}\nLast Boost: {last_boost}"
            e.add_field(name="Boosts", value=boosts, inline=False)

        bots = sum(m.bot for m in guild.members)
        fmt = f"Total: {guild.member_count} ({plural(bots):bot})"

        e.add_field(name="Members", value=fmt, inline=False)
        e.add_field(name="Roles", value=", ".join(roles) if len(roles) < 10 else f"{len(roles)} roles")

        emoji_stats = Counter()
        for emoji in guild.emojis:
            if emoji.animated:
                emoji_stats["animated"] += 1
                emoji_stats["animated_disabled"] += not emoji.available
            else:
                emoji_stats["regular"] += 1
                emoji_stats["disabled"] += not emoji.available
                gel = guild.emoji_limit
                fmt = f'Regular: {emoji_stats["regular"]}/{gel}\nAnimated: {emoji_stats["animated"]}/{gel}\n'
                if emoji_stats["disabled"] or emoji_stats["animated_disabled"]:
                    fmt = f'{fmt}Disabled: {emoji_stats["disabled"]} regular, {emoji_stats["animated_disabled"]} animated\n'

        fmt = f"{fmt}Total Emojis: {len(guild.emojis)}/{guild.emoji_limit * 2}"
        e.add_field(name="Emoji", value=fmt, inline=False)
        e.set_footer(text=f'Created: {guild.created_at.strftime("%m/%d/%Y")}')
        await inter.send(embed=e)

    @commands.slash_command()
    async def whois(self, inter, *, user: disnake.Member = None):
        """Shows info about a user."""
        if user == None:
            user: disnake.Member = inter.author
        e = disnake.Embed(description="")
        roles = [
            role.name.replace("@", "@\u200b") for role in getattr(user, "roles", []) if not role.id == inter.guild.default_role.id
        ]
        bottag = "<:bot_tag:880193490556944435>"
        e.set_author(name=f'{user}{bottag if user.bot else ""}')
        join_position = sorted(inter.guild.members, key=lambda m: m.joined_at).index(user) + 1

        e.add_field(name="Join Position", value=join_position)
        e.add_field(name="ID", value=user.id, inline=False)
        e.add_field(name="Joined", value=getattr(user, "joined_at", None).strftime("%m/%d/%Y"), inline=False)
        e.add_field(name="Created", value=user.created_at.strftime("%m/%d/%Y"), inline=False)

        voice = getattr(user, "voice", None)
        if voice is not None:
            vc = voice.channel
            other_people = len(vc.members) - 1
            voice = f"{vc.name} with {other_people} others" if other_people else f"{vc.name} by themselves"
            e.add_field(name="Voice", value=voice, inline=False)

        if roles:
            e.add_field(name="Roles", value=", ".join(roles) if len(roles) < 10 else f"{len(roles)} roles", inline=False)

        colour = user.colour
        if colour.value:
            e.colour = colour

        e.colour = 0xFFFFFF

        if user.avatar:
            e.set_thumbnail(url=user.avatar.url)

        if isinstance(user, disnake.User):
            e.set_footer(text="This member is not in this server.")

        e.description += (
            f"Mobile {status(str(user.mobile_status))}  "
            f"Desktop {status(str(user.desktop_status))}  "
            f"Web browser {status(str(user.web_status))}"
        )

        await inter.send(embed=e)

    @commands.slash_command(name="avatar", description="Shows the avatar of a user.")
    async def avatar(self, inter: disnake.ApplicationCommandInteraction, user: disnake.Member = None):
        """Shows the avatar of a user."""
        if user == None:
            user = inter.author

        embed = disnake.Embed(title=f"{user}'s avatar")
        embed.set_image(url=user.avatar.url)
        embed.set_author(name=f"{user}", icon_url=user.avatar.url)
        await inter.send(embed=embed)


def setup(bot):
    bot.add_cog(Commands(bot))
