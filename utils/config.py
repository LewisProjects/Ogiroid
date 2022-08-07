from utils.CONSTANTS import *


@dataclass
class Config:
    Development = False  # if true will use base server ID's else will use development server ID's
    if Development:
        print("Using Development Config variable")
        channels = Channels.dev()
        roles = Roles.dev()
        colors = Colors
        colours = colors
        debug = True
    else:
        channels = Channels
        roles = Roles
        colors = Colors
        colours = colors
        debug = False
