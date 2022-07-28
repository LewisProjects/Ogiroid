from disnake import ui, ButtonStyle


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
        How long the Paginator should timeout in, after the last interaction.

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
            await inter.send('Unable to change the page.', ephemeral=True)

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
            await inter.send('Unable to change the page.', ephemeral=True)

    @ui.button(emoji="➡️", style=ButtonStyle.grey)
    async def next(self, button, inter):
        try:
            if inter.author.id != self.author and self.author != 123:
                return await inter.send("You cannot interact with these buttons.", ephemeral=True)
            elif self.CurrentEmbed == len(self.embeds) - 1:
                return await inter.send('you are already at the end', ephemeral=True)
            await inter.response.edit_message(embed=self.embeds[self.CurrentEmbed + 1])
            self.CurrentEmbed += 1

        except:
            await inter.send('Unable to change the page.', ephemeral=True)


    @ui.button(emoji="⏭️", style=ButtonStyle.grey)
    async def end(self, button, inter):
        try:
            if inter.author.id != self.author and self.author != 123:
                return await inter.send("You cannot interact with these buttons.", ephemeral=True)
            elif self.CurrentEmbed == len(self.embeds) - 1:
                return await inter.send('you are already at the end', ephemeral=True)
            await inter.response.edit_message(embed=self.embeds[len(self.embeds) - 1])
            self.CurrentEmbed = len(self.embeds) - 1

        except:
            await inter.send('Unable to change the page.', ephemeral=True)
