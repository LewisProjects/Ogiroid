from __future__ import annotations

from io import BytesIO
from typing import Union, Tuple, Dict

import disnake
from PIL import Image
from PIL import ImageDraw

from utils.http import session


async def getavatar(user: Union[disnake.User, disnake.Member]) -> bytes:
    disver = str(disnake.__version__)
    if disver.startswith("1"):
        async with session.get(str(user.avatar_url)) as response:
            avatarbytes = await response.read()
        await session.close()
    elif disver.startswith("2"):
        async with session.get(str(user.display_avatar.url)) as response:
            avatarbytes = await response.read()
        await session.close()
    return avatarbytes


def strip_num(num: int | str):
    num = int(num)
    if num >= 1000:
        if num >= 1000000:
            num = f"{round(num / 1000000, 1)}M"
        else:
            num = f"{round(num / 1000, 1)}K"
    return num


class Rankcard:
    def __init__(self):
        self.POSITIONS: Dict[str, Tuple] = {
            "AVATAR_DIAM": (189, 189),
            "AVATAR_POS": (107, -186),
            "TEXT_POS": (-177, -348),
            "STATUS_POS": (290, 330, -40, 20),
        }

    async def getavatar(self, user: Union[disnake.User, disnake.Member]) -> bytes:
        async with session.get(str(user.display_avatar.url)) as response:
            avatarbytes = await response.read()
        with Image.open(BytesIO(avatarbytes)) as im:
            USER_IMG = im.resize(self.POSITIONS["AVATAR_DIAM"])
        return USER_IMG

    async def create_img(
        self,
        user: disnake.Member | disnake.User,
        level: int | str,
        xp: Tuple[int, int],
        rank: int | str,
    ) -> bytes:
        """
        args:
            user: the user that the rankcard is for
            level: the user's current level
            xp: A tuple of (currentXP, NeededXP)
        """
        level = f"{level:,d}"
        currentxp = xp[0]
        neededxp = xp[1]
        missingxp = xp[1] - xp[0]
        USER_IMG = await self.getavatar(user)
        # todo change text to using \n
        text = f""" 
Username: {user.name} 
Experience: {currentxp:,d} / {neededxp:,d} ({missingxp:,d} missing)
Level {level}
Rank #{rank:,d}"""
        BACKGROUND = Image.open("./assets/images/rank/background.png")
        draw = ImageDraw.Draw(BACKGROUND)

        draw.ellipse((160, 170, 208, 218), fill=0)  # status outline

        # status
        try:

            if user.status == disnake.Status.online:
                draw.ellipse(self.POSITIONS["STATUS_POS"], fill=(67, 181, 129))
            elif user.status == disnake.Status.offline:
                draw.ellipse(self.POSITIONS["STATUS_POS"], fill=(116, 127, 141))
            elif user.status == disnake.Status.dnd:
                draw.ellipse(self.POSITIONS["STATUS_POS"], fill=(240, 71, 71))
            elif user.status == disnake.Status.idle:
                draw.ellipse(self.POSITIONS["STATUS_POS"], fill=(250, 166, 26))
        except:
            draw.ellipse((165, 175, 204, 214), fill=(114, 137, 218))

        final_buffer = BytesIO()

        BACKGROUND.save(final_buffer, "png")
        final_buffer.seek(0)
        return final_buffer
