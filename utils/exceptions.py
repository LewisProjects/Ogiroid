from disnake.ext.commands import CheckFailure


class BotException(BaseException):
    pass


class BlacklistException(BotException):
    pass


class TagException(BotException):
    pass


class AliasException(TagException):
    pass


class FlagQuizException(BotException):
    pass


class TagNotFound(TagException, KeyError):
    pass


class TagsNotFound(TagException):
    pass  # used when no tags are found i.e. when the user has no tags or when there are no tags in the database


class TagAlreadyExists(TagException):
    pass


class AliasAlreadyExists(AliasException):
    pass


class AliasNotFound(AliasException):
    pass


class FlagQuizUserNotFound(FlagQuizException):
    pass

class FlagQuizUsersNotFound(FlagQuizException):
    pass

class BlacklistNotFound(BlacklistException):
    pass


class UserBlacklisted(CheckFailure, BlacklistException):
    async def __call__(self, ctx):
        pass

    def __init__(self, *args, **kwargs):
        pass


class CityNotFound(BotException):
    def __init__(self, city):
        super().__init__(f"City '{city}' not found!")


class InvalidAPIKEY(BotException):
    def __init__(self):
        super().__init__(f"You have an invalid API key!")
