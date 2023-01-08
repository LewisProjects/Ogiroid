from __future__ import annotations

import asyncio
import datetime as dt
import io
import random
from collections import namedtuple
from io import BytesIO
from typing import Union, Optional

import disnake
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from cachetools import TTLCache
from disnake import (
    Message,
    Member,
    MessageType,
    File,
    ApplicationCommandInteraction,
    ClientUser,
    Guild,
    Role,
    Embed,
    Option,
)
from disnake.ext import commands
from disnake.ext.commands import CooldownMapping, BucketType, Cog, Param, BadArgument

from utils import timeconversions
from utils.CONSTANTS import xp_probability, LEVELS_AND_XP, MAX_LEVEL
from utils.DBhandlers import ConfigHandler
from utils.bot import OGIROID
from utils.config import GConfig
from utils.exceptions import LevelingSystemError, UserNotFound
from utils.models import User, RoleReward
from utils.pagination import LeaderboardView
from utils.shortcuts import errorEmb, sucEmb, get_expiry

FakeGuild = namedtuple("FakeGuild", "id")


class LevelsController:
    def __init__(self, bot: OGIROID, db):
        self.bot = bot
        self.db = db

        self.__rate = 2
        self.__per = 60
        self._cooldown = CooldownMapping.from_cooldown(
            self.__rate, self.__per, BucketType.member
        )
        self.cache = TTLCache(maxsize=100_000, ttl=3600)
        self.config_hander = ConfigHandler(self.bot, self.db)

    def remove_cached(self, user: Member) -> None:
        self.cache.pop(f"levels_{user.id}_{user.guild.id}", None)

    @Cog.listener()
    async def on_error(self, inter, error):
        if isinstance(error, UserNotFound):
            await self.add_user(inter.author, inter.guild)
        else:
            raise error

    async def get_count(self, guild: Guild | int) -> int:
        if isinstance(guild, Guild):
            guild = guild.id

        record = await self.db.execute(
            "SELECT COUNT(*) FROM levels WHERE guild_id = ?", (int(guild),)
        )
        return (await record.fetchone())[0]

    async def get_leaderboard(
        self, guild: Guild, limit: int = 10, offset: Optional[int, int] = None
    ) -> list[User]:
        """get a list of users
        optionally you can specify a range of users to get from the leaderboard e.g. 200, 230
        """
        if offset is not None:
            if offset < 0:
                raise LevelingSystemError("the offset must be greater than 0")
            records = await self.db.execute(
                "SELECT * FROM levels WHERE guild_id = ? ORDER BY level DESC, xp DESC LIMIT ? OFFSET ?",
                (guild.id, limit, offset),
            )
        else:
            records = await self.db.execute(
                "SELECT * FROM levels WHERE guild_id = ? ORDER BY level DESC, xp DESC LIMIT ?",
                (guild.id, limit),
            )
        users = sorted(
            [User(*record) for record in await records.fetchall()],
            key=lambda x: x.total_exp,
            reverse=True,
        )
        return users

    async def add_user(self, user: Member, guild: Guild):
        self.remove_cached(user)
        await self.db.execute(
            "INSERT INTO levels (user_id, guild_id, level, xp) VALUES (?, ?, ?, ?)",
            (user.id, guild.id, 0, 0),
        )
        await self.db.commit()

    @staticmethod  # todo: remove
    def get_total_xp_for_level(level: int) -> int:
        """
        Returns the total amount of XP needed for the specified level. Levels go from 0-100
        """

        try:
            return sum(
                [exp for exp in [LEVELS_AND_XP[lvl] for lvl in range(1, level + 1)]][
                    ::-1
                ]
            )
        except KeyError:
            raise ValueError(
                f"Levels only go from 0-{MAX_LEVEL}, {level} is not a valid level"
            )

    async def on_cooldown(self, message) -> bool:
        bucket = self._cooldown.get_bucket(message)
        on_cooldown = bucket.update_rate_limit()  # type: ignore
        if on_cooldown is not None:
            return True
        return False

    async def change_cooldown(self, rate: int, per: float) -> None:
        """
        Update the cooldown rate

        Parameters
        ----------
        rate: :class:`int`
            The amount of messages each member can send before the cooldown triggers

        per: :class:`float`
            The amount of seconds each member has to wait before gaining more XP, aka the cooldown
        """
        if rate <= 0 or per <= 0:
            raise LevelingSystemError(
                "Invalid rate or per. Values must be greater than zero"
            )
        self._cooldown = CooldownMapping.from_cooldown(rate, per, BucketType.member)
        self.__rate = rate
        self.__per = per

    async def is_in_database(
        self, member: Union[Member, int], guild: Union[FakeGuild, int] = None
    ) -> bool:
        record = await self.db.execute(
            "SELECT EXISTS( SELECT 1 FROM levels WHERE user_id = ? AND guild_id = ? )",
            (member.id, guild.id if guild else member.guild.id),
        )
        return bool((await record.fetchone())[0])

    async def set_level(self, member: Member, level: int) -> None:
        if 0 <= level <= MAX_LEVEL:
            await self._update_record(
                member=member,
                level=level,
                xp=0,
                guild_id=member.guild.id,
            )  # type: ignore
            self.cache[f"levels_{member.id}_{member.guild.id}"] = User(
                xp=0,
                guild_id=member.guild.id,
                user_id=member.id,
                lvl=level,
            )
        else:
            raise LevelingSystemError(f'Parameter "level" must be from 0-{MAX_LEVEL}')

    async def _update_record(
        self, member: Union[Member, int], level: int, xp: int, guild_id: int
    ) -> None:
        self.remove_cached(
            member if isinstance(member, Member) else self.bot.get_user(member)
        )

        if await self.is_in_database(member, guild=FakeGuild(id=guild_id)):
            await self.db.execute(
                "UPDATE levels SET level = ?, xp = ? WHERE user_id = ? AND guild_id = ?",
                (
                    level,
                    xp,
                    member.id if isinstance(member, (Member, ClientUser)) else member,
                    guild_id,
                ),
            )
        else:
            await self.db.execute(
                "INSERT INTO levels (user_id, guild_id, level, xp) VALUES (?, ?, ?, ?)",
                (
                    member.id if isinstance(member, Member) else member,
                    guild_id,
                    level,
                    xp,
                ),
            )
        await self.db.commit()

    @staticmethod
    async def random_xp():
        return random.choice(xp_probability)

    async def add_xp(self, message: Message, xp: int):
        user = await self.get_user(message.author)
        if user is None:
            await self.set_level(message.author, 0)
        user = await self.get_user(message.author)
        old_lvl = user.lvl
        user.xp += xp
        while user.xp >= user.xp_needed:
            # get the extra xp that the user has after leveling up
            user.xp -= user.xp_needed
            user.lvl += 1

        await self._update_record(
            member=message.author,
            level=user.lvl,
            xp=user.xp,
            guild_id=message.guild.id,
        )  # type: ignore

        if user.lvl > old_lvl:
            self.bot.dispatch("level_up", message, user.lvl)

    async def get_boost(self, message: Message) -> int:
        """get the boost that the server/user will have then"""
        boost = 1
        config: GConfig = await self.config_hander.get_config(message.guild.id)
        if message.author.roles.__contains__(
            message.guild.get_role(self.bot.config.roles.nitro)
        ):
            boost = 2
        if config.xp_boost_active:
            boost *= config.xp_boost
        return int(boost)

    async def grant_xp(self, message):
        boost = await self.get_boost(message)
        xp = await self.random_xp() * boost
        try:
            await self.add_xp(message, xp)
        except UserNotFound:
            await self.add_user(message.author, message.guild)
            await self.add_xp(message, xp)
        self._cooldown.update_rate_limit(message)

    async def handle_message(self, message: Message):
        if any(
            [
                message.guild is None,
                message.author.bot,
                message.type
                not in [
                    MessageType.default,
                    MessageType.reply,
                    MessageType.thread_starter_message,
                ],
                message.content.__len__() < 5,
            ]
        ):
            return
        if not random.randint(1, 3) == 1:
            return
        elif await self.on_cooldown(message):
            return

        await self.grant_xp(message)

    async def get_user(self, user: Member) -> User:
        if f"levels_{user.id}_{user.guild.id}" in self.cache:
            return self.cache[f"levels_{user.id}_{user.guild.id}"]

        record = await self.db.execute(
            "SELECT * FROM levels WHERE user_id = ? AND guild_id = ?",
            (
                user.id,
                user.guild.id,
            ),
        )
        raw = await record.fetchone()
        if raw is None:
            raise UserNotFound
        self.cache[f"levels_{user.id}_{user.guild.id}"] = User(*raw)
        return User(*raw)

    async def generate_image_card(
        self, user: Member | User, rank: str, xp: int, lvl: int
    ) -> Image:
        """generates an image card for the user"""
        avatar: disnake.Asset = user.display_avatar.with_size(512)
        # this for loop finds the closest level to the xp and defines the values accordingly
        next_xp = LEVELS_AND_XP[int(lvl) + 1]
        # with Image.open("utils/data/images/rankcard.png").convert("RGBA") as base: NORMAL VERSION
        with Image.open("utils/data/images/winterrankcard.png").convert(
            "RGBA"
        ) as base:  # WINTER VERSION
            # make a blank image for the text, initialized to transparent text color
            txt = Image.new("RGBA", base.size, (255, 255, 255, 0))

            response = await self.bot.session.get(avatar.url)
            avatar_image_bytes = io.BytesIO(await response.read())
            avatar_img = Image.open(avatar_image_bytes).convert("RGBA")

            def mask_circle_transparent(pil_img, blur_radius, offset=0):
                """Make Image round(CTRL + C, CTRL + V ftw). https://note.nkmk.me/en/python-pillow-square-circle-thumbnail/"""
                offset = blur_radius * 2 + offset
                mask = Image.new("L", pil_img.size, 0)
                draw = ImageDraw.Draw(mask)
                draw.ellipse(
                    (
                        offset,
                        offset,
                        pil_img.size[0] - offset,
                        pil_img.size[1] - offset,
                    ),
                    fill=255,
                )
                mask = mask.filter(ImageFilter.GaussianBlur(blur_radius))

                result = pil_img.copy()
                result.putalpha(mask)

                return result

            def roundify(im, rad):
                circle = Image.new("L", (rad * 2, rad * 2), 0)
                draw = ImageDraw.Draw(circle)
                draw.ellipse((0, 0, rad * 2, rad * 2), fill=255)
                alpha = Image.new("L", im.size, 255)
                w, h = im.size
                alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
                alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
                alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
                alpha.paste(
                    circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad)
                )
                im.putalpha(alpha)
                return im

            # makes the avatar ROUND
            avatar_img = mask_circle_transparent(
                avatar_img.resize((189, 189)), blur_radius=1, offset=0
            )

            width = abs(round((xp / next_xp) * 418, 2))
            fnt = ImageFont.truetype("utils/data/opensans-semibold.ttf", 24)
            # get a drawing context
            d = ImageDraw.Draw(txt)
            # username
            d.text((179, 32), str(user.name), font=fnt, fill=(0, 0, 0, 255))
            # xp
            d.text((185, 65), f"{xp}/{next_xp}", font=fnt, fill=(0, 0, 0, 255))
            # level
            d.text((115, 96), str(lvl), font=fnt, fill=(0, 0, 0, 255))
            # Rank
            d.text((113, 130), f"#{rank}", font=fnt, fill=(0, 0, 0, 255))
            d.rectangle((44, 186, 44 + width, 186 + 21), fill=(255, 255, 255, 255))
            txt.paste(avatar_img, (489, 23))

            out = Image.alpha_composite(base, txt)
            out = roundify(out, rad=14)
            with BytesIO() as image_binary:
                out.save(image_binary, "PNG")
                image_binary.seek(0)
                return File(fp=image_binary, filename="image.png")

    @staticmethod
    async def send_levelup(message: Message, level: int):
        user = message.author
        if level in [0, 1, 2, 3]:
            return
        msg = f"""{user.mention}, you have leveled up to level {level}! 🥳
        """
        await message.channel.send(msg)

    async def get_rank(self, guild_id, user_record) -> int:
        """
        what to do
        #1. eliminate all the users that have a lower level than the user
        #2. sort the users by xp
        #3. get the index of the user
        #4. add 1 to the index
        """
        db_records = await self.db.execute(
            "SELECT * FROM levels WHERE guild_id = ? AND level >= ?",
            (
                guild_id,
                user_record.lvl,
            ),
        )
        raw_records = await db_records.fetchall()
        if raw_records is None:
            raise UserNotFound
        records = [User(*record) for record in raw_records]
        sorted_once = sorted(records, key=lambda x: x.xp, reverse=True)
        sorted_twice = sorted(sorted_once, key=lambda x: x.lvl, reverse=True)
        rank = sorted_twice.index(user_record) + 1
        return rank


