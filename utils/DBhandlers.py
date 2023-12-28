from __future__ import annotations, generator_stop
import asyncpg
import random
import time
from typing import (
    List,
    Literal,
    Optional,
    TYPE_CHECKING,
    Dict,
    Tuple,
    Sequence,
    Union,
    Any,
    Type,
)

from sqlalchemy import select, Result
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from utils.CONSTANTS import timings
from utils.cache import AsyncTTL
from utils.config import GConfig
from utils.db_models import Tag, Timezone, FlagQuiz
from utils.exceptions import *
from utils.models import (
    FlagQuizUser,
    BlacklistedUser,
    BirthdayModel,
    TimezoneModel,
    TagModel,
)
from utils.db_models import *

if TYPE_CHECKING:
    from utils.bot import OGIROID


class BaseModal:
    async def save(self):
        pass

    async def delete(self):
        pass


class ConfigHandler:
    def __init__(self, bot: "OGIROID", db: async_sessionmaker[AsyncSession]):
        self.bot = bot
        self.db = db
        self.config: Dict[dict] = {}

    async def load_config(self, guild_id: int):
        record = await self.db.fetchrow(
            "SELECT * FROM config WHERE guild_id = $1", guild_id
        )
        if record is None:
            await self.create_config(guild_id)
            return await self.load_config(guild_id)
        self.config[guild_id] = record

    async def get_config(self, guild_id: int) -> GConfig:
        if guild_id not in self.config:
            await self.load_config(guild_id)
        cnfg = self.config[guild_id]
        return GConfig(*cnfg)

    async def create_config(self, guild_id):
        await self.db.execute(
            "INSERT INTO config (guild_id) VALUES ($1)",
            guild_id,
        )

    async def get_boost(self, guild_id: int) -> int:
        config = await self.get_config(guild_id)
        return config.xp_boost


class FlagQuizHandler:
    def __init__(self, bot: "OGIROID", db: async_sessionmaker[AsyncSession]):
        self.bot = bot
        self.db = db

    async def get_user(self, user_id: int, guild_id: int) -> FlagQuiz:
        if await self.exists(user_id, guild_id):
            async with self.db.begin() as session:
                record = await session.execute(
                    select(FlagQuiz).filter_by(user_id=user_id, guild_id=guild_id)
                )
                user = record.scalar()
            return user
        else:
            raise UserNotFound

    async def exists(self, user_id: int, guild_id: int) -> bool:
        async with self.db.begin() as session:
            record = await session.execute(
                select(FlagQuiz).filter_by(user_id=user_id, guild_id=guild_id)
            )
            record = record.scalar()
        return record is not None

    async def get_leaderboard(
        self, order_by="correct", guild_id: int = None
    ) -> Sequence[FlagQuiz]:
        async with self.db.begin() as session:
            records = await session.execute(
                select(FlagQuiz)
                .filter_by(guild_id=guild_id)
                .order_by(getattr(FlagQuiz, order_by).desc())
                .limit(10)
            )
            leaderboard = records.scalars().all()
        if len(leaderboard) == 0:
            raise UsersNotFound
        return leaderboard

    async def add_data(
        self,
        user_id: int,
        tries: int,
        correct: int,
        user: FlagQuiz | None = None,
        guild_id: int = None,
    ) -> FlagQuiz or None:
        if user is not None:
            try:
                user = await self.get_user(user_id, guild_id)
            except UserNotFound:
                await self.add_user(user_id, guild_id, tries, correct)
                return

        async with self.db.begin() as session:
            user.tries += tries
            user.correct += correct
            if correct == 199:
                user.completed += 1
            session.add(user)
        return user

    async def add_user(
        self, user_id: int, guild_id: int, tries: int = 0, correct: int = 0
    ):
        if correct == 199:
            completed = 1
        else:
            completed = 0

        async with self.db.begin() as session:
            user = FlagQuiz(
                user_id=user_id,
                tries=tries,
                correct=correct,
                completed=completed,
                guild_id=guild_id,
            )
            session.add(user)

        return user


