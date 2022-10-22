from typing import TYPE_CHECKING

from disnake import ui, ButtonStyle, Embed

from utils.exceptions import UserNotFound
from utils.shortcuts import errorEmb
import datetime as dt
if TYPE_CHECKING:
    from cogs.Levels import LevelsController

class CreatePaginator(ui.View):
    """
    Paginator for Embeds.
    Parameters:
    ----------
    embeds: List[Embed]
        List of embeds which are in the Paginator. Paginator starts from first embed.
    author: int
        The ID of the author who can interact with the buttons. Anyone can interact with the Paginator Buttons if not specified.
    timeout: float
        How long the Paginator should time out in, after the last interaction.

    """

    def __init__(self, embeds: list, author: int = 123, timeout: float = None):
        self.embeds = embeds
        self.author = author
        self.CurrentEmbed = 0
        super().__init__(timeout=timeout if timeout else 180)

    @ui.button(emoji="⏮️", style=ButtonStyle.grey)
    async def front(self, button, inter):
        try:
            if inter.author.id != self.author and self.author != 123:
                return await inter.send("You cannot interact with these buttons.", ephemeral=True)
            elif self.CurrentEmbed == 0:
                return await inter.send("You are already on the first page.", ephemeral=True)
            elif self.CurrentEmbed:
                await inter.response.edit_message(embed=self.embeds[0])
                self.CurrentEmbed = 0
            else:
                raise ()

        except:
            await inter.send("Unable to change the page.", ephemeral=True)

    @ui.button(emoji="⬅️", style=ButtonStyle.grey)
    async def previous(self, button, inter):
        try:
            if inter.author.id != self.author and self.author != 123:
                return await inter.send("You cannot interact with these buttons.", ephemeral=True)
            elif self.CurrentEmbed == 0:
                return await inter.send("You are already on the first page.", ephemeral=True)
            if self.CurrentEmbed:
                await inter.response.edit_message(embed=self.embeds[self.CurrentEmbed - 1])
                self.CurrentEmbed = self.CurrentEmbed - 1
            else:
                raise ()

        except:
            await inter.send("Unable to change the page.", ephemeral=True)

    @ui.button(emoji="➡️", style=ButtonStyle.grey)
    async def next(self, button, inter):
        try:
            if inter.author.id != self.author and self.author != 123:
                return await inter.send("You cannot interact with these buttons.", ephemeral=True)
            elif self.CurrentEmbed == len(self.embeds) - 1:
                return await inter.send("you are already at the end", ephemeral=True)
            await inter.response.edit_message(embed=self.embeds[self.CurrentEmbed + 1])
            self.CurrentEmbed += 1

        except:
            await inter.send("Unable to change the page.", ephemeral=True)

    @ui.button(emoji="⏭️", style=ButtonStyle.grey)
    async def end(self, button, inter):
        try:
            if inter.author.id != self.author and self.author != 123:
                return await inter.send("You cannot interact with these buttons.", ephemeral=True)
            elif self.CurrentEmbed == len(self.embeds) - 1:
                return await inter.send("you are already at the end", ephemeral=True)
            await inter.response.edit_message(embed=self.embeds[len(self.embeds) - 1])
            self.CurrentEmbed = len(self.embeds) - 1

        except:
            await inter.send("Unable to change the page.", ephemeral=True)


