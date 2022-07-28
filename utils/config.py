from dataclasses import dataclass

from utils.CONSTANTS import Channels


@dataclass
class Config:
    channels = Channels
    debug = True  # todo change
