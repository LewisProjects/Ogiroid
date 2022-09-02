from __future__ import annotations

import asyncio
import io
import random
from collections import namedtuple
from io import BytesIO
from typing import Union

import disnake
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from disnake import Message, Member, MessageType, File, ApplicationCommandInteraction, ClientUser, Guild
from disnake.ext import commands
from disnake.ext.commands import CooldownMapping, BucketType, Cog

from utils.CONSTANTS import xp_probability, LEVELS_AND_XP, MAX_LEVEL
from utils.bot import OGIROID
from utils.exceptions import LevelingSystemError, UserNotFound
from utils.models import User
from utils.shortcuts import errorEmb

FakeGuild = namedtuple("FakeGuild", "id")


class LevelsController:
    def __init__(self, bot: OGIROID, db):
        self.bot = bot
        self.db = db

        self.__rate = 2
        self.__per = 60
        self._cooldown = CooldownMapping.from_cooldown(self.__rate, self.__per, BucketType.member)

    @Cog.listener()
    async def on_error(self, inter, error):
        if isinstance(error, UserNotFound):
            await self.add_user(inter.author, inter.guild)
        else:
            raise error

    async def add_user(self, user: Member, guild: Guild):
        await self.db.execute(
            "INSERT INTO levels (user_id, guild_id, level, xp, total_exp) VALUES (?, ?, ?, ?, ?)",
            (user.id, guild.id, 0, 0, 0),
        )
        await self.db.commit()

    def get_xp_for_level(self, level: int) -> int:
        """
        Returns the total amount of XP needed for the specified level. Levels go from 0-100
        """
        try:
            return LEVELS_AND_XP[str(level)]
        except KeyError:
            raise ValueError(f"Levels only go from 0-{MAX_LEVEL}, {level} is not a valid level")

    async def on_cooldown(self, message) -> bool:
        bucket = self._cooldown.get_bucket(message)
        on_cooldown = bucket.update_rate_limit()  # type: ignore
        print(f"{on_cooldown=} {bucket=}")
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
            raise LevelingSystemError("Invalid rate or per. Values must be greater than zero")
        self._cooldown = CooldownMapping.from_cooldown(rate, per, BucketType.member)
        self.__rate = rate
        self.__per = per

    async def is_in_database(self, member: Union[Member, int], guild: Union[FakeGuild, int] = None) -> bool:
        record = await self.db.execute(
            "SELECT EXISTS( SELECT 1 FROM levels WHERE user_id = ? AND guild_id = ? )",
            (member.id, guild.id if guild else member.guild.id),
        )
        return bool((await record.fetchone())[0])

    async def _update_record(
            self, member: Union[Member, int], level: int, xp: int, total_exp: int, guild_id: int, **kwargs
    ) -> None:
        print(f"{member=} {level=} {xp=} {total_exp=} {guild_id=} {kwargs=}")
        if await self.is_in_database(member, guild=FakeGuild(id=guild_id)):
            await self.db.execute(
                "UPDATE levels SET level = ?, xp = ?, total_exp = ? WHERE user_id = ? AND guild_id = ?",
                (level, xp, total_exp, member.id if isinstance(member, (Member, ClientUser)) else member, guild_id),
            )
        else:
            await self.db.execute(
                "INSERT INTO levels (user_id, guild_id, level, xp, total_exp) VALUES (?, ?, ?, ?, ?)",
                (guild_id, member.id if isinstance(member, Member) else member, level, xp, total_exp),
            )
        await self.db.commit()

    async def set_level(self, member: Member, level: int) -> None:
        if 0 <= level <= MAX_LEVEL:
            await self._update_record(
                member=member,
                level=level,
                xp=0,
                total_exp=LEVELS_AND_XP[str(level)],
                guild_id=member.guild.id,
                maybe_new_record=True,
            )
        else:
            raise LevelingSystemError(f'Parameter "level" must be from 0-{MAX_LEVEL}')

    @staticmethod
    async def random_xp():
        return random.choice(xp_probability)

    async def add_xp(self, message: Message, xp: int):
        user = await self.get_user(message.author)
        if user is None:
            await self.set_level(message.author, 0)
        user = await self.get_user(message.author)
        user.xp += xp
        user.total_exp += xp
        if user.xp >= user.xp_needed:
            extra_xp = user.xp - user.xp_needed
            user.lvl += 1
            user.xp = extra_xp
            await self._update_record(
                member=message.author,
                level=user.lvl,
                xp=user.xp,
                total_exp=user.total_exp,
                guild_id=message.guild.id,
                maybe_new_record=False,
            )

            self.bot.dispatch("level_up", message.author)

        await self._update_record(
            member=message.author,
            level=user.lvl,
            xp=user.xp,
            total_exp=user.total_exp,
            guild_id=message.guild.id,
            maybe_new_record=True,
        )

    async def grant_xp(self, message):
        try:
            await self.add_xp(message, await self.random_xp())
        except UserNotFound:
            await self.add_user(message.author, message.guild)
            await self.add_xp(message, await self.random_xp())
        self._cooldown.update_rate_limit(message)

    async def handle_message(self, message: Message):
        if any(
                [
                    message.guild is None,
                    message.author.bot,
                    message.type not in [MessageType.default, MessageType.reply, MessageType.thread_starter_message],
                    message.content.__len__() < 5,
                ]
        ):
            return
        if not random.randrange(0, 3) == 2:
            return
        elif await self.on_cooldown(message):
            return

        await self.grant_xp(message)

    async def get_user(self, user: Member) -> User:  # todo cache this
        record = await self.db.execute(
            "SELECT * FROM levels WHERE user_id = ? AND guild_id = ?", (user.id, user.guild.id,),
        )
        raw = await record.fetchone()
        if raw is None:
            raise UserNotFound
        return User(*raw)

    async def generate_image_card(self, user: Member | User, rank: str, xp: int, lvl: int) -> Image:
        """generates an image card for the user"""
        avatar: disnake.Asset = user.display_avatar.with_size(512)
        # this for loop finds the closest level to the xp and defines the values accordingly
        x = 999999 * 9999999
        next_xp = 100
        for key, value in LEVELS_AND_XP.items():
            if (x > value - xp > 0) and not (xp - value == xp):
                x = value - xp
                next_xp = value
                lvl = key
        with Image.open("utils/data/images/rankcard.png").convert("RGBA") as base:

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
                draw.ellipse((offset, offset, pil_img.size[0] - offset, pil_img.size[1] - offset), fill=255)
                mask = mask.filter(ImageFilter.GaussianBlur(blur_radius))

                result = pil_img.copy()
                result.putalpha(mask)

                return result

            # makes the avatar ROUND
            avatar_img = mask_circle_transparent(avatar_img.resize((189, 189)), blur_radius=1, offset=0)

            previous_xp = LEVELS_AND_XP[str(int(lvl) - 1)]

            width = round(((xp - previous_xp) / (next_xp - previous_xp)) * 418, 2)
            fnt = ImageFont.truetype("utils/data/opensans-semibold.ttf", 24)
            # get a drawing context
            d = ImageDraw.Draw(txt)
            # username
            d.text((179, 32), user.name, font=fnt, fill=(0, 0, 0, 255))
            # xp
            d.text((185, 65), f"{xp}/{next_xp}", font=fnt, fill=(0, 0, 0, 255))
            # level
            d.text((115, 96), lvl, font=fnt, fill=(0, 0, 0, 255))
            # Rank
            d.text((113, 130), f'#{rank}', font=fnt, fill=(0, 0, 0, 255))
            d.rectangle((44, 186, 44 + width, 186 + 21), fill=(255, 255, 255, 255))
            txt.paste(avatar_img, (489, 23))

            out = Image.alpha_composite(base, txt)
            with BytesIO() as image_binary:
                out.save(image_binary, "PNG")
                image_binary.seek(0)
                return File(fp=image_binary, filename="image.png")

    @staticmethod
    async def send_levelup(message: Message, level: int):
        user = message.author

        msg = f"""{user.mention}, you have leveled up to level {level}!
        """
        await message.channel.send(msg)

    async def get_rank(self, user_record) -> int:
        user_xp = user_record.total_exp
        sql = "SELECT * FROM levels WHERE total_exp >= ? ORDER BY total_exp DESC"
        records_raw = await self.db.execute(sql, (user_xp,))
        records = await records_raw.fetchall()
        rank = 1

        for record in records:
            record = User(*record)
            if record.user_id == user_record.user_id:
                return rank
            rank += 1
        raise UserNotFound


