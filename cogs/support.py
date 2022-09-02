import disnake
from disnake import TextInputStyle, Option
from disnake.ext import commands

from utils.bot import OGIROID


class BugModal(disnake.ui.Modal):
    def __init__(self, bot: OGIROID, bug_report_type: str):
        # The details of the modal, and its components
        self.bot = bot
        self.bug_report_type = bug_report_type
        components = [
            # disnake.ui.Select(
            #     placeholder="Bug Report for:",
            #     options=["Reddit-Bot", "Ogiroid"],
            #     custom_id="type",
            # ),
            disnake.ui.TextInput(
                label="Bug Title",
                placeholder="Title",
                custom_id="title",
                style=TextInputStyle.short,
                max_length=50,
            ),
            disnake.ui.TextInput(
                label="Expected Result",
                placeholder="Your expected result",
                custom_id="expected",
                style=TextInputStyle.paragraph,
                max_length=500,
            ),
            disnake.ui.TextInput(
                label="Actual Result",
                placeholder="Your actual result",
                custom_id="actual",
                style=TextInputStyle.paragraph,
                max_length=500,
            ),
            disnake.ui.TextInput(
                label="Further Explanation",
                placeholder="",
                custom_id="description",
                style=TextInputStyle.paragraph,
                required=False,
            ),
        ]
        super().__init__(
            title="Report Bug",
            custom_id="bug",
            components=components,
        )

    # The callback received when the user input is completed.
    async def callback(self, inter: disnake.ModalInteraction):
        bug_report_type = self.bug_report_type  # inter.data["components"][0]["components"][0]["values"][0]
        embed = disnake.Embed(title="Bug Report")
        embed.add_field(name="From:", value=inter.author)

        embed.add_field(name="Type:", value=bug_report_type)

        embed.add_field(name="Bug Title:", value=inter.text_values["title"], inline=False)

        embed.add_field(name="Expected Result: ", value=inter.text_values["expected"], inline=False)

        embed.add_field(name="Actual Result:", value=inter.text_values["actual"], inline=False)

        embed.add_field(
            name="Further Explanation:",
            value=inter.text_values["description"] if inter.text_values["description"] else "No explanation provided",
            inline=False,
        )

        if bug_report_type == "Reddit-Bot":
            channel = self.bot.get_channel(self.bot.config.channels.bug_report_reddit_bot)
        else:
            channel = self.bot.get_channel(self.bot.config.channels.bug_report_ogiroid)

        await channel.send(embed=embed)
        await inter.send("Sent bug report.\nThank you for pointing it out.", ephemeral=True)


class SuggestionModal(disnake.ui.Modal):
    def __init__(self, bot: OGIROID, suggestion_type: str):
        # The details of the modal, and its components
        self.bot = bot
        self.suggestion_type = suggestion_type
        components = [
            # disnake.ui.Select(
            #     placeholder="Suggestion for:",
            #     options=["Reddit-Bot", "Ogiroid"],
            #     custom_id="type",
            # ),
            disnake.ui.TextInput(
                label="Suggestion Title",
                placeholder="Title",
                custom_id="title",
                style=TextInputStyle.short,
                max_length=50,
            ),
            disnake.ui.TextInput(
                label="Description",
                placeholder="Describe your suggestion here",
                custom_id="description",
                style=TextInputStyle.paragraph,
            ),
        ]
        super().__init__(
            title="Suggestion",
            custom_id="suggest",
            components=components,
        )

    # The callback received when the user input is completed.
    async def callback(self, inter: disnake.ModalInteraction):
        suggestion_type = self.suggestion_type  # inter.data["components"][0]["components"][0]["values"][0]
        embed = disnake.Embed(title="Suggestion")
        embed.add_field(name="From:", value=inter.author)

        embed.add_field(name="Type:", value=suggestion_type)

        embed.add_field(name="Title:", value=inter.text_values["title"], inline=False)

        embed.add_field(name="Description:", value=inter.text_values["description"], inline=False)

        if suggestion_type == "Reddit-Bot":
            channel = self.bot.get_channel(self.bot.config.channels.suggestion_reddit_bot)
        else:
            channel = self.bot.get_channel(self.bot.config.channels.suggestion_ogiroid)
        await channel.send(embed=embed)
        await inter.response.send_message("Sent suggestion.\nThank you for your suggestion.", ephemeral=True)


class BotSupport(commands.Cog, name="Bot Support"):
    """Bot Support used for reporting bugs and suggesting features"""

    def __init__(self, bot: OGIROID):
        self.bot = bot

    @commands.slash_command(
        name="reportbug",
        description="Report a bug",
        options=[
            Option(
                name="for",
                required=True,
                description="Select for what this bug report is.",
                choices=["Reddit-Bot", "Ogiroid"],
            )
        ],
        connectors={"for": "bug_report_for"},
    )
    async def bug(self, inter: ApplicationCommandInteraction, bug_report_for: str):
        await inter.response.send_modal(modal=BugModal(self.bot, bug_report_for))

    @commands.slash_command(
        name="suggest",
        description="Suggest something for the bot",
        options=[
            Option(
                name="for",
                required=True,
                description="Select for what this suggestion is.",
                choices=["Reddit-Bot", "Ogiroid"],
            )
        ],
        connectors={"for": "suggestion_for"},
    )
    async def suggestion(self, inter, suggestion_for: str):
        await inter.response.send_modal(modal=SuggestionModal(self.bot, suggestion_for))


def setup(bot):
    bot.add_cog(BotSupport(bot))
