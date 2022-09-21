from __future__ import annotations, generator_stop

import random
import time
from typing import List, Literal, Optional, TYPE_CHECKING

from utils.CONSTANTS import timings
from utils.cache import AsyncTTL
from utils.exceptions import *
from utils.models import FlagQuizUser, BlacklistedUser, Tag, ReactionRole, WarningModel

if TYPE_CHECKING:
    from utils.bot import OGIROID


class FlagQuizHandler:
    def __init__(self, bot: 'OGIROID', db):
        self.bot = bot
        self.db = db
        self.cache = AsyncTTL(timings.MINUTE * 4)

    async def get_user(self, user_id: int) -> FlagQuizUser:
        user = await self.cache.get(str(user_id))
        if user is not None:
            return user
        elif await self.exists(user_id):
            async with self.db.execute(f"SELECT * FROM flag_quizz WHERE user_id = {user_id}") as cur:
                rawUserData = await cur.fetchone()
                user = FlagQuizUser(*rawUserData)
                await self.cache.set(str(user_id), user)
                return user

        else:
            raise UserNotFound

    async def exists(self, user_id: int):
        async with self.db.execute(f"SELECT EXISTS(SELECT 1 FROM flag_quizz WHERE user_id=?)", [user_id]) as cur:
            return bool((await cur.fetchone())[0])

    async def get_leaderboard(self, order_by="correct"):
        leaderboard = []
        async with self.db.execute(
            f"SELECT user_id, tries, correct, completed FROM flag_quizz ORDER BY {order_by} DESC LIMIT 10"
        ) as cur:
            async for row in cur:
                leaderboard.append(FlagQuizUser(*row))
            if len(leaderboard) == 0:
                raise UsersNotFound
            return leaderboard

    async def add_data(self, user_id: int, tries: int, correct: int, user: Optional[FlagQuizUser] = None) -> FlagQuizUser:
        if user is not None:
            try:
                user = await self.get_user(user_id)
            except UserNotFound:
                await self.add_user(user_id, tries, correct)
                return

        if correct == 199:
            completed = user.completed + 1
        else:
            completed = user.completed
        tries += user.tries
        correct += user.correct

        async with self.db.execute(
            f"UPDATE flag_quizz SET tries = {tries}, correct = {correct}, completed = {completed} WHERE user_id = {user_id}"
        ):
            await self.db.commit()
        return FlagQuizUser(user_id, tries, correct, completed)

    async def add_user(self, user_id: int, tries: int = 0, correct: int = 0):
        if correct == 199:
            completed = 1
        else:
            completed = 0

        async with self.db.execute(
            f"INSERT INTO flag_quizz (user_id, tries, correct, completed) VALUES ({user_id}, {tries}, {correct}, {completed})"
        ):
            await self.db.commit()


"""
note to any future contributors:
the self.exists() calls are very carefully used.
if you add a call to ANY of the functions in TagManager MAKE SURE it's called once
"""


