class TagException(BaseException):
    pass


class TagNotFound(TagException, KeyError):
    pass


class TagAlreadyExists(TagException):
    pass
