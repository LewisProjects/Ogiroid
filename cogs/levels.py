from collections import namedtuple
from typing import Tuple, Union, Optional, Dict

from disnake import Message, Member, MessageType
from disnake.ext import commands
import random

from disnake.ext.commands import CooldownMapping, BucketType

from utils.bot import OGIROID
from utils.CONSTANTS import xp_probability, LEVELS_AND_XP
from utils.exceptions import LevelingSystemError

FakeGuild = namedtuple("FakeGuild", "id")


class LevelsController:
    def __init__(self, bot: OGIROID, db):
        self.bot = bot
        self.db = db

        self.__rate = 2
        self.__per = 60
        self._cooldown = CooldownMapping.from_cooldown(self.__rate, self.__per, BucketType.user)
        self.__max_level__ = len(LEVELS_AND_XP) - 1

    def get_xp_for_level(self, level: int) -> int:
        """
        Returns the total amount of XP needed for the specified level. Levels go from 0-100
        """
        try:
            return LEVELS_AND_XP[str(level)]
        except KeyError:
            raise ValueError(f"Levels only go from 0-{self.__max_level__}, {level} is not a valid level")

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
        record = await self.db.execute("SELECT EXISTS( SELECT 1 FROM levels WHERE user_id = ? AND guild_id = ? )", (member.id, guild.id if guild else member.guild.id))
        return bool((await record.fetchone())[0])

    async def _update_record(
        self, member: Union[Member, int], level: int, xp: int, total_xp: int, guild_id: int, **kwargs
    ) -> None:
        maybe_new_record = kwargs.get("maybe_new_record", False)

        if await self.is_in_database(
            member, guild=FakeGuild(id=guild_id)
        ):
            await self.db.execute(
                "UPDATE levels SET level = ?, xp = ?, total_xp = ? WHERE user_id = ? AND guild_id = ?",
                (level, xp, total_xp, member.id if isinstance(member, Member) else member, guild_id),)
        else:
            await self.db.execute(
                "INSERT INTO levels (user_id, guild_id, level, xp, total_xp) VALUES (?, ?, ?, ?, ?)",
                (guild_id, member.id if isinstance(member, Member) else member, level, xp, total_xp),
            )
        await self.db.commit()

    async def set_level(self, member: Member, level: int) -> None:
        if 0 <= level <= self.__max_level__:
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
            raise LevelingSystemError(f'Parameter "level" must be from 0-{self.__max_level__}')

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

        #if user.exp > xp_needed:
        #    user.lvl += 1
        #    user.xp = 0
        #    await self.db.update_user(user)
        #    await sucEmb(message, f"You have leveled up to level {user.lvl}!")
        #    return True

    async def get_user(self, user_id: int):
        return self.db.get_user(user_id)



class Level(commands.Cog):
    def __init__(self, bot: OGIROID):
        self.bot = bot
        self.levels = LEVELS_AND_XP
        self.controller: LevelsController = None

    async def generate_image_card(self, msg, lvl, rank):
        """generates an image card for the user"""
        user = msg.author
        pass


    def cog_unload(self) -> None:
        pass

    @commands.Cog.listener()
    async def on_rankup(self, msg: Message, rank: int, level: int, exp: Tuple[int, int]):
        """
        Called when a user reaches a certain level
        """
        #await self.generate_image_card(msg, rank, user_id, level)  # todo use rankcads
        raw = f"""
**Username:** {msg.author.name}
**Experience:** {exp[0]}/{exp[1]}
**Level:** {level}
**rank:** {rank}"""
        await msg.channel.send(raw)


    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        await self.controller.handle_message(message)

    @commands.Cog.listener()
    async def on_ready(self):
        self.controller = LevelsController(self.bot, self.bot.db)
        print(await self.controller.is_in_database(self.bot.user, self.bot.guilds[0]))
        await self.controller._update_record(member=self.bot.user, level=1, xp=0, total_xp=0, guild_id=self.bot.guilds[0].id, maybe_new_record=True)
        print(await self.controller.is_in_database(self.bot.user, self.bot.guilds[0]))

    def get_user(self, user_id: int):
        return self.controller.get_user(user_id)





def setup(bot: OGIROID):
    bot.add_cog(Level(bot))
