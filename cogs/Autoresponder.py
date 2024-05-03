from typing import Union

import disnake
import re

from disnake import TextInputStyle
from disnake.ext import commands, tasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from utils.bot import OGIROID
from utils.db_models import AutoResponseMessages
from utils.http import session
from utils.shortcuts import errorEmb


class AutoResponder(commands.Cog, name="Autoresponder"):
    """Autoresponder commands"""

    def __init__(self, bot: OGIROID):
        self.bot = bot
        self.api_ninjas_key = self.bot.config.tokens.api_ninjas_key
        self.auto_responses = {}

    async def create_db_entry(
        self, inter: disnake.ModalInteraction, prefill_data=None, other_data=None
    ):
        if other_data is None:
            other_data = {}
        try:
            await inter.response.defer(ephemeral=True)
            response = inter.text_values["response"].strip()
            if inter.text_values["strings"]:
                strings = inter.text_values["strings"].strip().split("|||")
                strings = [string.strip() for string in strings if string.strip()]
            else:
                strings = []

            if inter.text_values["regex_strings"]:
                regex_strings = inter.text_values["regex_strings"].strip().split("|||")
                regex_strings = [
                    regex_string.strip()
                    for regex_string in regex_strings
                    if regex_string.strip()
                ]
            else:
                regex_strings = []

            #     add or edit
            async with self.bot.db.begin() as session:
                if prefill_data:
                    obj = await session.execute(
                        select(AutoResponseMessages).filter_by(id=prefill_data["id"])
                    )
                    obj = obj.scalars().first()
                    obj.response = response
                    obj.strings = strings
                    obj.regex_strings = regex_strings
                else:
                    obj = AutoResponseMessages(
                        response=response,
                        strings=strings,
                        regex_strings=regex_strings,
                        guild_id=inter.guild.id,
                        **other_data,
                    )
                session.add(obj)

            await inter.send("Autoresponder added/edited successfully", ephemeral=True)
            cached_responses = self.auto_responses.get(inter.guild.id, []).copy()
            cached_responses = list(filter(lambda x: x.id != obj.id, cached_responses))
            cached_responses.append(obj)
            self.auto_responses[inter.guild.id] = cached_responses
            return obj

        except Exception as e:
            print(e)
            await errorEmb(inter, f"Error: {e}")

    async def handle_perm(self, inter: disnake.ApplicationCommandInteraction):
        has_role = False
        for role in inter.author.roles:
            if role.id == self.bot.config.roles.reddit_bot_team:
                has_role = True
                break
        if not inter.author.guild_permissions.manage_messages and not has_role:
            await errorEmb(
                inter,
                "You need the `Manage Messages` permission to use this command",
                ephemeral=True,
            )
            return False
        return True

    @commands.Cog.listener()
    async def on_ready(self):
        await self.cache_auto_responses()
        print("[RESPONDER] Autoresponder ready")

    @commands.slash_command(description="Base autoresponder command")
    async def responder(self, inter):
        pass

    @commands.guild_only()
    @responder.sub_command(
        description="Add a response. Defaults to all channels. Modal will pop up."
    )
    async def add(
        self,
        inter: disnake.ApplicationCommandInteraction,
        channel1: Union[disnake.TextChannel, disnake.ForumChannel],
        case_sensitive: bool = False,
        channel2: Union[disnake.TextChannel, disnake.ForumChannel] = None,
        channel3: Union[disnake.TextChannel, disnake.ForumChannel] = None,
        channel4: Union[disnake.TextChannel, disnake.ForumChannel] = None,
        channel5: Union[disnake.TextChannel, disnake.ForumChannel] = None,
    ):
        if not await self.handle_perm(inter):
            return
        channel_ids = [channel1, channel2, channel3, channel4, channel5]
        data = {
            "case_sensitive": case_sensitive,
            "channel_ids": [ch.id for ch in channel_ids if ch],
        }
        await inter.response.send_modal(AutoResponderModal())
        modal_inter: disnake.ModalInteraction = await self.bot.wait_for(
            "modal_submit",
            check=lambda i: i.custom_id == "responder" and i.author == inter.author,
        )
        await self.create_db_entry(modal_inter, other_data=data)

    @commands.guild_only()
    @responder.sub_command(description="Edit a response. Modal will pop up.")
    async def edit(
        self,
        inter: disnake.ApplicationCommandInteraction,
        id: int = commands.Param(
            description="ID of the response to delete. Get id by: /responder list"
        ),
    ):
        if not await self.handle_perm(inter):
            return
        async with self.bot.db.begin() as session:
            response = await session.execute(
                select(AutoResponseMessages)
                .filter_by(id=id)
                .filter_by(guild_id=inter.guild.id)
            )
            response = response.scalars().first()

        if not response:
            return await errorEmb(
                inter, "No response found with that ID", ephemeral=True
            )

        await inter.response.send_modal(
            AutoResponderModal(
                prefill_data=response.__dict__,
            )
        )
        modal_inter: disnake.ModalInteraction = await self.bot.wait_for(
            "modal_submit",
            check=lambda i: i.custom_id == "responder" and i.author == inter.author,
        )
        await self.create_db_entry(modal_inter, prefill_data=response.__dict__)

    @commands.guild_only()
    @responder.sub_command(description="Delete a response")
    async def delete(
        self,
        inter: disnake.ApplicationCommandInteraction,
        id: int = commands.Param(
            description="ID of the response to delete. Get id by: /responder list"
        ),
    ):
        if not await self.handle_perm(inter):
            return
        await inter.response.defer(ephermeral=True)
        async with self.bot.db.begin() as session:
            response = await session.execute(
                select(AutoResponseMessages)
                .filter_by(id=id)
                .filter_by(guild_id=inter.guild.id)
            )
            response = response.scalars().first()

            if not response:
                return await errorEmb(
                    inter, "No response found with that ID", ephemeral=True
                )

            await session.delete(response)

        cached_responses = self.auto_responses.get(inter.guild.id, [])

        self.auto_responses[inter.guild.id] = list(
            filter(lambda x: x.id != id, cached_responses)
        )
        await inter.send("Autoresponder deleted successfully", ephemeral=True)

    @commands.guild_only()
    @responder.sub_command(description="List all responses")
    async def list(self, inter: disnake.ApplicationCommandInteraction):
        if not await self.handle_perm(inter):
            return
        await inter.response.defer(ephemeral=True)
        responses = self.auto_responses.get(inter.guild.id, [])

        response = ""
        for res in responses:
            response = f"ID: {res.id} | Enabled: {res.enabled} | Response: {res.response} | Strings: {res.strings} | Regex Strings: {res.regex_strings}\n"
            await inter.send(response, ephemeral=True)

        if not response:
            await inter.send("No responses found", ephemeral=True)

    @commands.guild_only()
    @responder.sub_command(description="Enable or disable a response")
    async def toggle(
        self,
        inter: disnake.ApplicationCommandInteraction,
        id: int = commands.Param(
            description="ID of the response to delete. Get id by: /responder list"
        ),
    ):
        if not await self.handle_perm(inter):
            return
        await inter.response.defer()
        async with self.bot.db.begin() as session:
            response = await session.execute(
                select(AutoResponseMessages)
                .filter_by(id=id)
                .filter_by(guild_id=inter.guild.id)
            )
            response = response.scalars().first()

            if not response:
                return await errorEmb(
                    inter, "No response found with that ID", ephemeral=True
                )

            response.enabled = not response.enabled

        cached_responses = self.auto_responses.get(inter.guild.id, [])
        cached_responses = list(filter(lambda x: x.id != id, cached_responses))

        if response.enabled:
            cached_responses.append(response)

        self.auto_responses[inter.guild.id] = cached_responses

        await inter.send(
            f"Autoresponder {response.id} toggled {'on' if response.enabled else 'off'} successfully",
            ephemeral=True,
        )

    @commands.Cog.listener(name="on_message")
    async def on_message(self, message: disnake.Message):
        if message.author.bot:
            return

        content = message.content

        if (
            message.attachments
            and (
                isinstance(message.channel, disnake.TextChannel)
                and message.channel.id == self.bot.config.channels.reddit_bot
            )
            or (
                isinstance(message.channel, disnake.Thread)
                and message.channel.parent_id
                == self.bot.config.channels.reddit_bot_forum
            )
        ):
            for attachment in message.attachments:
                if attachment.content_type.startswith("image"):
                    await message.add_reaction("👀")
                    image_data = await attachment.read()

                    api_url = "https://api.api-ninjas.com/v1/imagetotext"
                    async with await session.post(
                        api_url,
                        data={"image": image_data},
                        headers={"X-Api-Key": self.api_ninjas_key},
                    ) as trigger:
                        if trigger.status == 200:
                            data = await trigger.json()
                            text = ""
                            for t in data:
                                text += t["text"] + " "

                            content += " " + text
                        else:
                            await message.channel.send(
                                f"Error occurred while processing the image. Try pasting the text instead. {trigger.status_code} {trigger.text}"
                            )

        trigger_responses = self.auto_responses.get(message.guild.id, [])
        # filter by channel id, in case of forum and channel
        if isinstance(message.channel, disnake.Thread):
            trigger_responses = filter(
                lambda x: message.channel.parent_id in x.channel_ids, trigger_responses
            )
        else:
            trigger_responses = filter(
                lambda x: message.channel.id in x.channel_ids, trigger_responses
            )
        for trigger in trigger_responses:
            strings = trigger.strings
            regex_strings = trigger.regex_strings
            response_text = trigger.response

            if not trigger.case_sensitive:
                content = content.casefold()

                strings = [string.casefold() for string in strings]

            # Check if any of the strings are in the message
            if any(string in content for string in strings):
                if "<user.mention>" in response_text:
                    response_text = response_text.replace(
                        "<user.mention>", message.author.mention
                    )
                    await message.channel.send(response_text)
                else:
                    await message.reply(response_text)
                return

            # Check if any of the regex strings are in the message
            if any(
                re.search(
                    rf"{regex_string}",
                    content,
                    flags=re.IGNORECASE | re.MULTILINE
                    if not trigger.case_sensitive
                    else re.MULTILINE,
                )
                for regex_string in regex_strings
            ):
                if "<user.mention>" in response_text:
                    response_text = response_text.replace(
                        "<user.mention>", message.author.mention
                    )
                    await message.channel.send(response_text)
                else:
                    await message.reply(response_text)
                return

    async def cache_auto_responses(self):
        async with self.bot.db.begin() as session:
            responses = await session.execute(
                select(AutoResponseMessages).filter_by(enabled=True)
            )
            responses = responses.scalars().all()

        for response in responses:
            guild_responses = self.auto_responses.get(response.guild_id, [])
            guild_responses.append(response)
            self.auto_responses[response.guild_id] = guild_responses


