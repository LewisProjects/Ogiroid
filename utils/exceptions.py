class TagException(BaseException):
    pass


class TagNotFound(TagException, KeyError):
    pass


class TagsNotFound(TagException):
    pass  # used when no tags are found i.e when the user has no tags or when there are no tags in the database


class TagAlreadyExists(TagException):
    pass


class TicketException(BaseException):
    pass


class TicketNotFound(TicketException, KeyError):
    pass


class TicketsNotFound(TicketException):
    pass  # used when no tickets are found i.e when the user has no tickets or when there are no tickets in the database


class TicketAlreadyExists(TicketException):
    pass