class BlacklistHandler:
    def __init__(self, bot, db: async_sessionmaker[AsyncSession]):
        self.bot = bot
        self.db = db
        self.blacklist: List[BlacklistedUser] = []
        self.cache = AsyncTTL(timings.HOUR * 2)

    async def get_user(self, user_id: int) -> BlacklistedUser:
        user = await self.cache.get(user_id)
        if user is not None:
            return user
        elif user_id in [user.id for user in self.blacklist]:
            user: BlacklistedUser = [
                user for user in self.blacklist if user.id == user_id
            ][0]
            await self.cache.set(user_id, user)
            return user
        else:
            raise UserNotFound

    async def startup(self):
        await self.bot.wait_until_ready()
        try:
            await self.load_blacklist()
        except BlacklistNotFound:
            print("[BLACKLIST] No blacklisted users found")

    async def count(self) -> int:
        return len(self.blacklist)

    async def load_blacklist(self):
        blacklist = []
        async with self.db.begin() as session:
            records = await session.execute(select(Blacklist))
            records = records.scalars().all()
        for record in records:
            blacklist.append(record)
        if len(blacklist) == 0:
            raise BlacklistNotFound
        print(f"[BLACKLIST] {len(blacklist)} blacklisted users found and loaded")
        self.blacklist = blacklist

    async def get(self, user_id: int) -> BlacklistedUser:
        return await self.get_user(user_id)

    async def add(
        self,
        user_id: int,
        reason: str,
        bot: bool,
        tickets: bool,
        tags: bool,
        expires: int,
    ):
        user = Blacklist(
            user_id=user_id,
            reason=reason,
            bot=bot,
            tickets=tickets,
            tags=tags,
            expires=expires,
        )
        async with self.db.begin() as session:
            session.add(user)
        self.blacklist.append(user)
        await self.cache.set(user_id, user)

    async def remove(self, user_id: int):
        async with self.db.begin() as session:
            user = await session.execute(select(Blacklist).filter_by(user_id=user_id))
            user = user.scalar()
            await session.delete(user)

        self.blacklist.remove(await self.get_user(user_id))
        await self.cache.remove(user_id)

    async def blacklisted(self, user_id: int) -> bool:
        if await self.cache.exists(user_id):
            return True
        elif any(user.id == user_id for user in self.blacklist):
            await self.cache.set(user_id, self.get_user(user_id))
            return True
        else:
            return False

    async def edit_flags(self, user_id: int, bot: bool, tickets: bool, tags: bool):
        async with self.db.begin() as session:
            user = await session.execute(select(Blacklist).filter_by(user_id=user_id))
            user = user.scalar()
            user.bot = bot
            user.tickets = tickets
            user.tags = tags
            session.add(user)
        indx = await self.get_user_index(user_id)
        user = self.blacklist[indx]
        user = self.blacklist[indx] = user
        await self.cache.set(user_id, user)

    async def edit_reason(self, user_id: int, reason: str):
        async with self.db.begin() as session:
            user = await session.execute(select(Blacklist).filter_by(user_id=user_id))
            user = user.scalar()
            user.reason = reason
            session.add(user)
        indx = await self.get_user_index(user_id)
        self.blacklist[indx] = user
        await self.cache.set(user_id, user)

    async def edit_expiry(self, user_id: int, expires: int):
        async with self.db.begin() as session:
            user = await session.execute(select(Blacklist).filter_by(user_id=user_id))
            user = user.scalar()
            user.expires = expires
            session.add(user)
        indx = await self.get_user_index(user_id)
        self.blacklist[indx] = user
        await self.cache.set(user_id, user)

    async def get_user_index(self, user_id) -> int:
        return self.blacklist.index(await self.get_user(user_id))


