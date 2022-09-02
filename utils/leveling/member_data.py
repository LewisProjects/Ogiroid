from typing import Dict, Optional, Union


class MemberData:
    """Represents a members record from the database converted to an object where each value from their record can be easily accessed. Used in coordination with :class:`LevelingSystem`

    Attributes
    ----------
    id_number: :class:`int`
        The members ID

    name: :class:`str`
        The members name

    level: :class:`int`
        The members level

    xp: :class:`int`
        The members xp

    total_exp: :class:`int`
        The members total xp

    rank: Optional[:class:`int`]
        The members rank. Can be `None` if the member is not ranked yet

    mention: :class:`str`
        The disnake member mention string
    """

    __slots__ = ("id_number", "name", "level", "xp", "total_exp", "rank", "mention")

    def __init__(self, id_number: int, name: str, level: int, xp: int, total_exp: int, rank: Optional[int]):
        self.id_number = id_number
        self.name = name
        self.level = level
        self.xp = xp
        self.total_exp = total_exp
        self.rank = rank
        self.mention = f"<@{id_number}>"

    def __repr__(self):
        return f"<MemberData id_number={self.id_number} name={self.name!r} level={self.level} xp={self.xp} total_exp={self.total_exp} rank={self.rank}>"

    def to_dict(self) -> Dict[str, Union[int, str]]:
        """Return the :class:`dict` representation of the :class:`MemberData` object

        Returns
        -------
        Dict[:class:`str`, Union[:class:`int`, :class:`str`]]

            .. added:: v1.0.1
        """
        return {key: getattr(self, key) for key in self.__class__.__slots__}
