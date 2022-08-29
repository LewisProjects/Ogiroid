from collections.abc import Sequence
from typing import ClassVar, Optional, Union

from disnake import AllowedMentions, Embed, Member as DMember

from .errors import LevelingSystemError

default_message = "[$mention], you are now **level [$level]!**"
default_mentions = AllowedMentions(everyone=False, users=True, roles=False, replied_user=False)


class AnnouncementMemberGuild:
    """Helper class for AnnouncementMember"""

    icon_url: ClassVar[str] = "[$g_icon_url]"
    id: ClassVar[str] = "[$g_id]"
    name: ClassVar[str] = "[$g_name]"


class AnnouncementMember:
    """Helper class for LevelUpAnnouncement"""

    avatar_url: ClassVar[str] = "[$avatar_url]"
    banner_url: ClassVar[str] = "[$banner_url]"
    created_at: ClassVar[str] = "[$created_at]"
    default_avatar_url: ClassVar[str] = "[$default_avatar_url]"
    discriminator: ClassVar[str] = "[$discriminator]"
    display_avatar_url: ClassVar[str] = "[$display_avatar_url]"  # Guild avatar if they have one set
    display_name: ClassVar[str] = "[$display_name]"
    id: ClassVar[str] = "[$id]"
    joined_at: ClassVar[str] = "[$joined_at]"
    mention: ClassVar[str] = "[$mention]"
    name: ClassVar[str] = "[$name]"
    nick: ClassVar[str] = "[$nick]"

    Guild: ClassVar[AnnouncementMemberGuild] = AnnouncementMemberGuild()


class LevelUpAnnouncement:
    """A helper class for setting up messages that are sent when someone levels up"""

    TOTAL_XP: ClassVar[str] = "[$total_xp]"
    LEVEL: ClassVar[str] = "[$level]"
    RANK: ClassVar[str] = "[$rank]"
    Member: ClassVar[AnnouncementMember] = AnnouncementMember()

    def __init__(
        self,
        message: Union[str, Embed] = default_message,
        level_up_channel_ids: Optional[Sequence[int]] = None,
        allowed_mentions: AllowedMentions = default_mentions,
        tts: bool = False,
        delete_after: Optional[float] = None,
    ):
        self.message = message
        self.level_up_channel_ids = level_up_channel_ids
        self._total_xp: Optional[int] = None
        self._level: Optional[int] = None
        self._rank: Optional[int] = None
        self._send_kwargs = {"allowed_mentions": allowed_mentions, "tts": tts, "delete_after": delete_after}

    def _convert_markdown(self, to_convert: str) -> str:
        """Convert the markdown text to the value it represents

        .. added:: v0.0.2
        """
        markdowns = {
            LevelUpAnnouncement.TOTAL_XP: self._total_xp,
            LevelUpAnnouncement.LEVEL: self._level,
            LevelUpAnnouncement.RANK: self._rank,
        }
        for mrkd, value in markdowns.items():
            to_convert = to_convert.replace(mrkd, str(value))
        return to_convert

    def _convert_member_markdown(self, to_convert: str, message_author: DMember) -> str:
        """Convert the member markdown text to the value it represents

        .. added:: v0.0.2
        .. changes::
            v1.1.0
                Updated `disnake.Member.avatar_url` -> `disnake.Member.avatar.url`
                Updated `disnake.Guild.icon_url` -> `disnake.Guild.icon.url`
                Added `disnake.Member.display_avatar.url`
                Added `disnake.Member.banner.url`
        """
        DEFAULT_URL = message_author.default_avatar.url
        markdowns = {
            # member
            AnnouncementMember.avatar_url: message_author.avatar.url if message_author.avatar is not None else DEFAULT_URL,
            AnnouncementMember.banner_url: message_author.banner.url if message_author.banner is not None else DEFAULT_URL,
            AnnouncementMember.created_at: message_author.created_at,
            AnnouncementMember.default_avatar_url: DEFAULT_URL,
            AnnouncementMember.discriminator: message_author.discriminator,
            AnnouncementMember.display_avatar_url: message_author.display_avatar.url,
            AnnouncementMember.display_name: message_author.display_name,
            AnnouncementMember.id: message_author.id,
            AnnouncementMember.joined_at: message_author.joined_at,
            AnnouncementMember.mention: message_author.mention,
            AnnouncementMember.name: message_author.name,
            AnnouncementMember.nick: message_author.nick,
            # guild
            AnnouncementMember.Guild.icon_url: message_author.guild.icon.url
            if message_author.guild.icon is not None
            else DEFAULT_URL,
            AnnouncementMember.Guild.id: message_author.guild.id,
            AnnouncementMember.Guild.name: message_author.guild.name,
        }
        for mrkd, value in markdowns.items():
            to_convert = to_convert.replace(mrkd, str(value))
        return to_convert

    def _parse_message(self, message: Union[str, Embed], message_author: DMember) -> Union[str, Embed]:
        """
        .. changes::
            v0.0.2
                Added handling for embed announcements
                Added handling for LevelUpAnnouncement.Member markdowns
                Moved markdown conversion to its own method (`_convert_markdown`)
        """
        if isinstance(message, str):
            partial = self._convert_markdown(message)
            full = self._convert_member_markdown(partial, message_author)
            return full

        elif isinstance(message, Embed):
            embed = message
            new_dict_embed = {}
            temp_formatted = []

            def e_dict_to_converted(embed_value: dict) -> dict:
                """If the value from the :class:`disnake.Embed` dictionary contains a :class:`LevelUpAnnouncement` markdown, convert the markdown to it's
                associated value and return it for use

                    .. added:: v0.0.2
                """
                temp_dict = {}
                for key, value in embed_value.items():
                    if not isinstance(value, str):
                        temp_dict[key] = value
                    else:
                        partial = self._convert_markdown(value)
                        full = self._convert_member_markdown(partial, message_author)
                        temp_dict[key] = full
                else:
                    return temp_dict.copy()

            for embed_key, embed_value in embed.to_dict().items():
                # description, title, etc...
                if isinstance(embed_value, str):
                    partial = self._convert_markdown(embed_value)
                    full = self._convert_member_markdown(partial, message_author)
                    new_dict_embed[embed_key] = full

                # field inline values or disnake.Color
                elif isinstance(embed_value, (int, bool)):
                    new_dict_embed[embed_key] = embed_value

                # footer, author, etc...
                elif isinstance(embed_value, dict):
                    new_dict_embed[embed_key] = e_dict_to_converted(embed_value)

                # fields
                elif isinstance(embed_value, list):
                    for item in embed_value:  # "item" is a dict
                        temp_formatted.append(e_dict_to_converted(item))
                    new_dict_embed[embed_key] = temp_formatted.copy()
                    temp_formatted.clear()

            return Embed.from_dict(new_dict_embed)

        else:
            raise LevelingSystemError(
                f'Level up announcement parameter "message" expected a str or disnake.Embed, got {message.__class__.__name__}'
            )