class Level(commands.Cog):
    def __init__(self, bot: OGIROID):
        self.bot = bot
        self.levels = LEVELS_AND_XP
        self.controller: LevelsController = None

    def cog_unload(self) -> None:
        pass

    @commands.Cog.listener()
    async def on_level_up(self, msg: Message, level: int):
        """
        Called when a user reaches a certain level
        """

        await self.controller.send_levelup(msg, level)
        if await self.is_role_reward(msg.guild, level):
            role = await self.get_role_reward(msg.guild, level)
            if role is not None:
                await msg.author.add_roles(role, reason=f"Level up to level {level}")

    async def is_role_reward(self, guild: Guild, level: int) -> bool:
        query = await self.bot.db.execute(
            "SELECT EXISTS (SELECT 1 FROM role_rewards WHERE guild_id = ? AND required_lvl = ?)",
            (guild.id, level),
        )
        return bool((await query.fetchone())[0])

    async def get_role_reward(self, guild: Guild, level: int) -> Role:

        query = await self.bot.db.execute(
            "SELECT role_id FROM role_rewards WHERE guild_id = ? AND required_lvl = ?",
            (guild.id, level),
        )
        try:
            role_id = (await query.fetchone())[0]
        except TypeError:
            return None

        return guild.get_role(role_id)

    @commands.Cog.listener()
    async def on_message(self, message):
        try:
            await self.controller.handle_message(message)
        except AttributeError:  # bot has not fully started up yet

            await self.bot.wait_until_ready()
            await asyncio.sleep(5)
            await self.on_message(message)

    @commands.Cog.listener()
    async def on_ready(self):
        self.controller = LevelsController(self.bot, self.bot.db)
        if not self.bot.ready_:
            print("[Levels] Ready")

    @commands.slash_command()
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    async def xp_boost(self, inter: ApplicationCommandInteraction):
        return

    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    @xp_boost.sub_command()
    async def active(self, inter: ApplicationCommandInteraction, active: bool):
        await self.bot.db.execute(
            "UPDATE config SET xp_boost_enabled = ? WHERE guild_id = ?",
            (active, inter.guild.id),
        )
        await self.bot.db.commit()
        await inter.response.send_message(
            f"XP Boost is now {'enabled' if active else 'disabled'}"
        )

    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    @xp_boost.sub_command()
    async def set(
        self,
        inter: ApplicationCommandInteraction,
        amount=Option(
            name="amount",
            type=Union[float, int],
            required=True,
            description="The amount to boost by",
            max_value=10,
            min_value=0.1,
        ),
        expires: str = "Never",
    ):
        """Set the xp boost for the server and optionally set an expiration date"""
        try:
            expires = (await timeconversions.convert(expires)).dt.timestamp()
        except BadArgument:
            return await inter.response.send_message(
                'Invalid date format: Invalid time provided, try e.g. "tomorrow" or "3 days".'
            )
        await self.bot.db.execute(
            "UPDATE config SET xp_boost = ?, xp_boost_expiry = ? WHERE guild_id = ?",
            (amount, expires, inter.guild.id),
        )
        await self.bot.db.commit()
        await inter.response.send_message(
            f"Successfully set the xp boost to {amount}x it will expire {get_expiry(expires)} "
        )

    @commands.slash_command()
    @commands.guild_only()
    async def rank(
        self, inter: ApplicationCommandInteraction, user: Optional[Member] = None
    ):
        """
        Get the rank of a user in the server or yourself if no user is specified

        """
        user = user if user is not None else inter.author
        await inter.response.defer()
        if user.bot:
            return await errorEmb(inter, text="Bots can't rank up!")
        try:
            user_record = await self.controller.get_user(user)
            if not user_record:
                print("[Levels] User not found")
                await self.controller.add_user(user, inter.guild)
                return await self.rank(inter, user)
            rank = await self.controller.get_rank(inter.guild.id, user_record)
            image = await self.controller.generate_image_card(
                user, rank, user_record.xp, user_record.lvl
            )
            await inter.send(file=image)
        except UserNotFound:
            return await errorEmb(inter, text="User has never spoke!")

    @staticmethod
    async def random_xp():
        return random.choice(xp_probability)

    @commands.slash_command()
    @commands.guild_only()
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def leaderboard(self, inter: ApplicationCommandInteraction):
        """
        Get the leaderboard of the server
        """

        await inter.response.defer()
        limit = 10
        set_user = False
        records = await self.controller.get_leaderboard(inter.guild, limit=limit)
        try:
            cmd_user = await self.controller.get_user(inter.author)
        except UserNotFound:
            cmd_user = None

        if not records:
            return await errorEmb(inter, text="No records found!")
        embed = Embed(title="Leaderboard", color=0x00FF00)

        for i, record in enumerate(records):
            user = await self.bot.fetch_user(record.user_id)
            if record.user_id == inter.author.id:
                embed.add_field(
                    name=f"{i + 1}. {user} ~ You ",
                    value=f"Level: {record.lvl}\nTotal XP: {record.total_exp:,}",
                    inline=False,
                )
                set_user = True
            else:
                embed.add_field(
                    name=f"{i + 1}. {user}",
                    value=f"Level: {record.lvl}\nTotal XP: {record.total_exp:,}",
                    inline=False,
                )
        if not set_user:
            rank = await self.controller.get_rank(inter.guild.id, cmd_user)
            embed.add_field(
                name=f"{rank}. You",
                value=f"Level: {cmd_user.lvl}\nTotal XP: {cmd_user.xp:,}",
                inline=False,
            )

        embed.set_footer(
            text=f"{inter.author}", icon_url=inter.author.display_avatar.url
        )
        embed.timestamp = dt.datetime.now()

        await inter.send(
            embed=embed,
            view=LeaderboardView(
                controller=self.controller, firstemb=embed, author=inter.author.id
            ),
        )

    @commands.slash_command()
    @commands.guild_only()
    @commands.has_any_role("Staff", "staff")
    async def set_lvl(
        self,
        inter: ApplicationCommandInteraction,
        user: Member,
        level: int = Param(description="The level to set the user to", le=100, ge=0),
    ):
        """
        Set a user's level
        """
        if not level >= 0 and level < MAX_LEVEL:
            return await errorEmb(
                inter, text=f"Level must be between 0 and {MAX_LEVEL}"
            )
        if user.bot:
            return await errorEmb(inter, text="Bots can't rank up!")
        try:
            await self.controller.set_level(user, level)
        except LevelingSystemError:
            return await errorEmb(inter, text="Invalid mofo")
        await sucEmb(
            inter, text=f"Set {user.mention}'s level to {level}", ephemeral=False
        )

    @commands.slash_command()
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    async def role_reward(self, inter: ApplicationCommandInteraction):

        return

    @role_reward.sub_command()
    @commands.has_permissions(manage_roles=True)
    async def add(
        self,
        inter: ApplicationCommandInteraction,
        role: Role = Param(name="role", description="what role to give"),
        level_needed: int = Param(
            name="level_needed", description="The level needed to get the role"
        ),
    ):
        """adds a role to the reward list"""
        if int(level_needed) not in self.levels:
            return await errorEmb(
                inter, text=f"Level must be within 1-{MAX_LEVEL} found"
            )

        if await self.bot.db.execute(
            "SELECT 1 FROM role_rewards WHERE guild_id = ? AND role_id = ?",
            (inter.guild.id, role.id),
        ):
            sql = "INSERT OR IGNORE INTO role_rewards (guild_id, role_id, required_lvl) VALUES (?, ?, ?)"
            await self.bot.db.execute(sql, (inter.guild.id, role.id, level_needed))
            await self.bot.db.commit()
            return await sucEmb(
                inter,
                f"Added {role.mention} to the role reward list for level {level_needed}",
            )
        return await errorEmb(
            inter, text=f"{role.mention} is already in the role reward list"
        )

    @role_reward.sub_command()
    @commands.has_permissions(manage_roles=True)
    async def remove(
        self,
        inter: ApplicationCommandInteraction,
        role: Role = Param(name="role", description="what role to remove"),
    ):
        """remove a role reward"""
        if await self.bot.db.execute(
            "SELECT 1 FROM role_rewards WHERE guild_id = ? AND role_id = ?",
            (inter.guild.id, role.id),
        ):
            sql = "DELETE FROM role_rewards WHERE guild_id = ? AND role_id = ?"
            await self.bot.db.execute(sql, (inter.guild.id, role.id))
            await self.bot.db.commit()

            return await sucEmb(
                inter, f"Removed {role.mention} from the role reward list"
            )
        return await errorEmb(
            inter, text=f"{role.mention} is not in the role reward list"
        )

    @role_reward.sub_command()
    async def list(self, inter: ApplicationCommandInteraction):
        """list all role rewards"""
        sql = "SELECT * FROM role_rewards WHERE guild_id = ?"
        records = await self.bot.db.execute(sql, (inter.guild.id,))
        records = await records.fetchall()
        if not records:
            return await errorEmb(inter, text="No role rewards found")
        embed = Embed(title="Role Rewards", color=0x00FF00)
        for record in records:
            record = RoleReward(*record)
            embed.add_field(
                name=f"Level {record.required_lvl}",
                value=f"{inter.guild.get_role(record.role_id).mention}",
                inline=False,
            )
        await inter.send(
            embed=embed,
            allowed_mentions=disnake.AllowedMentions(
                everyone=False, roles=False, users=False
            ),
        )


def setup(bot: OGIROID):
    bot.add_cog(Level(bot))