class BlacklistHandler:
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        self.blacklist: List[BlacklistedUser] = []
        self.cache = AsyncTTL(timings.HOUR * 2)

    async def get_user(self, user_id: int) -> BlacklistedUser:
        """
        explanation: if user is in the cache return user; else: fetch it and add it to the cache then return user
        """
        user = await self.cache.get(user_id)
        if user is not None:
            return user
        elif user_id in [user.id for user in self.blacklist]:
            user: BlacklistedUser = [user for user in self.blacklist if user.id == user_id][0]
            await self.cache.add(user_id, user)
            return user
        else:
            raise UserNotFound

    async def startup(self):
        """waits for the bot to be ready and then loads the blacklist"""
        await self.bot.wait_until_ready()
        try:
            await self.load_blacklist()
        except BlacklistNotFound:
            print("[BLACKLIST] No blacklisted users found")

    async def count(self) -> int:
        """Returns the amount of blacklisted users"""
        return len(self.blacklist)

    async def load_blacklist(self):
        """Loads the blacklist into memory"""
        blacklist = []
        async with self.db.execute(f"SELECT * FROM blacklist") as cur:
            async for row in cur:
                blacklist.append(BlacklistedUser(*row).fix_db_types())
        if len(blacklist) == 0:
            raise BlacklistNotFound
        print(f"[BLACKLIST] {len(blacklist)} blacklisted users found and loaded")
        self.blacklist = blacklist

    async def get(self, user_id: int) -> BlacklistedUser:
        """Returns the BlacklistedUser object of the user"""
        return self.get_user(user_id)

    async def add(self, user_id: int, reason: str, bot: bool, tickets: bool, tags: bool, expires: int):
        """Adds a user to the blacklist"""
        await self.db.execute(
            f"INSERT INTO blacklist (user_id, reason, bot, tickets, tags, expires) VALUES (?, ?, ?, ?, ?, ?)",
            [user_id, reason, bot, tickets, tags, expires],
        )
        await self.db.commit()
        user = BlacklistedUser(user_id, reason, bot, tickets, tags, expires)
        self.blacklist.append(user)
        await self.cache.add(user_id, user)

    async def remove(self, user_id: int):
        """Removes a user from the blacklist"""
        await self.db.execute(f"DELETE FROM blacklist WHERE user_id = ?", [user_id])
        await self.db.commit()
            self.blacklist.remove(await self.get_user(user_id))
        await self.cache.remove(user_id)

    async def blacklisted(self, user_id: int) -> bool:
        """Returns True if the user is blacklisted"""
        if await self.cache.exists(user_id):
            return True
        elif any(user.id == user_id for user in self.blacklist):
            await self.cache.add(
                user_id, self.get_user(user_id)
            )
            return True
        else:
            return False

    async def edit_flags(self, user_id: int, bot: bool, tickets: bool, tags: bool):
        """Edits the flags (blacklist perms) of a user"""
        await self.db.execute(
            f"UPDATE blacklist SET bot = ?, tickets = ?, tags = ? WHERE user_id = ?", [bot, tickets, tags, user_id]
        )
        await self.db.commit()
        indx = self.get_user_index(user_id)
        user = self.blacklist[indx]
        user.bot = bot
        user.tickets = tickets
        user.tags = tags
        user = self.blacklist[indx] = user
        await self.cache.set(user_id, user)

    async def edit_reason(self, user_id: int, reason: str):
        """Edits the blacklist reason of a user"""
        await self.db.execute(f"UPDATE blacklist SET reason = ? WHERE user_id = ?", [reason, user_id])
        await self.db.commit()
        indx = self.get_user_index(user_id)
        user = self.blacklist[indx]
        user.reason = reason
        self.blacklist[indx] = user
        await self.cache.set(user_id, user)

    async def edit_expiry(self, user_id: int, expires: int):
        """Edits when the blacklist expires of a user"""
        await self.db.execute(f"UPDATE blacklist SET expires = ? WHERE user_id = ?", [expires, user_id])
        await self.db.commit()
        indx = self.get_user_index(user_id)
        user = self.blacklist[indx]
        user.expires = expires
        self.blacklist[indx] = user
        await self.cache.set(user_id, user)

    def get_user_index(self, user_id) -> int:
        """Returns the index of the user in the blacklist"""
        return self.blacklist.index(self.get_user(user_id))


