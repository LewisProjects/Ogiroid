import disnake
import re
from disnake.ext import commands
import requests

from utils.bot import OGIROID


class RedditBot(commands.Cog, name="Reddit Bot"):
    """All the Reddit Bot related commands!"""

    def __init__(self, bot: OGIROID):
        self.bot = bot

        self.api_ninjas_key = self.bot.config.tokens.api_ninjas_key

    # Get Information Related to the GitHub of the Bot
    @commands.slash_command(
        name="rbgithub",
        description="Get Information Related to the GitHub of the Reddit Bot",
    )
    @commands.guild_only()
    async def rbgithub(self, ctx):
        url = await self.bot.session.get(
            "https://api.github.com/repos/elebumm/RedditVideoMakerBot"
        )
        json = await url.json()
        if url.status == 200:
            # Creat an embed with the information: Name, Description, URL, Stars, Gazers, Forks, Last Updated
            embed = disnake.Embed(
                title=f"{json['name']} information",
                description=f"{json['description']}",
                color=0xFFFFFF,
            )
            embed.set_thumbnail(url=f"{json['owner']['avatar_url']}")
            embed.add_field(
                name="GitHub Link: ",
                value=f"**[Link to the Reddit Bot]({json['html_url']})**",
                inline=True,
            )
            embed.add_field(
                name="Stars <:starr:990647250847940668>: ",
                value=f"{json['stargazers_count']}",
                inline=True,
            )
            embed.add_field(
                name="Gazers <:gheye:990645707427950593>: ",
                value=f"{json['subscribers_count']}",
                inline=True,
            )
            embed.add_field(
                name="Forks <:fork:990644980773187584>: ",
                value=f"{json['forks_count']}",
                inline=True,
            )
            embed.add_field(
                name="Open Issues <:issue:990645996918808636>: ",
                value=f"{json['open_issues_count']}",
                inline=True,
            )
            embed.add_field(
                name="License <:license:990646337118818404>: ",
                value=f"{json['license']['spdx_id']}",
                inline=True,
            )
            embed.add_field(
                name="Clone Command <:clone:990646924640153640>: ",
                value=f"```git clone {json['clone_url']}```",
                inline=False,
            )
            await ctx.send(embed=embed)

    @commands.Cog.listener(name="on_message")
    async def on_message(self, message):
        if message.author.bot:
            return

        if not (isinstance(message.channel, disnake.TextChannel) and message.channel.id == self.bot.config.channels.reddit_bot) and not (isinstance(message.channel, disnake.Thread) and message.channel.parent_id == self.bot.config.channels.reddit_bot_forum):
            return

        content = message.content

        if message.attachments:
            for attachment in message.attachments:
                if attachment.content_type.startswith("image"):
                    await message.add_reaction("👀")
                    image_data = await attachment.read()

                    api_url = 'https://api.api-ninjas.com/v1/imagetotext'
                    async with await self.bot.session.post(
                        api_url,
                        json={"file": image_data},
                        headers={'X-Api-Key': self.api_ninjas_key}
                    ) as resp:
                        image_data = await resp.read()
                        print(image_data)

                    # print(response.status)
                    # print(await response.text())
                    # if response.status == 200:
                    #     print(response)
                    #     data = await response.json()
                    #     print(data)
                    #     text = data.get("text")
                    #     print(text)
                    #     if text:
                    #         print(text)
                    #         await message.reply(f"Here is the text extracted from the image: {text}")

        content = content.lower()

        ###
        # Username not found
        # check if content contains "waiting for locator("[name=\"username\"]")"
        ###
        username_error_words = [
            ["waiting", "locator", "name", "username"],
            ["waiting", "locator", "name", "usernane"],
            ["waiting", "locator", "timeout", "exceeded"]
        ]

        def find_and_check(string, words_list):
            for words in words_list:
                # Create a regular expression pattern to match any of the words
                pattern = re.compile('|'.join(words))

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
                "Hey there! If you're looking to remove the box around your text, simply follow these steps:\n\n" +
                "1. Navigate to the main folder of the project.\n" +
                "2. Locate the `config.toml` file.\n" +
                "3. Open the `config.toml` file with a text editor.\n" +
                "4. Find the setting named `theme`.\n" +
                "5. Change the value of `theme` to `transparent`.\n" +
                "6. Save the changes and restart the bot."
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
            ["reason", "probably", "aid", "value", "correct", "load", "speech", "try", "again"],
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
            ["moviepy", "error", "ffmpeg", "encountered", "writing", "file", "unknown", "encoder", "not", "found"],
        ]

        if find_and_check(content, ffmpeg_not_installed_error_words):
            # error is when ffmpeg is not install (correctly), the ffmpeg.exe file has to be in the main folder of the project
            await message.reply(
                """Hey there! It seems like you're encountering an error related to ffmpeg not being installed in your project. To resolve this issue, please make sure to download the ffmpeg.exe files and place them in the main folder of your project. Once done, try running your project again, and the error should be resolved. If you need further assistance, feel free to ask! 😊"""
            )
            return

def setup(bot):
    bot.add_cog(RedditBot(bot))
