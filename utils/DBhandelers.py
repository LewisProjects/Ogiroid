from __future__ import annotations

import time
from typing import List, Literal, Optional

from utils.exceptions import *
from utils.models import FlagQuizUser, BlacklistedUser, Tag


class FlagQuizHandler:
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db

    async def get_user(self, user_id: int):
        users = []
        async with self.db.execute(f"SELECT * FROM flag_quizz WHERE user_id = {user_id}") as cur:
            async for row in cur:
                users.append(FlagQuizUser(*row))
        if len(users) == 0:
            raise FlagQuizUserNotFound
        return users

    async def get_leaderboard(self, order_by="correct"):
        leaderboard = []
        async with self.db.execute(
            f"SELECT user_id, tries, correct, completed FROM flag_quizz ORDER BY {order_by} DESC LIMIT 10"
        ) as cur:
            async for row in cur:
                leaderboard.append(FlagQuizUser(*row))
            if len(leaderboard) == 0:
                raise FlagQuizUsersNotFound
            return leaderboard

    async def add_data(self, user_id: int, tries: int, correct: int):
        try:
            user = await self.get_user(user_id)
            user = user[0]
        except FlagQuizUserNotFound:
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

    async def add_user(self, user_id: int, tries: int, correct: int):
        if correct == 199:
            completed = 1
        else:
            completed = 0

        async with self.db.execute(
            f"INSERT INTO flag_quizz (user_id, tries, correct, completed) VALUES ({user_id}, {tries}, {correct}, {completed})"
        ):
            await self.db.commit()


class BlacklistHandler:
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        self.blacklist: List[BlacklistedUser] = []

    def get_user(self, user_id: int) -> BlacklistedUser:
        return [user for user in self.blacklist if user.id == user_id][0]

    async def startup(self):
        await self.bot.wait_until_ready()
        try:
            await self.load_blacklist()
        except BlacklistNotFound:
            print("[BLACKLIST] No blacklisted users found")

    async def count(self):
        return len(self.blacklist)

    async def load_blacklist(self):
        blacklist = []
        async with self.db.execute(f"SELECT * FROM blacklist") as cur:
            async for row in cur:
                blacklist.append(BlacklistedUser(*row).fix_db_types())
        if len(blacklist) == 0:
            raise BlacklistNotFound
        print(f"[BLACKLIST] {len(blacklist)} blacklisted users found and loaded")
        self.blacklist = blacklist

    async def get(self, user_id: int):
        return self.get_user(user_id)

    async def add(self, user_id: int, reason: str, bot: bool, tickets: bool, tags: bool, expires: int):
        await self.db.execute(
            f"INSERT INTO blacklist (user_id, reason, bot, tickets, tags, expires) VALUES (?, ?, ?, ?, ?, ?)",
            [user_id, reason, bot, tickets, tags, expires],
        )
        await self.db.commit()
        self.blacklist.append(BlacklistedUser(user_id, reason, bot, tickets, tags, expires))

    async def remove(self, user_id: int):
        await self.db.execute(f"DELETE FROM blacklist WHERE user_id = ?", [user_id])
        await self.db.commit()
        self.blacklist.remove(self.get_user(user_id))

    async def blacklisted(self, user_id: int):
        return any(user.id == user_id for user in self.blacklist)

    async def edit_flags(self, user_id: int, bot: bool, tickets: bool, tags: bool):
        await self.db.execute(
            f"UPDATE blacklist SET bot = ?, tickets = ?, tags = ? WHERE user_id = ?", [bot, tickets, tags, user_id]
        )
        await self.db.commit()
        self.blacklist[self.get_user_index(user_id)].bot = bot
        self.blacklist[self.get_user_index(user_id)].tickets = tickets
        self.blacklist[self.get_user_index(user_id)].tags = tags

    async def edit_reason(self, user_id: int, reason: str):
        await self.db.execute(f"UPDATE blacklist SET reason = ? WHERE user_id = ?", [reason, user_id])
        await self.db.commit()
        self.blacklist[self.blacklist.index(self.get_user(user_id))].reason = reason

    async def edit_expiry(self, user_id: int, expires: int):
        await self.db.execute(f"UPDATE blacklist SET expires = ? WHERE user_id = ?", [expires, user_id])
        await self.db.commit()
        self.blacklist[self.blacklist.index(self.get_user(user_id))].expires = expires

    def get_user_index(self, user_id):
        return self.blacklist.index(self.get_user(user_id))


""" note to any future contributors:
the self.exists() calls are very carefully used.
if you add a call to ANY of the functions in TagManager MAKE SURE it's called once
"""