class TagManager:
    def __init__(self, bot: 'OGIROID', db):
        self.bot = bot
        self.db = db
        self.session = self.bot.session
        self.names = {"tags": [], "aliases": []}
        self.cache = AsyncTTL(timings.DAY / 2)  # cache tags for 12 hrs
        self.pool = self.bot.pool

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
        await self.db.execute(
            "INSERT INTO tags (tag_id, content, owner, created_at, views) VALUES (?, ?, ?, ?, 0)",
            [name, content, owner, int(time.time())],
        )
        await self.db.commit()
        self.names["tags"].append(name)
        await self.cache.add(name, Tag(name, content, owner, int(time.time()), 0))

    async def get(self, name, /, force: bool = False) -> Tag:
        """
        Returns the tag object of the tag with the given name or alias
        args:
            name: the name of the tag
            force: if True, will ignore the cache and get the tag from the database
        """
        name = await self.get_name(name)
        if not force:
            item = await self.cache.get(name)
            if item is not None:
                return item
            else:
                await self.cache.add(name, await self.get(name, force=True))

        _cur = await self.db.execute("SELECT * FROM tags WHERE tag_id= ?", [name])
        raw = await _cur.fetchone()
        if raw is None:
            return
        return Tag(*raw)

    async def all(self, orderby: Literal["views", "created_at"] = "views", limit=10) -> List[Tag]:
        tags = []
        async with self.db.execute(f"SELECT * FROM tags ORDER BY {orderby} DESC{f' LIMIT {limit}' if limit > 1 else ''}") as cur:
            async for row in cur:
                tags.append(Tag(*row))
        if len(tags) == 0:
            raise TagsNotFound
        return tags

    async def delete(self, name):
        name = await self.get_name(name)
        await self.db.execute("DELETE FROM tags WHERE tag_id = ?", [name])
        await self.db.commit()
        # internals below
        self.names["tags"].remove(name)
        for tag in await self.get_aliases(name):
            self.names["aliases"].remove(tag)
            await self.cache.delete(tag)
        await self.remove_aliases(name)

    async def update(self, name, param, new_value):
        async with self.db.execute(f"UPDATE tags SET {param} = ? WHERE tag_id = ?", [new_value, name]):
            await self.db.commit()
        if param == "tag_id":
            await self.cache.add(new_value, await self.get(name))
            await self.cache.remove(name)
        else:
            await self.cache.set(name, await self.get(name, force=True))  # force to fetch directly from the database

    async def rename(self, name, new_name):
        name = await self.get_name(name)
        await self.update(name, "tag_id", new_name)
        async with self.db.execute(f"UPDATE tag_relations SET tag_id = ? WHERE tag_id = ?", [new_name, name]):
            await self.db.commit()

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
        await self.db.execute("UPDATE tags SET views = views + 1 WHERE tag_id = ?", [name])
        await self.db.commit()

    async def get_top(self, limit=10):
        tags = []
        async with self.db.execute(f"SELECT tag_id, views FROM tags ORDER BY views DESC LIMIT {limit}") as cur:
            async for row in cur:
                tags.append(Tag(*row))
        if len(tags) == 0:
            raise TagsNotFound
        return tags

    async def get_tags_by_owner(self, owner: int, limit=10, orderby: Literal["views", "created_at"] = "views"):
        tags = []
        async with self.db.execute(
            f"SELECT tag_id, views FROM tags WHERE owner = {owner} ORDER BY {orderby} DESC LIMIT {limit}"
        ) as cur:
            async for row in cur:
                tags.append(Tag(*row))
        if len(tags) == 0:
            raise TagsNotFound
        return tags

    async def count(self) -> int:
        async with self.db.execute("SELECT COUNT(*) FROM tags") as cur:
            return int(tuple(await cur.fetchone())[0])

    async def get_name(self, name_or_alias):
        """gets the true name of a tag (not the alias)"""

        name_or_alias = name_or_alias.casefold()
        if name_or_alias in self.names["tags"]:
            return name_or_alias  # it's  a tag
        _cur = await self.db.execute("SELECT tag_id FROM tag_relations WHERE alias = ?", [name_or_alias])
        value = await _cur.fetchone()
        if value is None:
            raise TagNotFound(name_or_alias)
        return value

    async def add_alias(self, name, alias):
        name = await self.get_name(name)
        aliases = await self.get_aliases(name)
        if alias in aliases:
            raise AliasAlreadyExists
        elif len(aliases) > 10:
            raise AliasLimitReached
        await self.db.execute("INSERT INTO tag_relations (tag_id, alias) VALUES (?, ?)", [name, alias])
        await self.db.commit()
        self.names["aliases"].append(alias)
        await self.cache.add(alias, await self.get(name))

    async def remove_alias(self, name, alias):
        name = await self.get_name(name)
        if alias not in (await self.get_aliases(name)):
            raise AliasNotFound
        await self.db.execute("DELETE FROM tag_relations WHERE tag_id = ? AND alias = ?", [name, alias])
        await self.db.commit()
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
        await self.db.execute("DELETE FROM tag_relations WHERE tag_id = ?", [name])
        await self.db.commit()

    async def get_aliases(self, name: Optional = None) -> List[str] | TagNotFound:
        if not name:
            async with self.db.execute("SELECT * FROM tag_relations") as cur:
                content = await cur.fetchall()
                if content is None:
                    return []
                return [row[1] for row in content]
        name = await self.get_name(name)
        async with self.db.execute("SELECT * FROM tag_relations WHERE tag_id = ?", [name]) as cur:
            content = await cur.fetchall()
            if content is None:
                return []
        return [alias for tag_id, alias in list(set(content))]


