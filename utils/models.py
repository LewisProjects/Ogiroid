from dataclasses import dataclass
import time


@dataclass
class Tag:
    name: str
    content: str
    owner: int
    created_at: int = time.time()
    views: int = 0

