from __future__ import annotations

from dataclasses import dataclass
import time

"""careful moving the order of the below dataclasses as it will break the corresponding calls to them"""


@dataclass
class BlacklistedUser:
    id: int
    reason: str
    bot: bool
    tickets: bool
    tags: bool
    expires: int = 0  # 0 means never


@dataclass
class Tag:
    name: str
    content: str
    owner: int
    created_at: int = time.time()  # todo remove time.time()
    views: int = 0


@dataclass
class Alias:
    tag_id: str
    alias: str