class RolesHandler:
    """Stores message_id, role_id, emoji(example: <:starr:990647250847940668> or ⭐ depending on type of emoji
    and roles given out"""

    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        self.messages = []

    async def startup(self):
        self.messages = await self.get_messages()

    async def exists(self, message_id: int, emoji: str, role_id: int) -> bool | ReactionRole:
        """Check if msg exists in the database if it does, it returns the message else it returns False"""
        for msg in self.messages:
            if msg.role_id == role_id and message_id == msg.message_id and str(emoji) == msg.emoji:
                return msg
        return False

    async def get_messages(self):
        """get all messages from the database"""
        messages = []
        async with self.db.execute(f"SELECT message_id, role_id, emoji, roles_given FROM reaction_roles") as cur:
            async for row in cur:
                messages.append(ReactionRole(*row))
            return messages

    async def create_message(self, message_id: int, role_id: int, emoji: str):
        """creates a message for a reaction role"""
        if await self.exists(message_id, emoji, role_id):
            raise ReactionAlreadyExists
        await self.db.execute(
            "INSERT INTO reaction_roles (message_id, role_id, emoji) VALUES (?, ?, ?)", [message_id, role_id, emoji]
        )
        await self.db.commit()

        self.messages.append(ReactionRole(message_id, role_id, emoji, 0))

    async def increment_roles_given(self, message_id: str, emoji: str):
        """increments the roles given out for a message"""
        await self.db.execute(
            "UPDATE reaction_roles SET roles_given = roles_given + 1 WHERE message_id = ? AND emoji = ?",
            [message_id, emoji],
        )
        await self.db.commit()
        # todo: cache remove below
        for message in self.messages:
            if message.message_id == message_id and message.emoji == emoji:
                message.roles_given += 1
                return

    async def remove_message(self, message_id: int, emoji: str, role_id: int):
        """removes a message from the database"""
        msg = await self.exists(message_id, emoji, role_id)
        if not msg:
            raise ReactionNotFound
        await self.db.execute(
            "DELETE FROM reaction_roles WHERE message_id = ? AND emoji = ? AND role_id = ?",
            [message_id, emoji, role_id],
        )
        await self.db.commit()
        self.messages.remove(msg)

    async def remove_messages(self, message_id: int):
        """Removes all messages matching the id"""
        await self.db.execute("DELETE FROM reaction_roles WHERE message_id = ?", [message_id])
        await self.db.commit()
        self.messages = [msg for msg in self.messages if msg.message_id != message_id]


class WarningHandler:
    def __init__(self, bot, db):
        self.db = db
        self.bot = bot

    async def get_warning(self, warning_id: int) -> Optional[WarningModel]:
        async with self.db.execute("SELECT * FROM warnings WHERE warning_id = ?", [warning_id]) as cur:
            content = await cur.fetchone()
            if content is None:
                return None
            return WarningModel(*content)

    async def get_warnings(self, user_id: int) -> List[WarningModel]:
        warnings = []
        async with self.db.execute("SELECT * FROM warnings WHERE user_id = ?", [user_id]) as cur:
            async for row in cur:
                warnings.append(WarningModel(*row))
        return warnings

    async def create_warning(self, user_id: int, reason: str, moderator_id: int):
        await self.db.execute(
            "INSERT INTO warnings (user_id, reason, moderator_id) VALUES (?, ?, ?)", [user_id, reason, moderator_id]
        )
        await self.db.commit()
        return True

    async def remove_all_warnings(self, user_id: int) -> bool:
        warnings = await self.get_warnings(user_id)
        if len(warnings) == 0:
            return False
        await self.db.execute("DELETE FROM warnings WHERE user_id = ?", [user_id])
        await self.db.commit()

    async def remove_warning(self, warning_id: int) -> bool:
        warning = await self.get_warning(warning_id)
        if warning is None:
            return False
        await self.db.execute("DELETE FROM warnings WHERE warning_id = ?", [warning_id])
        await self.db.commit()
        return True
