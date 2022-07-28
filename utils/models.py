from dataclasses import dataclass
import time


@dataclass
class Tag:
    name: str
    content: str
    owner: int
    created_at: int = time.time()
    views: int = 0

@dataclass
class FakeEmbed:
    title: str
    description: str
    color: int
    fields: list
    footer: str
    timestamp: int