class TagManager:
    def __init__(self, bot: "OGIROID", db: async_sessionmaker[AsyncSession]):
        self.bot = bot
        self.db = db
        self.session = self.bot.session
        self.names = {"tags": [], "aliases": []}
        self.cache = AsyncTTL(timings.DAY / 2)  # cache tags for 12 hrs

    async def startup(self):
        await self.bot.wait_until_ready()
        print("[TAGS] Loading tags...")
        try:
            tags = await self.all()
            aliases = await self.get_aliases()
            for tag in tags:
                self.names["tags"].append(tag.name)
            for alias in aliases:
                self.names["aliases"].append(alias)
            print(f"[TAGS] Loaded {len(tags)} tags and {len(aliases)} aliases")
        except TagsNotFound:
            print("[TAGS] No tags found")

    async def get_tag_from_cache(self, name):
        name = await self.get_name(name)
        return await self.cache.get(name)

    async def exists(self, name, exception: TagException, should: bool) -> bool:
        """Returns True if the tag exists"""
        name = name.casefold()
        if await self.cache.exists(name):
            if should:
                return True
            raise exception

        else:
            full_list = self.names["tags"] + self.names["aliases"]
            if should:
                if name in full_list:
                    return True
                raise exception
            else:
                if name not in full_list:
                    return True
                raise exception

    async def create(self, name, content, owner):
        async with self.db.begin() as session:
            new_tag = Tag(
                name=name,
                content=content,
                owner=owner,
                created_at=int(time.time()),
                views=0,
            )
            session.add(new_tag)
        self.names["tags"].append(name)
        await self.cache.add(name, new_tag)

    async def get(self, name, /, force: bool = False) -> Type[Tag] | None:
        """
        Returns the tag object of the tag with the given name or alias
        args:
            name: the name or alias of the tag
            force: if True, will ignore the cache and get the tag from the database
        """
        name = await self.get_name(name)
        if not force:
            item = await self.cache.get(name)
            if item is not None:
                return item
            else:
                await self.cache.add(name, await self.get(name, force=True))

        async with self.db.begin() as session:
            record = await session.get(Tag, name)
        if record is None:
            return
        return record

    async def all(
        self, orderby: Literal["views", "created_at"] = "views", limit=10
    ) -> Sequence[Tag]:
        if orderby not in ["views", "created_at"]:
            raise ValueError("Invalid orderby value")

        async with self.db.begin() as session:
            records = await session.execute(
                select(Tag).order_by(getattr(Tag, orderby).desc()).limit(limit)
            )
            records = records.scalars().all()

        if len(records) == 0:
            raise TagsNotFound
        return records

    async def delete(self, name):
        async with self.db.begin() as session:
            await session.delete(await self.get_name(name))
        self.names["tags"].remove(name)
        for tag in await self.get_aliases(name):
            self.names["aliases"].remove(tag)
            await self.cache.delete(tag)
        await self.remove_aliases(name)

    async def update(self, name, param, new_value):
        async with self.db.begin() as session:
            tag = await session.get(Tag, name)
            setattr(tag, param, new_value)
        if param == "name":
            await self.cache.add(new_value, await self.get(name))
            await self.cache.remove(name)
        else:
            await self.cache.set(
                name, await self.get(name, force=True)
            )  # force to fetch directly from the database

    async def rename(self, name, new_name):
        name = await self.get_name(name)
        await self.update(name, "name", new_name)
        async with self.db.begin() as session:
            tag_relation = await session.execute(
                select(TagRelations).filter_by(name=name)
            )
            tag_relation.name = new_name

        self.names["tags"].append(new_name)
        self.names["tags"].remove(name)

    async def transfer(self, name, new_owner: int):
        name = await self.get_name(name)
        await self.update(name, "owner", new_owner)

    async def increment_views(self, name):
        name = await self.get_name(name)

        tag = await self.cache.get(name, default=False)
        if tag:
            tag.views += 1
            await self.cache.set(name, tag)
        async with self.db.begin() as session:
            tag = await session.get(Tag, name)
            tag.views += 1

    async def get_top(self, limit=10):
        tags = []
        async with self.db.begin() as session:
            records = await session.execute(
                select(Tag).order_by(Tag.views.desc()).limit(limit)
            )
            records = records.scalars().all()
        for record in records:
            tags.append(record)
        if len(tags) == 0:
            raise TagsNotFound
        return tags

    async def get_tags_by_owner(
        self,
        owner: int,
        limit=10,
        orderby: Literal["views", "created_at"] = "views",
    ):
        tags = []
        async with self.db.begin() as session:
            records = await session.execute(
                select(Tag)
                .filter_by(owner=owner)
                .order_by(getattr(Tag, orderby).desc())
                .limit(limit)
            )
            records = records.scalars().all()
        for record in records:
            tags.append(record)
        if len(tags) == 0:
            raise TagsNotFound
        return tags

    async def count(self) -> int:
        async with self.db.begin() as session:
            records = await session.execute(select(Tag))
            return len(records.scalars().all())

    async def get_name(self, name_or_alias: str | tuple):
        """gets the true name of a tag (not the alias)"""
        if isinstance(name_or_alias, tuple):
            return await self.get_name(name_or_alias[0])

        if type(name_or_alias) == str:
            name_or_alias = name_or_alias.casefold()  ## todo fix.
        elif type(name_or_alias) == TagRelations:
            name_or_alias = name_or_alias.alias.casefold()
        if name_or_alias in self.names["tags"]:
            return name_or_alias  # it's  a tag
        async with self.db.begin() as session:
            record = await session.execute(
                select(TagRelations).filter_by(alias=name_or_alias)
            )
            record = record.scalar()
        if record is None:
            raise TagNotFound(name_or_alias)
        return record.name

    async def add_alias(self, name, alias):
        name = await self.get_name(name)
        aliases = await self.get_aliases(name)
        if alias in aliases:
            raise AliasAlreadyExists
        elif len(aliases) > 10:
            raise AliasLimitReached
        elif alias in self.names["tags"] or alias in self.names["aliases"]:
            raise TagAlreadyExists
        async with self.db.begin() as session:
            new_relation = TagRelations(name=name, alias=alias)
            session.add(new_relation)
        self.names["aliases"].append(alias)
        await self.cache.add(alias, await self.get(name))

    async def remove_alias(self, name, alias):
        name = await self.get_name(name)
        if alias not in (await self.get_aliases(name)):
            raise AliasNotFound
        async with self.db.begin() as session:
            tag_relation = await session.execute(
                select(TagRelations).filter_by(name=name, alias=alias)
            )
            await session.delete(tag_relation.scalar())
        self.names["aliases"].remove(alias)
        await self.cache.delete(alias)

    async def random(self):
        return random.choice(self.names["tags"])

    async def remove_aliases(self, name):
        name = await self.get_name(name)
        aliases = await self.get_aliases(name)
        for alias in aliases:
            self.names["aliases"].remove(alias)
            await self.cache.delete(alias)
        async with self.db.begin() as session:
            await session.delete(select(TagRelations).filter_by(name=name))

    async def get_aliases(self, name: Optional = None) -> List[str] | TagNotFound:
        if not name:
            async with self.db.begin() as session:
                records = await session.execute(select(TagRelations))
                records = records.scalars()
            if records is None:
                return []
            return [row.alias for row in records]
        name = await self.get_name(name)
        async with self.db.begin() as session:
            records = await session.execute(select(TagRelations).filter_by(name=name))
            records = records.scalars().all()
        if records is None:
            return []
        return [record.alias for record in records]


