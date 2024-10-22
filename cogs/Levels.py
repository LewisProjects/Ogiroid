from __future__ import annotations

import asyncio
import datetime
import datetime as dt
import io
import random
from collections import namedtuple
from io import BytesIO
from typing import Union, Optional

import disnake
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops, ImageColor
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
from disnake.ext import commands, tasks
from disnake.ext.commands import (
    CooldownMapping,
    BucketType,
    Cog,
    Param,
    BadArgument,
)
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from utils import timeconversions
from utils.CONSTANTS import xp_probability, LEVELS_AND_XP, MAX_LEVEL, Colors
from utils.DBhandlers import ConfigHandler
from utils.bot import OGIROID
from utils.db_models import Levels, Config, RoleReward, CustomRoles
from utils.exceptions import LevelingSystemError, UserNotFound
from utils.pagination import LeaderboardView
from utils.shortcuts import errorEmb, sucEmb, get_expiry

FakeGuild = namedtuple("FakeGuild", "id")


class LevelsController:
    def __init__(self, bot: OGIROID, db: async_sessionmaker[AsyncSession]):
        self.bot = bot
        self.db = db

        self.__rate = 2
        self.__per = 60
        self._cooldown = CooldownMapping.from_cooldown(
            self.__rate, self.__per, BucketType.member
        )
        self.cache = TTLCache(maxsize=100_000, ttl=3600)
        self.config_handler = ConfigHandler(self.bot, self.db)

    def remove_cached(self, user: Member) -> None:
        self.cache.pop(f"levels_{user.id}_{user.guild.id}", None)

    @Cog.listener()
    async def on_error(self, inter, error):
        if isinstance(error, UserNotFound):
            await self.add_user(inter.author, inter.guild)
        else:
            raise error

    async def get_leaderboard(
        self, guild: Guild, limit: int = 10, offset: Optional[int, int] = None
    ) -> list[Levels]:
        """get a list of users
        optionally you can specify a range of users to get from the leaderboard e.g. 200, 230
        """
        if offset is not None:
            if offset < 0:
                raise LevelingSystemError("the offset must be greater than 0")
            async with self.db.begin() as session:
                records = await session.execute(
                    select(Levels)
                    .filter_by(guild_id=guild.id)
                    .order_by(Levels.level.desc(), Levels.xp.desc())
                    .limit(limit)
                    .offset(offset)
                )
            records = records.scalars().all()
        else:
            async with self.db.begin() as session:
                records = await session.execute(
                    select(Levels)
                    .filter_by(guild_id=guild.id)
                    .order_by(Levels.level.desc(), Levels.xp.desc())
                    .limit(limit)
                )
                records = records.scalars().all()
        users = sorted(
            [record for record in records],
            key=lambda x: x.total_exp,
            reverse=True,
        )
        return users

    async def get_count(self, guild: Guild | int) -> int:
        if isinstance(guild, Guild):
            guild = guild.id

        async with self.db.begin() as session:
            records = await session.execute(select(Levels).filter_by(guild_id=guild))
            return len(records.scalars().all())

    async def add_user(self, user: Member, guild: Guild):
        self.remove_cached(user)
        async with self.db.begin() as session:
            session.add(Levels(user_id=user.id, guild_id=guild.id, level=0, xp=0))

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
        async with self.db.begin() as session:
            if isinstance(member, (Member, ClientUser)):
                record = await session.execute(
                    select(Levels)
                    .filter_by(user_id=member.id, guild_id=guild.id)
                    .limit(1)
                )
            else:
                record = await session.execute(
                    select(Levels).filter_by(user_id=member, guild_id=guild.id).limit(1)
                )
            return bool(record.scalars().all())

    async def set_level(self, member: Member, level: int) -> None:
        if 0 <= level <= MAX_LEVEL:
            await self._update_record(
                member=member,
                level=level,
                xp=0,
                guild_id=member.guild.id,
            )  # type: ignore
            self.cache[f"levels_{member.id}_{member.guild.id}"] = Levels(
                xp=0,
                guild_id=member.guild.id,
                user_id=member.id,
                level=level,
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
            async with self.db.begin() as session:
                record = await session.execute(
                    select(Levels)
                    .filter_by(
                        user_id=member.id if isinstance(member, Member) else member,
                        guild_id=guild_id,
                    )
                    .limit(1)
                )
                record = record.scalars().first()
                record.level = level
                record.xp = xp
                session.add(record)
        else:
            async with self.db.begin() as session:
                session.add(
                    Levels(
                        user_id=member.id if isinstance(member, Member) else member,
                        guild_id=guild_id,
                        level=level,
                        xp=xp,
                    )
                )

    @staticmethod
    async def random_xp():
        return random.choice(xp_probability)

    async def add_xp(self, message: Message, xp: int):
        user = await self.get_user(message.author)
        if user is None:
            await self.set_level(message.author, 0)
        user = await self.get_user(message.author)
        old_lvl = user.level
        user.xp += xp
        while user.xp >= user.xp_needed:
            # get the extra xp that the user has after leveling up
            user.xp -= user.xp_needed
            user.level += 1

        await self._update_record(
            member=message.author,
            level=user.level,
            xp=user.xp,
            guild_id=message.guild.id,
        )  # type: ignore

        if user.level > old_lvl:
            self.bot.dispatch("level_up", message, user.level)

    async def get_boost(self, message: Message) -> int:
        """get the boost that the server/user will have then"""
        boost = 1
        config: Config = await self.config_handler.get_config(message.guild.id)
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

    async def get_user(self, user: Member, bypass: bool = False) -> Levels:
        """
        get the user from the database
        :param user: the user to get
        :param bypass: bypass the cache and get the user from the database
        :return: the user
        """
        if f"levels_{user.id}_{user.guild.id}" in self.cache and not bypass:
            return self.cache[f"levels_{user.id}_{user.guild.id}"]

        async with self.db.begin() as session:
            record = await session.execute(
                select(Levels).filter_by(user_id=user.id, guild_id=user.guild.id)
            )
            record = record.scalar()
            if record is None:
                raise UserNotFound
            self.cache[f"levels_{user.id}_{user.guild.id}"] = record
            return record

    async def generate_image_card(
        self,
        user: Member | Levels,
        rank: str,
        xp: int,
        lvl: int,
        theme: str = "light",
    ) -> Image:
        """generates an image card for the user"""
        avatar: disnake.Asset = user.display_avatar.with_size(512)
        # this for loop finds the closest level to the xp and defines the values accordingly
        next_xp = LEVELS_AND_XP[int(lvl) + 1]

        card = "utils/data/images/rankcard.png"
        if (
            datetime.datetime.now().month == 12
            and datetime.datetime.now().day >= 10
            or datetime.datetime.now().month == 1
            and datetime.datetime.now().day <= 10
        ):
            # winter version
            card = "utils/data/images/winterrankcard.png"
        #     halloween version
        elif datetime.datetime.now().month == 10 and datetime.datetime.now().day >= 9:
            card = "utils/data/images/halloweenrankcard.png"

        with Image.open(card).convert("RGBA") as base:
            # make a blank image for the text, initialized to transparent text color
            foreground = (0, 0, 0, 255)  # black
            background = (255, 255, 255, 255)  # white
            transparent = (255, 255, 255, 0)
            txt = Image.new("RGBA", base.size, transparent)

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
                mode = im.mode
                circle = Image.new("L", (rad * 2, rad * 2), 0)
                draw = ImageDraw.Draw(circle)
                draw.ellipse((0, 0, rad * 2, rad * 2), fill=255)
                alpha = Image.new("L", im.size, 255)
                w, h = im.size
                alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
                alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
                alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
                alpha.paste(
                    circle.crop((rad, rad, rad * 2, rad * 2)),
                    (w - rad, h - rad),
                )
                im.putalpha(alpha)
                return im.convert(mode)

            # makes the avatar ROUND
            avatar_img = mask_circle_transparent(
                avatar_img.resize((189, 189)), blur_radius=1, offset=0
            )

            width = abs(round((xp / next_xp) * 418, 2))
            fnt = ImageFont.truetype("utils/data/opensans-semibold.ttf", 24)
            # get a drawing context
            d = ImageDraw.Draw(txt)
            # username
            d.text(
                (179, 32),
                str(user.name),
                font=fnt,
                fill=foreground,
            )
            # xp
            d.text(
                (185, 65),
                f"{xp}/{next_xp}",
                font=fnt,
                fill=foreground,
            )
            # level
            d.text((115, 97), str(lvl), font=fnt, fill=foreground)
            # Rank
            d.text(
                (113, 130),
                f"#{rank}",
                font=fnt,
                fill=foreground,
            )
            d.rectangle((44, 185, 44 + width, 185 + 21), fill=background)

            out = Image.alpha_composite(base, txt)
            out = roundify(out.convert("RGB"), rad=14)
            if theme == "dark":
                out = ImageChops.invert(out)
            out.paste(avatar_img, (489, 23), avatar_img)

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

    async def get_rank(
        self, guild_id, user_record, return_updated: bool = False
    ) -> (Levels, int) | int:
        """
        #1. eliminate all the users that have a lower level than the user
        #2. sort the users by xp
        #3. get the index of the user
        #4. add 1 to the index
        """
        async with self.db.begin() as session:
            records = await session.execute(
                select(Levels)
                .filter_by(guild_id=guild_id)
                .filter(Levels.level >= user_record.level)
            )
            records = records.scalars().all()

        if records is None:
            raise UserNotFound
        sorted_once = sorted(records, key=lambda x: x.total_exp, reverse=True)
        ids = [record.user_id for record in sorted_once]

        try:
            rank = ids.index(user_record.user_id) + 1
        except ValueError:
            user = self.bot.get_guild(guild_id).get_member(user_record.user_id)
            log_channel = self.bot.get_channel(self.bot.config.channels.logs)
            emb = Embed(
                description=f"User {user} not found in Level cache for guild {guild_id} bypassing cache...",
                color=Colors.red,
            )
            await log_channel.send(embed=emb)
            return await self.get_rank(
                guild_id,
                await self.get_user(user, bypass=True),
                return_updated=return_updated,
            )

        if return_updated:
            return user_record, rank
        else:
            return rank


class Level(commands.Cog):
    def __init__(self, bot: OGIROID):
        self.bot = bot
        self.levels = LEVELS_AND_XP
        self.controller: LevelsController = None
        self.custom_role_cleanup.start()

    def cog_unload(self) -> None:
        self.custom_role_cleanup.cancel()
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
        async with self.bot.db.begin() as session:
            record = await session.execute(
                select(RoleReward)
                .filter_by(guild_id=guild.id)
                .filter_by(required_lvl=level)
            )
            return bool(record.scalars().all())

    async def get_role_reward(self, guild: Guild, level: int) -> Role | None:
        async with self.bot.db.begin() as session:
            record = await session.execute(
                select(RoleReward)
                .filter_by(guild_id=guild.id)
                .filter_by(required_lvl=level)
            )
            record = record.scalar()
            if record is None:
                return None
            return guild.get_role(record.role_id)

    @commands.Cog.listener()
    async def on_message(self, message):
        try:
            await self.controller.handle_message(message)
        except AttributeError:  # bot has not fully started up yet
            print("[Levels] Message received but not ready yet. Retried")
            await self.bot.wait_until_ready()
            await asyncio.sleep(5)
            await self.on_message(message)

    @commands.Cog.listener()
    async def on_ready(self):
        self.controller = LevelsController(self.bot, self.bot.db)

        if not self.bot.ready_:
            print("[Levels] Ready")

    @tasks.loop(
        time=[
            dt.time(
                dt.datetime.utcnow().hour,
                dt.datetime.utcnow().minute,
                dt.datetime.utcnow().second + 10,
            )
        ]
    )
    # @tasks.loop(days=1)
    async def custom_role_cleanup(self):
        #     cleanup roles of users that are not in the top x+5 anymore
        async with self.bot.db.begin() as session:
            records = await session.execute(select(CustomRoles))
            records: list[CustomRoles] = records.scalars().all()
            # get all the configs
            config = await session.execute(select(Config))
            config: list[Config] = config.scalars().all()
            # map config limit to guild ids
            config_map = {
                record.guild_id: record.custom_roles_threshold for record in config
            }

            for record in records:
                user = self.bot.get_user(record.user_id)
                if user:
                    member = self.bot.get_guild(record.guild_id).get_member(
                        record.user_id
                    )
                    if member:
                        user_record = await self.controller.get_user(
                            member, bypass=True
                        )
                        leaderboard = await self.controller.get_leaderboard(
                            self.bot.get_guild(record.guild_id),
                            limit=config_map[record.guild_id],
                        )
                else:
                    member = None
                if not member or not any(
                    [record.user_id == user_record.user_id for record in leaderboard]
                ):
                    role = self.bot.get_guild(record.guild_id).get_role(record.role_id)
                    await role.delete()
                    await session.execute(
                        delete(CustomRoles).where(CustomRoles.user_id == user.id)
                    )
                    await self.bot.get_channel(self.bot.config.channels.logs).send(
                        f"Role {role} deleted for user {user}"
                    )

    @commands.slash_command(description="Create a custom role for yourself")
    @commands.guild_only()
    async def custom_role(self, inter: ApplicationCommandInteraction):
        return

    @custom_role.sub_command(description="Create a custom role for yourself")
    @commands.guild_only()
    async def create(
        self,
        inter: ApplicationCommandInteraction,
        color: str = commands.Param(
            description="The hex color of the role",
        ),
        name: str = commands.Param(
            description="The name of the role",
        ),
        icon: str
        | None = commands.Param(
            description="The icon of the role, must be a url and server needs to have boosts",
            default=None,
        ),
    ):
        """
        Create a custom role for yourself
        """
        await inter.response.defer()

        async with self.bot.db.begin() as session:
            record = await session.execute(
                select(CustomRoles).filter_by(user_id=inter.author.id)
            )
            record = record.scalar()
            if record is not None:
                return await inter.send("You already have a custom role")

        async with self.bot.db.begin() as session:
            record = await session.execute(
                select(Config).filter_by(guild_id=inter.guild.id)
            )
            config = record.scalar()
            limit = config.custom_roles_threshold
            min_lvl = config.min_required_lvl if config.min_required_lvl else 5

        leaderboard = await self.controller.get_leaderboard(
            inter.guild, limit=limit + 1
        )
        if not any([record.user_id == inter.author.id for record in leaderboard]):
            return await inter.send(
                f"You need to be in the top {limit} to create a custom role"
            )

        user_record = await self.controller.get_user(inter.author, bypass=True)
        if user_record.level < min_lvl:
            return await inter.send(
                f"You need to be at least level {config.min_required_lvl} to create a custom role"
            )

        color = disnake.Color(int(color.replace("#", ""), 16))
        role_position = (
            inter.guild.get_role(config.position_role_id).position - 1
            if config.position_role_id
            else inter.guild.me.top_role.position - 1
        )

        if not inter.guild.features.__contains__("ROLE_ICONS") or icon is None:
            role = await inter.guild.create_role(
                name=name,
                color=color,
                reason=f"Custom role created by {inter.author}",
            )

        else:
            # get icon from url
            icon = await self.bot.session.get(icon)
            icon = io.BytesIO(await icon.read())
            icon = Image.open(icon)
            # convert to be less than 256kb
            icon = icon.convert("RGB")
            icon = icon.resize((128, 128))
            # save the image to a buffer
            with io.BytesIO() as image_binary:
                icon.save(image_binary, "PNG")
                image_binary.seek(0)
                icon = image_binary.read()
            role = await inter.guild.create_role(
                name=name,
                color=color,
                reason=f"Custom role created by {inter.author}",
                icon=icon,
            )

        await role.edit(position=role_position)

        async with self.bot.db.begin() as session:
            session.add(
                CustomRoles(
                    user_id=inter.author.id,
                    guild_id=inter.guild.id,
                    role_id=role.id,
                )
            )

        await inter.author.add_roles(role)
        await inter.send(f"Role {role.mention} created and added to you!")

    @custom_role.sub_command(description="Delete your custom role")
    @commands.guild_only()
    async def delete(self, inter: ApplicationCommandInteraction):
        """
        Delete your custom role
        """
        await inter.response.defer()
        async with self.bot.db.begin() as session:
            record = await session.execute(
                select(CustomRoles).filter_by(user_id=inter.author.id)
            )
            record = record.scalar()
            if record is None:
                return await inter.send("You don't have a custom role")
            role = inter.guild.get_role(record.role_id)
            await session.execute(
                delete(CustomRoles).where(CustomRoles.user_id == inter.author.id)
            )
            await role.delete()

        await inter.send("Custom role deleted")

    @custom_role.sub_command(description="Get your custom role", name="get")
    @commands.guild_only()
    async def get_custom_role(self, inter: ApplicationCommandInteraction):
        """
        Get your custom role
        """
        await inter.response.defer()
        async with self.bot.db.begin() as session:
            record = await session.execute(
                select(CustomRoles).filter_by(user_id=inter.author.id)
            )
            record = record.scalar()
            if record is None:
                return await inter.send("You don't have a custom role")
            role = inter.guild.get_role(record.role_id)
        await inter.send(f"Your custom role is {role.mention}")

    @custom_role.sub_command(description="Edit your custom role", name="edit")
    @commands.guild_only()
    async def edit_custom_role(
        self,
        inter: ApplicationCommandInteraction,
        color: str
        | None = commands.Param(
            description="The hex color of the role",
            default=None,
        ),
        name: str
        | None = commands.Param(
            description="The name of the role",
            default=None,
        ),
        icon: str
        | None = commands.Param(
            description="The icon of the role, must be a url and server needs to have boosts",
            default=None,
        ),
    ):
        """
        Edit your custom role
        """
        await inter.response.defer()
        async with self.bot.db.begin() as session:
            record = await session.execute(
                select(CustomRoles).filter_by(user_id=inter.author.id)
            )
            record = record.scalar()
            if record is None:
                return await inter.send("You don't have a custom role")

        color = disnake.Color(int(color.replace("#", ""), 16))
        role = inter.guild.get_role(record.role_id)
        if icon is not None and inter.guild.features.__contains__("ROLE_ICONS"):
            # get icon from url
            icon = await self.bot.session.get(icon)
            icon = io.BytesIO(await icon.read())
            icon = Image.open(icon)
            # convert to be less than 256kb
            icon = icon.convert("RGB")
            icon = icon.resize((128, 128))
            # save the image to a buffer
            with io.BytesIO() as image_binary:
                icon.save(image_binary, "PNG")
                image_binary.seek(0)
                icon = image_binary.read()
            await role.edit(name=name, color=color, icon=icon)
        else:
            await role.edit(name=name, color=color)

        await inter.send(f"Role {role.mention} edited")

    @custom_role.sub_command(description="Change limit of custom roles(default 20)")
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    async def limits(
        self,
        inter: ApplicationCommandInteraction,
        limit: int = commands.Param(
            default=None, description="The limit of custom roles(default 20)"
        ),
        min_lvl: int = commands.Param(
            default=None,
            description="The minimum level required to create a custom role",
        ),
        after_role_positon: Role = commands.Param(
            default=None,
            description="The role after which the custom roles will be placed",
        ),
    ):
        """
        Change the limit of custom roles
        """
        await inter.response.defer()
        if limit is None and min_lvl is None and after_role_positon is None:
            return await inter.send(
                "You need to specify a limit or a min level to change"
            )
        async with self.bot.db.begin() as session:
            record_ = await session.execute(
                select(Config).filter_by(guild_id=inter.guild.id)
            )
            record: Config = record_.scalar()
            if limit is not None:
                record.custom_roles_threshold = limit
            if min_lvl is not None:
                record.min_required_lvl = min_lvl
            if after_role_positon is not None:
                record.position_role_id = after_role_positon.id
            session.add(record)
        await inter.send(f"Custom roles config updated")

    @commands.slash_command(description="XP boost base command")
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    async def xp_boost(self, inter: ApplicationCommandInteraction):
        return

    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    @xp_boost.sub_command()
    async def active(self, inter: ApplicationCommandInteraction, active: bool):
        """Enable or disable xp boost"""
        await inter.response.defer()
        async with self.bot.db.begin() as session:
            record = await session.execute(
                select(Config).filter_by(guild_id=inter.guild.id)
            )
            record = record.scalar()
            record.xp_boost_enabled = active
            session.add(record)

        await inter.send(f"XP Boost is now {'enabled' if active else 'disabled'}")

    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    @xp_boost.sub_command()
    async def get(self, inter: ApplicationCommandInteraction):
        """
        gets the current xp boost for the bot
        """
        await inter.response.defer()
        async with self.bot.db.begin() as session:
            record = await session.execute(
                select(Config).filter_by(guild_id=inter.guild.id)
            )
            config = record.scalar()
        if config is None:
            return await inter.send("There is no config setup for this server")
        emb = Embed(
            title="XP Boost",
            description=f"XP Boost is currently {'enabled' if config.xp_boost_enabled else 'disabled'}",
            color=0x2F3136,
        )
        emb.add_field(name="Multiplier", value=str(config.xp_boost) + "x")
        emb.add_field(name="Expires", value=get_expiry(config.xp_boost_expiry))
        await inter.send(embed=emb)

    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    @xp_boost.sub_command()
    async def set(
        self,
        inter: ApplicationCommandInteraction,
        amount: str = Option(
            name="amount",
            required=True,
            description="The amount to boost by",
        ),
        expires: str = "Never",
    ):
        """Set the xp boost for the server and optionally set an expiration date"""
        await inter.response.defer()
        try:
            amount = float(amount)
        except ValueError:
            return await inter.send("Invalid amount")
        if amount < 0.1:
            return await inter.send("Amount must be greater than 0.1")
        elif amount > 10:
            return await inter.send("Amount must be less than 10")
        try:
            expires = (await timeconversions.convert(expires)).dt.timestamp()
        except BadArgument:
            return await inter.send(
                'Invalid date format: Invalid time provided, try e.g. "tomorrow" or "3 days".'
            )
        async with self.bot.db.begin() as session:
            record = await session.execute(
                select(Config).filter_by(guild_id=inter.guild.id)
            )
            record = record.scalar()
            record.xp_boost = amount
            record.xp_boost_expiry = expires
            session.add(record)
        await inter.send(
            f"Successfully set the xp boost to {amount}x it will expire {get_expiry(expires)} "
        )

    @commands.slash_command()
    @commands.guild_only()
    async def rank(
        self,
        inter: ApplicationCommandInteraction,
        user: Optional[Member] = None,
        theme: Optional[str] = Param(
            description="The theme of the rank card",
            choices=["light", "dark"],
            default="light",
        ),
    ):
        """
        Get the rank of a user in the server or yourself if no user is specified

        """
        await inter.response.defer()
        user = user if user is not None else inter.author
        if user.bot or user.system:
            return await errorEmb(inter, text="Bots can't rank up!")
        try:
            user_record = await self.controller.get_user(user)
            if not user_record:
                print("[Levels] User not found")
                await self.controller.add_user(user, inter.guild)
                return await self.rank(inter, user)
            user_record, rank = await self.controller.get_rank(
                inter.guild.id, user_record, return_updated=True
            )
            image = await self.controller.generate_image_card(
                user, rank, user_record.xp, user_record.level, theme
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
                    name=f"{i + 1}. {user.name} ~ You ",
                    value=f"Level: {record.level}\nTotal XP: {record.total_exp:,}",
                    inline=False,
                )
                set_user = True
            else:
                embed.add_field(
                    name=f"{i + 1}. {user.name}",
                    value=f"Level: {record.level}\nTotal XP: {record.total_exp:,}",
                    inline=False,
                )
        if not set_user:
            rank = await self.controller.get_rank(inter.guild.id, cmd_user)
            embed.add_field(
                name=f"{rank}. You",
                value=f"Level: {cmd_user.level}\nTotal XP: {cmd_user.xp:,}",
                inline=False,
            )

        embed.set_footer(
            text=f"{inter.author}", icon_url=inter.author.display_avatar.url
        )
        embed.timestamp = dt.datetime.now()

        await inter.send(
            embed=embed,
            view=LeaderboardView(
                controller=self.controller,
                firstemb=embed,
                author=inter.author.id,
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
        await inter.response.defer()
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
            inter,
            text=f"Set {user.mention}'s level to {level}",
            ephemeral=False,
        )

    @commands.slash_command(description="Role rewards base command")
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    async def role_reward(self, inter: ApplicationCommandInteraction):
        return

    @role_reward.sub_command()
    @commands.has_permissions(manage_roles=True)
    async def add(
        self,
        inter: ApplicationCommandInteraction,
        role: Role = Param(name="role", description="What role to give"),
        level_needed: int = Param(
            name="level_needed", description="The level needed to get the role"
        ),
    ):
        """Adds a role to the reward list"""
        await inter.response.defer()
        if int(level_needed) not in self.levels:
            return await errorEmb(
                inter, text=f"Level must be within 1-{MAX_LEVEL} found"
            )
        async with self.bot.db.begin() as session:
            record = await session.execute(
                select(RoleReward)
                .filter_by(guild_id=inter.guild.id)
                .filter_by(role_id=role.id)
            )
            record = record.scalar()
        if record is None:
            async with self.bot.db.begin() as session:
                session.add(
                    RoleReward(
                        guild_id=inter.guild.id,
                        role_id=role.id,
                        required_lvl=level_needed,
                    )
                )
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
        role: Role = Param(name="role", description="What role to remove"),
    ):
        """Remove a role reward"""
        await inter.response.defer()
        async with self.bot.db.begin() as session:
            record = await session.execute(
                select(RoleReward)
                .filter_by(guild_id=inter.guild.id)
                .filter_by(role_id=role.id)
            )
            record = record.scalar()
        if record is not None:
            async with self.bot.db.begin() as session:
                await session.delete(record)
            return await sucEmb(
                inter, f"Removed {role.mention} from the role reward list"
            )
        return await errorEmb(
            inter, text=f"{role.mention} is not in the role reward list"
        )

    @role_reward.sub_command()
    async def list(self, inter: ApplicationCommandInteraction):
        """List all role rewards"""
        await inter.response.defer()
        async with self.bot.db.begin() as session:
            records = await session.execute(
                select(RoleReward).filter_by(guild_id=inter.guild.id)
            )
            records = records.scalars().all()
        if not records:
            return await errorEmb(inter, text="No role rewards found")
        embed = Embed(title="Role Rewards", color=0x00FF00)
        for record in records:
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