class LeaderboardView(ui.View):
    """
    Paginator for Leaderboards.
    Parameters:
    ----------
    author: int
        The ID of the author who can interact with the buttons. Anyone can interact with the Paginator Buttons if not specified.
    UserPicked: bool
        If True, the user has already been shown and no need to add an extra field
    """
    def __init__(self, controller: "LevelsController", firstemb: Embed, author: int = 123, set_user: bool = False, timeout: float = None):

        self.controller = controller
        self.author = author
        self.CurrentEmbed = 0
        self.firstemb = firstemb
        self.user_set = set_user
        super().__init__(timeout=timeout if timeout else 180,)

    async def at_last_page(self, inter):
        records = await self.controller.get_count(inter.guild.id)
        if records % 10 <= 0:
            return True
        else:
            return False



    async def create_page(self, inter, page_num) -> Embed:
        if page_num == 0:
            return self.firstemb
        else:
            records = await self.controller.get_leaderboard(inter.guild, limit=10, offset=page_num*10)
            try:
                cmd_user = await self.controller.get_user(inter.author)
            except UserNotFound:
                cmd_user = None

            if not records:
                return await errorEmb(inter, text="No records found!")
            embed = Embed(title="Leaderboard", color=0x00FF00)

            for i, record in enumerate(records):
                user = await inter.bot.fetch_user(record.user_id)
                if record.user_id == inter.author.id:
                    embed.add_field(name=f"{i + 1}. {user} ~ You ",
                                    value=f"Level: {record.lvl}\nTotal XP: {record.total_exp:,}", inline=False)
                    self.user_set = True
                else:
                    embed.add_field(name=f"{i + 1}. {user}",
                                    value=f"Level: {record.lvl}\nTotal XP: {record.total_exp:,}",
                                    inline=False)
            if not self.user_set:
                rank = await self.controller.get_rank(inter.guild.id, cmd_user)
                embed.add_field(
                    name=f"{rank}. You",
                    value=f"Level: {cmd_user.lvl}\nTotal XP: {cmd_user.xp:,}",
                    inline=False,
                )

            embed.set_footer(text=f"{inter.author}", icon_url=inter.author.avatar.url)
            embed.timestamp = dt.datetime.now()

    @ui.button(emoji="⏮️", style=ButtonStyle.grey)
    async def front(self, button, inter):
        try:
            if inter.author.id != self.author and self.author != 123:
                return await inter.send("You cannot interact with these buttons.", ephemeral=True)
            elif self.CurrentEmbed == 0:
                return await inter.send("You are already on the first page.", ephemeral=True)
            elif self.CurrentEmbed:
                await inter.response.edit_message(embed=await self.create_page(inter, 0))
                self.CurrentEmbed = 0
            else:
                raise ()
        except:
            await inter.send("Unable to change the page.", ephemeral=True)

    @ui.button(emoji="⬅️", style=ButtonStyle.grey)
    async def previous(self, button, inter):
        try:
            if inter.author.id != self.author and self.author != 123:
                return await inter.send("You cannot interact with these buttons.", ephemeral=True)
            elif self.CurrentEmbed == 0:
                return await inter.send("You are already on the first page.", ephemeral=True)
            if self.CurrentEmbed:
                await inter.response.edit_message(embed=await self.create_page(inter, self.CurrentEmbed - 1))
                self.CurrentEmbed = self.CurrentEmbed - 1
            else:
                raise ()

        except:
            await inter.send("Unable to change the page.", ephemeral=True)

    @ui.button(emoji="➡️", style=ButtonStyle.grey)
    async def next(self, button, inter):
        try:
            if inter.author.id != self.author and self.author != 123:
                return await inter.send("You cannot interact with these buttons.", ephemeral=True)
            elif await self.at_last_page(inter):
                return await inter.send("you are already at the end", ephemeral=True)
            await inter.response.edit_message(embed=await self.create_page(inter, self.CurrentEmbed + 1))
            self.CurrentEmbed += 1

        except:
            await inter.send("Unable to change the page.", ephemeral=True)

    @ui.button(emoji="⏭️", style=ButtonStyle.grey)
    async def end(self, button, inter):
        try:
            if inter.author.id != self.author and self.author != 123:
                return await inter.send("You cannot interact with these buttons.", ephemeral=True)
            elif await self.at_last_page(inter):
                return await inter.send("you are already at the end", ephemeral=True)
            get_last_page = await self.controller.get_count(inter.guild.id)
            if get_last_page % 10 == 0:
                last_page = get_last_page // 10
            else:
                last_page = get_last_page // 10 + 1
            await inter.response.edit_message(embed=await self.create_page(inter, last_page))
            self.CurrentEmbed = last_page

        except:
            await inter.send("Unable to change the page.", ephemeral=True)