class TagManager:
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        self.session = self.bot.session
        self.names = {"tags": [], "aliases": []}

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

    async def exists(self, name, exception: TagException, should: bool) -> bool | TagException:
        full_list = self.names["tags"] + (self.names["aliases"])
        name = name.casefold()
        if should:
            if name in full_list:
                return True
            raise exception
        else:
            if name not in full_list:
                return True
            raise exception

    async def create(self, name, content, owner):
        await self.exists(name, TagAlreadyExists, should=False)
        self.names["tags"].append(name)
        await self.db.execute(
            "INSERT INTO tags (tag_id, content, owner, views, created_at) VALUES (?, ?, ?, 0, ?)",
            [name, content, owner, int(time.time())],
        )
        await self.db.commit()

    async def get(self, name) -> Tag | TagNotFound:
        await self.exists(name, TagNotFound, should=True)
        name = await self.get_name(name)
        async with self.db.execute("SELECT * FROM tags WHERE tag_id= ?", [name]) as cur:
            async for row in cur:
                return Tag(*row)

    async def all(self, orderby: Literal["views", "created_at"] = "views", limit=10) -> List[Tag]:
        tags = []
        async with self.db.execute(f"SELECT * FROM tags ORDER BY {orderby} DESC{f' LIMIT {limit}' if limit > 1 else ''}") as cur:
            async for row in cur:
                tags.append(Tag(*row))
        if len(tags) == 0:
            raise TagsNotFound
        return tags

    async def delete(self, name):
        await self.exists(name, TagNotFound, should=True)
        name = await self.get_name(name)
        for tag in await self.get_aliases(name):
            self.names["aliases"].remove(tag)
        await self.remove_aliases(name)
        self.names["tags"].remove(name)
        await self.db.execute("DELETE FROM tags WHERE tag_id = ?", [name])
        await self.db.commit()

    async def update(self, name, param, new_value):
        async with self.db.execute(f"UPDATE tags SET {param} = ? WHERE tag_id = ?", [new_value, name]):
            await self.db.commit()

    async def rename(self, name, new_name):
        await self.exists(name, TagNotFound, should=True)  # if the tag doesn't exist, it will raise TagNotFound
        await self.exists(
            new_name, TagAlreadyExists, should=False
        )  # if new tag's name already exists, it will raise TagAlreadyExists
        name = await self.get_name(name)
        await self.update(name, "tag_id", new_name)
        async with self.db.execute(f"UPDATE tag_relations SET tag_id = ? WHERE tag_id = ?", [new_name, name]):
            await self.db.commit()
        self.names["tags"].append(new_name)
        self.names["tags"].remove(name)

    async def transfer(self, name, new_owner: int):
        await self.exists(name, TagNotFound, should=True)
        name = await self.get_name(name)
        await self.update(name, "owner", new_owner)

    async def increment_views(self, name, tag: Tag = None):
        name = await self.get_name(name)
        if tag:
            current_views = tag.views
        else:
            current_views = (await self.get(name)).views
        await self.update(name, "views", (current_views + 1))

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
        # await self.exists(name_or_alias, TagNotFound, should=True)
        if name_or_alias in self.names["tags"]:
            return name_or_alias  # it's  a tag
        async with self.db.execute("SELECT tag_id FROM tag_relations WHERE alias = ?", [name_or_alias]) as cur:
            async for row in cur:  # it's an alias
                return row[0]

    async def add_alias(self, name, alias):
        name = await self.get_name(name)
        await self.exists(name, TagNotFound, should=True)
        aliases = (await self.get_aliases(name))
        if alias in aliases:
            raise AliasAlreadyExists
        elif len(aliases) > 10:
            raise AliasLimitReached
        self.names["aliases"].append(alias)
        await self.db.execute("INSERT INTO tag_relations (tag_id, alias) VALUES (?, ?)", [name, alias])
        await self.db.commit()

    async def remove_alias(self, name, alias):
        await self.exists(name, TagNotFound, should=True)
        name = await self.get_name(name)
        if alias not in (await self.get_aliases(name)):
            raise AliasNotFound
        await self.db.execute("DELETE FROM tag_relations WHERE tag_id = ? AND alias = ?", [name, alias])
        await self.db.commit()

    async def remove_aliases(self, name):
        await self.exists(name, TagNotFound, should=True)
        name = await self.get_name(name)
        await self.db.execute("DELETE FROM tag_relations WHERE tag_id = ?", [name])
        await self.db.commit()

    async def get_aliases(self, name: Optional = None) -> List[str] | TagNotFound:
        if not name:
            async with self.db.execute("SELECT * FROM tag_relations") as cur:
                content = await cur.fetchall()
                if content is None:
                    return []
                return [row[1] for row in content]
        await self.exists(name, TagNotFound, should=True)
        name = await self.get_name(name)
        async with self.db.execute("SELECT * FROM tag_relations WHERE tag_id = ?", [name]) as cur:
            content = await cur.fetchall()
            if content is None:
                return []
        return [alias for tag_id, alias in list(set(content))]
