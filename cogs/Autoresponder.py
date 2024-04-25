import disnake
import re

from disnake import TextInputStyle
from disnake.ext import commands
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from utils.bot import OGIROID
from utils.db_models import AutoResponseMessages
from utils.http import session
from utils.shortcuts import errorEmb, QuickEmb


# class AutoResponseMessages(Base):
#     __tablename__ = "auto_response_messages"
#     # needs to be list of strings and list of regex strings, channels, guild and response
#     id = Column(Integer, primary_key=True)
#     guild_id = Column(BigInteger)
#     channel_ids = Column(ARRAY(BigInteger))
#     regex_strings = Column(ARRAY(Text))
#     strings = Column(ARRAY(Text))
#     response = Column(Text)
#     case_sensitive = Column(Boolean)
#     enabled = Column(Boolean)
#     ephemeral = Column(Boolean)


class AutoResponder(commands.Cog, name="Autoresponder"):
    """Autoresponder commands"""

    def __init__(self, bot: OGIROID):
        self.bot = bot
        self.api_ninjas_key = self.bot.config.tokens.api_ninjas_key

    @commands.slash_command(description="Base autoresponder command")
    async def responder(self, inter):
        pass

    @responder.sub_command(
        description="Add a response. Defaults to all channels. Modal will pop up."
    )
    async def add(
        self,
        inter: disnake.ApplicationCommandInteraction,
        case_sensitive: bool = False,
        ephemeral: bool = False,
        channel1: disnake.TextChannel = None,
        channel2: disnake.TextChannel = None,
        channel3: disnake.TextChannel = None,
        channel4: disnake.TextChannel = None,
        channel5: disnake.TextChannel = None,
    ):
        channel_ids = [channel1, channel2, channel3, channel4, channel5]
        data = {
            "case_sensitive": case_sensitive,
            "ephemeral": ephemeral,
            "channel_ids": [ch.id for ch in channel_ids if ch],
        }
        await inter.response.send_modal(
            AutoResponderModal(bot=self.bot, other_data=data)
        )

    @responder.sub_command(description="Edit a response. Modal will pop up.")
    async def edit(self, inter: disnake.ApplicationCommandInteraction, id: int):
        async with self.bot.db.begin() as session:
            response = (
                session.query(AutoResponseMessages)
                .filter_by(id=id)
                .filter_by(guild_id=inter.guild.id)
                .first()
            )

        if not response:
            return await errorEmb(inter, "No response found with that ID")

        await inter.response.send_modal(
            AutoResponderModal(bot=self.bot, prefill_data=response)
        )

    @responder.sub_command(description="Delete a response")
    async def delete(self, inter: disnake.ApplicationCommandInteraction, id: int):
        await inter.response.defer()
        async with self.bot.db.begin() as session:
            session.query(AutoResponseMessages).filter_by(id=id).delete()
        await QuickEmb(inter, "Autoresponder deleted successfully").success()

    @responder.sub_command(description="List all responses")
    async def list(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        async with self.bot.db.begin() as session:
            responses = await session.execute(
                select(AutoResponseMessages).filter_by(guild_id=inter.guild.id)
            )

        if not responses:
            return await errorEmb(inter, "No responses found")

        response = ""
        for res in responses:
            response += f"ID: {res.id} | Response: {res.response} | Strings: {res.strings} | Regex Strings: {res.regex_strings}\n"

        await inter.send(response if response else "No responses found")

    @commands.Cog.listener(name="on_message")
    async def on_message(self, message):
        if message.author.bot:
            return

        if not (
            isinstance(message.channel, disnake.TextChannel)
            and message.channel.id == self.bot.config.channels.reddit_bot
        ) and not (
            isinstance(message.channel, disnake.Thread)
            and message.channel.parent_id == self.bot.config.channels.reddit_bot_forum
        ):
            return

        content = message.content

        if message.attachments:
            for attachment in message.attachments:
                if attachment.content_type.startswith("image"):
                    await message.add_reaction("👀")
                    image_data = await attachment.read()

                    api_url = "https://api.api-ninjas.com/v1/imagetotext"
                    async with await session.post(
                        api_url,
                        data={"image": image_data},
                        headers={"X-Api-Key": self.api_ninjas_key},
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            text = ""
                            for t in data:
                                text += t["text"] + " "

                            content += " " + text
                        else:
                            await message.channel.send(
                                f"Error occurred while processing the image. Try pasting the text instead. {response.status_code} {response.text}"
                            )

        content = content.lower()

        ###
        # Username not found
        # check if content contains "waiting for locator("[name=\"username\"]")"
        ###
        username_error_words = [
            ["waiting", "locator", "name", "username"],
            ["waiting", "locator", "name", "usernane"],
            ["waiting", "locator", "timeout", "exceeded"],
        ]

        def find_and_check(string, words_list):
            for words in words_list:
                # Create a regular expression pattern to match any of the words
                pattern = re.compile("|".join(words))

                # Search for matches in the string
                matches = pattern.findall(string)

                # Check if all words are found
                if all(word in matches for word in words):
                    return True

            return False

        if find_and_check(content, username_error_words):
            await message.reply(
                "Hey there! It seems like you're encountering an error related to `waiting for locator(\"[name=\\\"username\\\"]\")`. Don't worry, we've got you covered! 🛠️\n\nWe've identified a fix for this issue in a fork of the project. You can find the solution in the following repository: [RedditVideoMakerBot](<https://github.com/Cyteon/RedditVideoMakerBot/tree/master>)\n\nFeel free to use this fork to resolve the error. You can continue using your existing configuration from the 'old' repository without any changes."
            )
            return

        ###
        # Transparent Background
        ###
        # Patterns to match messages needing the transparent option
        transparent_patterns = [
            r".*(?:black|gray|grey|dark-?gray|dark-?grey|ugly).*background.*",
            r".*(?:black|gray|grey|dark-?gray|dark-?grey|ugly).*image.*",
            r".*(?:black|gray|grey|dark-?gray|dark-?grey|ugly).*block.*",
            r".*(?:black|gray|grey|dark-?gray|dark-?grey|ugly).*screen.*",
            r".*hide.*box.*",
            r".*remove.*box.*text.*",
            r".*massive?.*box.*behind.*text.*",
            r".*box.*behind.*text.*",
            r".*set.*captions.*transparent.*",
            r".*opaque.*background.*words.*",
            r".*image.*behind.*text.*",
            r".*dont.*want.*gray.*image.*",
        ]

        def needs_transparent_option(string):
            # Check if message matches any of the patterns
            for pattern in transparent_patterns:
                if re.match(pattern, string, re.IGNORECASE):
                    return True

            return False

        if needs_transparent_option(content):
            # write this message to people:
            await message.channel.send(
                "Hey there! If you're looking to remove the box around your text, simply follow these steps:\n\n"
                + "1. Navigate to the main folder of the project.\n"
                + "2. Locate the `config.toml` file.\n"
                + "3. Open the `config.toml` file with a text editor.\n"
                + "4. Find the setting named `theme`.\n"
                + "5. Change the value of `theme` to `transparent`.\n"
                + "6. Save the changes and restart the bot."
            )
            return

        ###
        # No attribute getsize FreeTypeFont
        ###
        fontsize_error_words = [
            ["freetypefont", "object", "no", "attribute", "getsize"]
        ]

        if find_and_check(content, fontsize_error_words):
            # write this message to people:
            await message.reply(
                """To error `AttributeError: 'FreeTypeFont' object has no attribute 'getsize'` happens due to Pillow removing the getsize function in the versions after 9.5.0.\nTo fix the problem use `pip install Pillow==9.5.0` in your project folder."""
            )
            return

        ###
        # Out of quota
        ###
        out_of_quota_error_words = [
            ["request", "exceeds", "quota", "characters", "remaining", "elevenlabs"],
        ]

        if find_and_check(content, out_of_quota_error_words):
            # write this message to people:
            await message.reply(
                """Hey there! It seems like you're encountering an error related to `request exceeds quota characters remaining elevenlabs`.\n\nThis error occurs when you've exceeded the maximum number of requests allowed by the API. To resolve this issue, you can either wait for the quota to reset or consider upgrading your plan to increase the number of requests you can make.\n\nA free alternative would be to replace your voice_choice in your config.toml file, change it from `"elevenlabs"` to `"streamlabspolly"`."""
            )
            return

        ###
        # Tiktok tts error
        ###
        tiktok_tts_error_words = [
            [
                "reason",
                "probably",
                "aid",
                "value",
                "correct",
                "load",
                "speech",
                "try",
                "again",
            ],
        ]

        if find_and_check(content, tiktok_tts_error_words):
            await message.reply(
                """Hey there! It seems like you're encountering an error related to `Reason: probably the aid value isn't correct, message: the Couldn't load speech. Try again.`.\n\nThis error occurs because the TikTok tts is currently broken. To resolve this issue, you can set the voice_choice in your `config.toml` file to `"streamlabspolly"`"""
            )
            return

        ###
        # ffmpeg not installed error
        ###
        ffmpeg_not_installed_error_words = [
            [
                "moviepy",
                "error",
                "ffmpeg",
                "encountered",
                "writing",
                "file",
                "unknown",
                "encoder",
                "not",
                "found",
            ],
        ]

        if find_and_check(content, ffmpeg_not_installed_error_words):
            # error is when ffmpeg is not install (correctly), the ffmpeg.exe file has to be in the main folder of the project
            await message.reply(
                """Hey there! It seems like you're encountering an error related to ffmpeg not being installed in your project. To resolve this issue, please make sure to download the ffmpeg.exe files and place them in the main folder of your project. Once done, try running your project again, and the error should be resolved. If you need further assistance, feel free to ask! 😊"""
            )
            return


class AutoResponderModal(disnake.ui.Modal):
    def __init__(
        self,
        bot: OGIROID,
        prefill_data: AutoResponseMessages = None,
        other_data: dict = None,
    ):
        # The details of the modal, and its components
        components = [
            disnake.ui.TextInput(
                label="Response",
                placeholder="Response",
                style=TextInputStyle.paragraph,
                custom_id="response",
                value=prefill_data.get("response", "") if prefill_data else "",
            ),
            disnake.ui.TextInput(
                label="Strings, separated by |||",
                placeholder="Strings(trigger)",
                style=TextInputStyle.paragraph,
                custom_id="strings",
                value=prefill_data.get("strings", "") if prefill_data else "",
            ),
            disnake.ui.TextInput(
                label="Regex Strings, separated by |||",
                placeholder="Regex Strings(trigger)",
                style=TextInputStyle.paragraph,
                custom_id="regex_strings",
                value=prefill_data.get("regex_strings", "") if prefill_data else "",
            ),
        ]
        self.bot = bot
        self.prefill_data = prefill_data
        self.other_data = other_data
        super().__init__(
            title="AutoResponder",
            custom_id="responder",
            components=components,
        )

    # The callback received when the user input is completed.
    async def callback(self, inter: disnake.ModalInteraction):
        try:
            await inter.response.defer()
            response = inter.text_values["response"].strip()
            strings = inter.text_values["strings"].strip()
            regex_strings = inter.text_values["regex_strings"].strip()
            strings = strings.split("|||")
            regex_strings = regex_strings.split("|||")

            #     add or edit
            async with self.bot.db.begin() as session:
                if self.prefill_data:
                    session.query(AutoResponseMessages).filter_by(
                        id=self.prefill_data["id"]
                    ).update(
                        {
                            "response": response,
                            "strings": strings,
                            "regex_strings": regex_strings,
                        }
                    )
                else:
                    session.add(
                        AutoResponseMessages(
                            response=response,
                            strings=strings,
                            regex_strings=regex_strings,
                            **self.other_data,
                        )
                    )

            return QuickEmb(inter, "Autoresponder added/edited successfully").success()

        except Exception as e:
            print(e)
            await errorEmb(inter, f"Error: {e}")


def setup(bot):
    bot.add_cog(AutoResponder(bot))