class Level(commands.Cog):
    def __init__(self, bot: OGIROID):
        self.bot = bot
        self.levels = LEVELS_AND_XP
        self.controller: LevelsController = None

    def cog_unload(self) -> None:
        pass

    @commands.Cog.listener()
    async def on_rankup(self, msg: Message, level: int):
        """
        Called when a user reaches a certain level
        """
        await self.controller.send_levelup(msg, level)

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
        print('[Level] Ready')

    @commands.slash_command()
    @commands.guild_only()
    async def rank(self, inter: ApplicationCommandInteraction, user: Member):
        user = user or inter.author
        await inter.response.defer()
        if user.bot:
            return await errorEmb(inter, text="Bots can't rank up!")
        try:
            user_record = await self.controller.get_user(user)
        except UserNotFound:
            return await errorEmb(inter, text="User has never spoke!")
        if not user_record:
            print('[Level] User not found')
            await self.controller.add_user(user, inter.guild)
            return await self.rank(inter, user)
        rank = await self.controller.get_rank(user_record)
        image = await self.controller.generate_image_card(user,
                                                          rank, user_record.xp,
                                                          user_record.lvl)
        await inter.send(file=image)

    @staticmethod
    async def random_xp():
        return random.choice(xp_probability)


def setup(bot: OGIROID):
    bot.add_cog(Level(bot))
