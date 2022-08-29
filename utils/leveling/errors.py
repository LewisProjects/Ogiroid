class LevelingSystemError(Exception):
    """Base exception for :class:`LevelingSystem`"""

    def __init__(self, message: str):
        super().__init__(message)


class RoleAwardError(LevelingSystemError):
    """Base exception for :class:`RoleAward`"""

    def __init__(self, message: str):
        super().__init__(message)


class ConnectionFailure(LevelingSystemError):
    """Attempted to connect to the database file when the event loop is already running"""

    def __init__(self):
        super().__init__("Cannot connect to database file because the event loop is already running")


class NotConnected(LevelingSystemError):
    """Attempted to use a method that requires a connection to a database file"""

    def __init__(self):
        super().__init__(
            'You attempted to use a method that requires a database connection. Did you forget to connect to the database file first using "LevelingSystem.connect_to_database_file()"?'
        )


class DatabaseFileNotFound(LevelingSystemError):
    """The database file was not found"""

    def __init__(self, message):
        super().__init__(message)


class ImproperRoleAwardOrder(RoleAwardError):
    """When setting the awards :class:`dict` in the :class:`LevelingSystem` constructor, :attr:`RoleAward.level_requirement` was not greater than the last level"""

    def __init__(self, message):
        super().__init__(message)


class ImproperLeaderboard(LevelingSystemError):
    """Raised when the leaderboard table in the database file does not have the correct settings"""

    def __init__(self):
        super().__init__("It seems like the leaderboard table was altered. Components changed or deleted")


class LeaderboardNotFound(LevelingSystemError):
    """When accessing the "LevelingSystem.db" file, the table "leaderboard" was not found inside that file"""

    def __init__(self):
        super().__init__(
            'When accessing the "LevelingSystem.db" file, the table "leaderboard" was not found inside that file. Use LevelingSystem.create_database_file() to create the file'
        )


class FailSafe(LevelingSystemError):
    """Raised when the expected value for a method that can cause massive unwanted results, such as :meth:`LevelingSystem.wipe_database()`, was set to `False`"""

    def __init__(self):
        super().__init__('Failsafe condition raised due to default argument. "intentional" was set to False')