class RolesHandler:
    """Stores message_id, role_id, emoji(example: <:starr:990647250847940668> or ⭐ depending on type of emoji
    and roles given out"""

    def __init__(self, bot, db: async_sessionmaker[AsyncSession]):
        self.bot = bot
        self.db = db
        self.messages = []

    async def startup(self):
        self.messages = await self.get_messages()

    async def exists(
        self, message_id: int, emoji: str, role_id: int
    ) -> bool | ReactionRole:
        """Check if msg exists in the database if it does, it returns the message else it returns False"""
        for msg in self.messages:
            if (
                msg.role_id == role_id
                and message_id == msg.message_id
                and str(emoji) == msg.emoji
            ):
                return msg
        return False

    async def get_messages(self):
        """get all messages from the database"""
        messages = []
        async with self.db.begin() as session:
            records = await session.execute(select(ReactionRole))
            records = records.scalars().all()

        for record in records:
            messages.append(record)

        print(f"[REACTION ROLES] Loaded {len(messages)} reaction roles")
        return messages

    async def create_message(self, message_id: int, role_id: int, emoji: str):
        """creates a message for a reaction role"""
        if await self.exists(message_id, emoji, role_id):
            raise ReactionAlreadyExists

        async with self.db.begin() as session:
            new_reaction = ReactionRole(
                message_id=message_id, role_id=role_id, emoji=emoji
            )
            session.add(new_reaction)

        self.messages.append(new_reaction)

    async def increment_roles_given(self, message_id: str, emoji: str):
        """increments the roles given out for a message"""
        async with self.db.begin() as session:
            reaction_role = await session.execute(
                select(ReactionRole).filter_by(message_id=message_id, emoji=emoji)
            )
            reaction_role.scalar().roles_given += 1

        for message in self.messages:
            if message.message_id == message_id and message.emoji == emoji:
                message.roles_given += 1
                return

    async def remove_message(self, message_id: int, emoji: str, role_id: int):
        """removes a role from the database"""
        msg = await self.exists(message_id, emoji, role_id)
        if not msg:
            raise ReactionNotFound
        async with self.db.begin() as session:
            await session.delete(msg)

    async def remove_messages(self, message_id: int):
        """Removes all messages matching the id"""
        async with self.db.begin() as session:
            await session.delete(select(ReactionRole).filter_by(message_id=message_id))
        self.messages = [msg for msg in self.messages if msg.message_id != message_id]


