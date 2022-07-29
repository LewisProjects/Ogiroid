class TagException(BaseException):
    pass


class AliasException(TagException):
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


class CityNotFound(Exception):
    def __init__(self, city):
        super().__init__(f"City '{city}' not found!")


class InvalidAPIKEY(Exception):
    def __init__(self):
        super().__init__(f"You have an invalid API key!")