class AutoResponderModal(disnake.ui.Modal):
    def __init__(
        self,
        prefill_data: AutoResponseMessages = None,
    ):
        # The details of the modal, and its components
        components = [
            disnake.ui.TextInput(
                label="Response",
                placeholder="Response, use <user.mention> to mention the user.",
                style=TextInputStyle.paragraph,
                custom_id="response",
                value=prefill_data.get("response", "") if prefill_data else "",
            ),
            disnake.ui.TextInput(
                label="Strings, separated by |||",
                placeholder="Strings(trigger), to use multiple strings, separate with |||",
                style=TextInputStyle.paragraph,
                custom_id="strings",
                value="|||".join(prefill_data.get("strings", ""))
                if prefill_data
                else "",
                required=False,
            ),
            disnake.ui.TextInput(
                label="Regex Strings, separated by |||",
                placeholder="Regex Strings(trigger), to use multiple regexes, separate with |||",
                style=TextInputStyle.paragraph,
                custom_id="regex_strings",
                value="|||".join(prefill_data.get("regex_strings", ""))
                if prefill_data
                else "",
                required=False,
            ),
        ]
        super().__init__(
            title="AutoResponder",
            custom_id="responder",
            components=components,
        )


def setup(bot):
    bot.add_cog(AutoResponder(bot))