class WarningHandler:
    def __init__(self, bot, db: async_sessionmaker[AsyncSession]):
        self.db = db
        self.bot = bot

    async def get_warning(self, warning_id: int) -> Optional[Warnings]:
        async with self.db.begin() as session:
            result = await session.get(Warnings, warning_id)
            return result

    async def get_warnings(self, user_id: int, guild_id: int) -> Sequence[Warnings]:
        async with self.db.begin() as session:
            warnings = await session.execute(
                select(Warnings).filter_by(user_id=user_id, guild_id=guild_id)
            )
            return warnings.scalars().all()

    async def create_warning(
        self, user_id: int, reason: str, moderator_id: int, guild_id: int
    ):
        async with self.db.begin() as session:
            warning = Warnings(
                user_id=user_id,
                reason=reason,
                moderator_id=moderator_id,
                guild_id=guild_id,
            )
            session.add(warning)

            return warning

    async def remove_warning(self, warning_id: int, guild_id: int) -> bool:
        warning = await self.get_warning(warning_id)
        if warning is None:
            return False
        async with self.db.begin() as session:
            await session.delete(warning)

        return True


class BirthdayHandler:
    def __init__(self, bot, db: async_sessionmaker[AsyncSession]):
        self.db = db
        self.bot = bot

    async def get_user(self, user_id: int) -> Optional[BirthdayModel]:
        async with self.db.begin() as session:
            result = await session.execute(select(Birthday).filter_by(user_id=user_id))
            result = result.scalar()
            return result

    async def get_users(self) -> List[BirthdayModel]:
        users = []
        async with self.db.begin() as session:
            records = await session.execute(select(Birthday))
            records = records.scalars().all()
        for record in records:
            users.append(record)
        return users

    async def delete_user(self, user_id: int) -> bool:
        user = await self.get_user(user_id)
        if user is None:
            raise UserNotFound
        async with self.db.begin() as session:
            await session.delete(user)

        return True

    async def create_user(self, user_id: int, birthday: str) -> bool:
        user = await self.get_user(user_id)
        if user is not None:
            raise UserAlreadyExists
        async with self.db.begin() as session:
            birthday = Birthday(
                user_id=user_id,
                birthday=birthday,
                birthday_last_changed=int(time.time()),
            )
            session.add(birthday)

        return True

    async def update_user(self, user_id: int, birthday: str) -> bool:
        user = await self.get_user(user_id)
        if user is None:
            raise UserNotFound
        async with self.db.begin() as session:
            user.birthday = birthday
            user.birthday_last_changed = int(time.time())
            session.add(user)

        return True


class TimezoneHandler:
    def __init__(self, bot, db: async_sessionmaker[AsyncSession]):
        self.db = db
        self.bot = bot

    async def get_user(self, user_id: int) -> Optional[Timezone]:
        async with self.db.begin() as session:
            record = await session.execute(select(Timezone).filter_by(user_id=user_id))
            record = record.scalar()
            return record

    async def get_users(self) -> Sequence[Timezone]:
        async with self.db.begin() as session:
            records = await session.execute(select(Timezone))
            records = records.scalars().all()
            return records

    async def delete_user(self, user_id: int) -> bool:
        user = await self.get_user(user_id)
        if user is None:
            raise UserNotFound
        async with self.db.begin() as session:
            await session.delete(user)

        return True

    async def create_user(self, user_id: int, timezone: str) -> bool:
        user = await self.get_user(user_id)
        if user is not None:
            raise UserAlreadyExists
        async with self.db.begin() as session:
            timezone = Timezone(
                user_id=user_id,
                timezone=timezone,
                timezone_last_changed=int(time.time()),
            )
            session.add(timezone)

        return True

    async def update_user(self, user_id: int, timezone: str) -> bool:
        user: Timezone = await self.get_user(user_id)
        if user is None:
            raise UserNotFound
        async with self.db.begin() as session:
            user.timezone = timezone
            user.timezone_last_changed = int(time.time())
            session.add(user)

        return True
