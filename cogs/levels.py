import io
from collections import namedtuple
from typing import Tuple, Union

import disnake
from disnake import Message, Member, MessageType, File, ApplicationCommandInteraction
from disnake.ext import commands
import random

from disnake.ext.commands import CooldownMapping, BucketType

from PIL import Image, ImageDraw, ImageFont, ImageFilter
from io import BytesIO

from utils.bot import OGIROID
from utils.CONSTANTS import xp_probability, LEVELS_AND_XP, MAX_LEVEL
from utils.exceptions import LevelingSystemError

FakeGuild = namedtuple("FakeGuild", "id")


class LevelsController:
    def __init__(self, bot: OGIROID, db):
        self.bot = bot
        self.db = db

        self.__rate = 2
        self.__per = 60
        self._cooldown = CooldownMapping.from_cooldown(self.__rate, self.__per, BucketType.user)

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
        if not on_cooldown:
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
        record = await self.db.execute("SELECT EXISTS( SELECT 1 FROM levels WHERE user_id = ? AND guild_id = ? )",
                                       (member.id, guild.id if guild else member.guild.id))
        return bool((await record.fetchone())[0])

    async def _update_record(
            self, member: Union[Member, int], level: int, xp: int, total_xp: int, guild_id: int, **kwargs
    ) -> None:

        if await self.is_in_database(
                member, guild=FakeGuild(id=guild_id)
        ):
            await self.db.execute(
                "UPDATE levels SET level = ?, xp = ?, total_xp = ? WHERE user_id = ? AND guild_id = ?",
                (level, xp, total_xp, member.id if isinstance(member, Member) else member, guild_id), )
        else:
            await self.db.execute(
                "INSERT INTO levels (user_id, guild_id, level, xp, total_xp) VALUES (?, ?, ?, ?, ?)",
                (guild_id, member.id if isinstance(member, Member) else member, level, xp, total_xp),
            )
        await self.db.commit()

    async def set_level(self, member: Member, level: int) -> None:
        if 0 <= level <= MAX_LEVEL:
            await self._update_record(
                member=member,
                level=level,
                xp=0,
                total_xp=LEVELS_AND_XP[str(level)],
                guild_id=member.guild.id,
                name=str(member),
                maybe_new_record=True,
            )
        else:
            raise LevelingSystemError(f'Parameter "level" must be from 0-{MAX_LEVEL}')

    @staticmethod
    async def random_xp():
        return random.choice(xp_probability)

    def user_xp_given(self, user_id: int):
        pass

    async def add_xp(self, message: Message, xp: int):
        return self.db.add_xp(message.author, xp)

    async def grant_xp(self, message):
        on_cooldown = await self.on_cooldown(message)
        if not on_cooldown:
            await self.add_xp(message, await self.random_xp())

    async def handle_message(self, message):
        if any(
                [
                    message.guild is None,
                    message.author.bot,
                    message.type != MessageType.default,
                ]
        ):
            return
        user = await self.grant_xp(message)

        # if user.exp > xp_needed:
        #    user.lvl += 1
        #    user.xp = 0
        #    await self.db.update_user(user)
        #    await sucEmb(message, f"You have leveled up to level {user.lvl}!")
        #    return True

    async def get_user(self, user_id: int):
        return await self.db.get_user(user_id) # todo continue this

    async def generate_image_card(self, msg, rank, xp):
        """generates an image card for the user"""
        xp = int(xp)
        user = msg.author
        avatar: disnake.Asset = user.display_avatar.with_size(512)

        # this for loop finds the closest level to the xp and defines the values accordingly
        x = 999999 * 9999999
        for key, value in LEVELS_AND_XP.items():
            if x > value - xp > 0 and not xp - value == xp:
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

            # get a font
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
            d.text((113, 130), rank, font=fnt, fill=(0, 0, 0, 255))

            d.rectangle((44, 186, 44 + width, 186 + 21), fill=(255, 255, 255, 255))

            txt.paste(avatar_img, (489, 23))

            out = Image.alpha_composite(base, txt)
            with BytesIO() as image_binary:
                out.save(image_binary, 'PNG')
                image_binary.seek(0)
                return File(fp=image_binary, filename='image.png')

    @staticmethod
    async def send_levelup(message: Message, level: int):
        user = message.author

        msg = f"""{user.mention}, you have leveled up to level {level}!
        """
        await message.channel.send(msg)


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
        return #todo remove this

        if message.author.bot:
            return
        await self.controller.handle_message(message)

    @commands.Cog.listener()
    async def on_ready(self):
        return #todo remove this
        self.controller = LevelsController(self.bot, self.bot.db)
        print(await self.controller.is_in_database(self.bot.user, self.bot.guilds[0]))
        await self.controller._update_record(member=self.bot.user, level=1, xp=0, total_xp=0,
                                             guild_id=self.bot.guilds[0].id, maybe_new_record=True)
        print(await self.controller.is_in_database(self.bot.user, self.bot.guilds[0]))  # todo remove

    @commands.slash_command()
    async def rank(self, inter: ApplicationCommandInteraction, user: Member):
        user = await self.controller.get_user(user.id)
        if not user:
            return await inter.send(file=await self.controller.generate_image_card(inter.original_message(), user.id, user.name))
        await inter.send(file=await self.controller.generate_image_card(inter.original_message(), user.xp, user.level))

    @staticmethod
    async def random_xp():
        return random.choice(xp_probability)

    def get_user(self, user_id: int):
        return self.controller.get_user(user_id)


def setup(bot: OGIROID):
    bot.add_cog(Level(bot))
