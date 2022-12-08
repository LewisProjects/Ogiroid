import asyncio
import os
import random
import time
from datetime import datetime, timezone

import akinator as ak
import disnake
import requests
from discord_together import DiscordTogether
from disnake import Embed, ApplicationCommandInteraction, Member
from disnake.ext import commands
from disnake.utils import utcnow
from dotenv import load_dotenv

from utils.CONSTANTS import morse
from utils.assorted import renderBar
from utils.bot import OGIROID
from utils.http import HTTPSession
from utils.shortcuts import errorEmb

load_dotenv("../secrets.env")


class Fun(commands.Cog):
    """Fun Commands!"""

    def __init__(self, bot: OGIROID):
        self.togetherControl = None
        self.bot = bot
        self.morse = morse

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.bot.ready_:
            TOKEN = os.getenv("TOKEN")
            # noinspection PyUnresolvedReferences
            self.togetherControl = await DiscordTogether(TOKEN)

    @commands.slash_command(
        name="spotify", description="Show what song a member listening to in Spotify"
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.guild_only()
    async def spotifyinfo(self, inter: ApplicationCommandInteraction, user: Member):
        user = user or inter.author

        spotify: disnake.Spotify = disnake.utils.find(
            lambda s: isinstance(s, disnake.Spotify), user.activities
        )
        if not spotify:
            return await errorEmb(inter, f"{user} is not listening to Spotify!")

        e = (
            Embed(
                title=spotify.title,
                colour=spotify.colour,
                url=f"https://open.spotify.com/track/{spotify.track_id}",
            )
            .set_author(name="Spotify", icon_url="https://i.imgur.com/PA3vvdN.png")
            .set_thumbnail(url=spotify.album_cover_url)
        )

        # duration
        cur, dur = (
            utcnow() - spotify.start.replace(tzinfo=timezone.utc),
            spotify.duration,
        )

        # Bar stuff
        barLength = 5 if user.is_on_mobile() else 17
        bar = renderBar(
            int((cur.seconds / dur.seconds) * 100),
            fill="─",
            empty="─",
            point="⬤",
            length=barLength,
        )

        e.add_field(name="Artist", value=", ".join(spotify.artists))

        e.add_field(name="Album", value=spotify.album)

        e.add_field(
            name="Duration",
            value=(
                f"{cur.seconds // 60:02}:{cur.seconds % 60:02}"
                + f" {bar} "
                + f"{dur.seconds // 60:02}:"
                + f"{dur.seconds % 60:02}"
            ),
            inline=False,
        )
        await inter.send(embed=e)

    @commands.slash_command(
        name="poll",
        description="Make a Poll enter a question atleast 2 options and upto 6 options.",
    )
    @commands.cooldown(1, 90, commands.BucketType.user)
    @commands.cooldown(1, 30, commands.BucketType.channel)
    async def poll(
        self,
        inter: ApplicationCommandInteraction,
        question,
        choice1,
        choice2,
        choice3=None,
        choice4=None,
        choice5=None,
        choice6=None,
    ):
        """
        Makes a poll quickly.
        """
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣"]
        choices = [choice1, choice2, choice3, choice4, choice5, choice6]
        choices = [choice for choice in choices if choice is not None]
        choices_str = ""
        emojis = emojis[
            : len(choices)
        ]  # trims emojis list to length of inputted choices
        i = 0
        for emoji in emojis:
            choices_str += f"{emoji}  {choices[i]}\n\n"
            i += 1

        embed = disnake.Embed(title=question, description=choices_str, colour=0xFFFFFF)

        if inter.author:
            embed.set_footer(text=f"Poll by {inter.author}")
        embed.timestamp = datetime.now()

        await inter.response.send_message(embed=embed)
        poll = await inter.original_message()  # Gets the message which got sent
        for emoji in emojis:
            await poll.add_reaction(emoji)

    @commands.slash_command(
        name="youtube", description="Watch YouTube in a Discord VC with your friends"
    )
    async def youtube(self, inter):
        """Watch YouTube in a Discord VC with your friends"""
        if inter.author.voice:
            chan = inter.author.voice.channel.id
            link = await self.togetherControl.create_link(chan, "youtube")
            embed = disnake.Embed(
                title="YouTube",
                description=f"Click __[here]({link})__ to start the YouTube together session.",
                color=0xFF0000,
                timestamp=datetime.now(),
            )
            embed.set_footer(
                text=f"Command issued by: {inter.author.name}",
                icon_url=inter.author.display_avatar,
            )
            await inter.send(embed=embed)
        else:
            e = await inter.send(
                "**You must be in a voice channel to use this command!**"
            )
            time.sleep(5)
            await e.delete()

    @commands.slash_command()
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def joke(self, inter: ApplicationCommandInteraction):
        """Get a random joke!"""
        response = await self.bot.session.get("https://some-random-api.ml/joke")
        data = await response.json()
        embed = disnake.Embed(title="Joke!", description=data["joke"], color=0xFFFFFF)
        embed.set_footer(
            text=f"Command issued by: {inter.author.name}",
            icon_url=inter.author.display_avatar,
        )
        await inter.send(embed=embed)

    @commands.slash_command(
        name="beer", description="Give someone a beer! 🍻"
    )  # Credit: AlexFlipNote - https://github.com/AlexFlipnote
    async def beer(
        self,
        inter: ApplicationCommandInteraction,
        user: disnake.Member = None,
        *,
        reason,
    ):
        """Give someone a beer! 🍻"""
        if not user or user.id == inter.author.id:
            return await inter.send(f"**{inter.author.name}**: paaaarty!🎉🍺")
        if user.id == self.bot.user.id:
            return await inter.send("*drinks beer with you* 🍻")
        if user.bot:
            return await inter.send(
                f"I would love to give beer to the bot **{inter.author.name}**, but I don't think it will respond to you :/"
            )
        beer_offer = f"**{user.name}**, you got a 🍺 offer from **{inter.author.name}**"
        beer_offer = f"{beer_offer}\n\n**Reason:** {reason}" if reason else beer_offer
        await inter.send(beer_offer)
        msg = await inter.original_message()

        def reaction_check(m):
            if m.message_id == msg.id and m.user_id == user.id and str(m.emoji) == "🍻":
                return True
            return False

        try:
            await msg.add_reaction("🍻")
            await self.bot.wait_for(
                "raw_reaction_add", timeout=30.0, check=reaction_check
            )
            await msg.edit(
                content=f"**{user.name}** and **{inter.author.name}** are enjoying a lovely beer together 🍻"
            )
        except asyncio.TimeoutError:
            await msg.delete()
            await inter.send(
                f"well, doesn't seem like **{user.name}** wanted a beer with you **{inter.author.name}** ;-;"
            )
        except disnake.Forbidden:
            # Yeah so, bot doesn't have reaction permission, drop the "offer" word
            beer_offer = f"**{user.name}**, you got a 🍺 from **{inter.author.name}**"
            beer_offer = (
                f"{beer_offer}\n\n**Reason:** {reason}" if reason else beer_offer
            )
            await msg.edit(content=beer_offer)

    @commands.slash_command(
        aliases=["slots", "bet"]
    )  # Credit: AlexFlipNote - https://github.com/AlexFlipnote
    async def slot(self, inter):
        """Roll the slot machine"""
        emojis = "💻💾💿🖥🖨🖱🌐⌨"
        a, b, c = [random.choice(emojis) for g in range(3)]
        slotmachine = f"**[ {a} | {b} | {c} ]\n{inter.author.name}**,"

        if a == b == c:
            await inter.send(f"{slotmachine} All matching, you won! 🎉")
        elif (a == b) or (a == c) or (b == c):
            await inter.send(f"{slotmachine} 2 in a row, you won! 🎉")
        else:
            await inter.send(f"{slotmachine} No match, you lost 😢")

    @commands.slash_command(
        name="8ball", brief="8ball", description="Ask the magic 8ball a question"
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def eightball(self, inter: ApplicationCommandInteraction, *, question):
        """Ask the magic 8ball a question"""
        responses = [
            "It is certain.",
            "It is decidedly so.",
            "Without a doubt.",
            "Yes - definitely.",
            "You may rely on it.",
            "As I see it, yes.",
            "Most likely.",
            "Outlook good.",
            "Yes.",
            "Signs point to yes.",
            "Reply hazy, try again.",
            "Ask again later.",
            "Better not tell you now.",
            "Cannot predict now.",
            "Concentrate and ask again.",
            "Don't count on it.",
            "My reply is no.",
            "My sources say no.",
            "Outlook not so good.",
            "Very doubtful.",
        ]
        await inter.send(
            f"Question: {question}\nAnswer: **{random.choice(responses)}**"
        )

    @commands.slash_command(
        name="askogiroid",
        description="Ogiroid will guess the character you are thinking off.",
    )
    # Credit for this code goes to: Yash230306 - https://github.com/Yash230306/Akinator-Discord-Bot/blob/main/bot.py
    async def askogiroid(self, inter):
        async with inter.author.typing():
            intro = disnake.Embed(
                title="Ogiroid",
                description=f"Hello {inter.author.mention}!",
                color=0xFFFFFF,
            )
            intro.set_thumbnail(
                url="https://media.discordapp.net/attachments/985729550732394536/987287532146393109/discord-avatar-512-NACNJ.png"
            )
            intro.set_footer(
                text="Think about a real or fictional character. I will try to guess who it is"
            )
            bye = disnake.Embed(
                title="Ogiroid",
                description="Bye, " + inter.author.mention,
                color=0xFFFFFF,
            )
            bye.set_footer(text="Ogiroid left the chat!")
            bye.set_thumbnail(
                url="https://media.discordapp.net/attachments/985729550732394536/987287532146393109/discord-avatar-512-NACNJ.png"
            )
            await inter.send(embed=intro)

            def check(msg):
                return msg.author == inter.author and msg.channel == inter.channel

            components = [
                disnake.ui.Button(
                    label="Yes", custom_id="y", style=disnake.ButtonStyle.green
                ),
                disnake.ui.Button(
                    label="No", custom_id="n", style=disnake.ButtonStyle.red
                ),
                disnake.ui.Button(label="Probably", custom_id="p"),
                disnake.ui.Button(label="Idk", custom_id="idk"),
                disnake.ui.Button(
                    label="Back", custom_id="b", style=disnake.ButtonStyle.blurple
                ),
            ]

            try:
                aki = ak.Akinator()
                q = aki.start_game(language="en")
                channel = self.bot.get_channel(inter.channel.id)
                button_click = channel
                while aki.progression <= 80:
                    question = disnake.Embed(
                        title="Question", description=q, color=0xFFFFFF
                    )
                    question.set_thumbnail(
                        url="https://media.discordapp.net/attachments/985729550732394536/987287532146393109/discord-avatar-512-NACNJ.png"
                    )
                    await button_click.send(embed=question, components=components)
                    try:
                        button_click = await self.bot.wait_for(
                            "button_click", check=check, timeout=30
                        )
                    except asyncio.TimeoutError:
                        await inter.send(
                            "Sorry you took too long to respond!(waited for 30sec)"
                        )
                        await inter.send(embed=bye)
                        return
                    if button_click.component.custom_id == "b":
                        try:
                            q = aki.back()
                        except ak.CantGoBackAnyFurther as e:
                            await errorEmb(button_click, e)
                            continue
                    else:
                        q = aki.answer(button_click.component.custom_id)

                aki.win()
                answer = disnake.Embed(
                    title=f"Your character: {aki.first_guess['name']}",
                    description=f"Your character is: {aki.first_guess['description']}",
                    color=0xFFFFFF,
                )
                # answer.set_image(aki.first_guess['absolute_picture_path']) may contain NSFW images
                answer.set_footer(text="Was I correct?")
                await button_click.send(
                    embed=answer, components=[components[0], components[1]]
                )
                # await inter.send(f"It's {aki.first_guess['name']} ({aki.first_guess['description']})! Was I correct?(y/n)\n{aki.first_guess['absolute_picture_path']}\n\t")
                try:
                    correct = await self.bot.wait_for(
                        "button_click", check=check, timeout=30
                    )
                except asyncio.TimeoutError:
                    await errorEmb(correct, "Sorry you took too long to respond.")
                    await inter.send(embed=bye)
                    return
                if correct.component.custom_id == "y":
                    yes = disnake.Embed(title="Yeah!!!", color=0xFFFFFF)
                    yes.set_thumbnail(
                        url="https://media.discordapp.net/attachments/985729550732394536/987287532146393109/discord-avatar-512-NACNJ.png"
                    )
                    await correct.send(embed=yes)
                else:
                    no = disnake.Embed(title="Oh Noooooo!!!", color=0xFFFFFF)
                    no.set_thumbnail(
                        url="https://media.discordapp.net/attachments/985729550732394536/987287532146393109/discord-avatar-512-NACNJ.png"
                    )
                    await correct.send(embed=no)
                await channel.send(embed=bye)
            except Exception as e:
                await errorEmb(inter, e)

    @commands.slash_command(
        name="bored", brief="activity", description="Returns an activity"
    )
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def bored(self, inter):
        """Returns an activity"""
        async with HTTPSession() as activitySession:
            async with activitySession.get(
                f"https://boredapi.com/api/activity", ssl=False
            ) as activityData:  # keep as http
                activity = await activityData.json()
                await inter.send(activity["activity"])

    @commands.slash_command(
        name="morse", description="Encode text into morse code and decode morse code."
    )
    async def morse(self, inter):
        pass

    @morse.sub_command(name="encode", description="Encodes text into morse code.")
    async def encode(self, inter: ApplicationCommandInteraction, text: str):
        encoded_list = []

        for char in text:

            for key in self.morse:
                if key == char.lower():
                    encoded_list.append(self.morse[key])

        encoded_string = " ".join(encoded_list)
        await inter.send(f"``{encoded_string}``")

    @morse.sub_command(name="decode", description="Decodes Morse Code into Text.")
    async def decode(self, inter: ApplicationCommandInteraction, morse_code):
        decoded_list = []
        morse_list = morse_code.split()

        for item in morse_list:

            for key, value in self.morse.items():
                if value == item:
                    decoded_list.append(key)

        decoded_string = "".join(decoded_list)
        await inter.send(f"``{decoded_string}``")

    @commands.slash_command(description="Get Pokémon related information!")
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def pokemon(self, inter):
        pass

    @pokemon.sub_command(name="info", description="Get information about a Pokémon.")
    async def info(
        self,
        inter: ApplicationCommandInteraction,
        pokem: str = commands.ParamInfo(
            name="pokemon", description="The name of the Pokémon"
        ),
    ):
        response = await self.bot.session.get(
            f"https://pokeapi.co/api/v2/pokemon/{pokem}"
        )
        poke_data = await response.json()

        try:
            embed = disnake.Embed(title=poke_data["name"], color=0xFFFFFF)
            embed.set_thumbnail(url=poke_data["sprites"]["front_default"])
            embed.add_field(name="Type", value=poke_data["types"][0]["type"]["name"])
            embed.add_field(name="Height", value=f"{poke_data['height']}m")
            embed.add_field(name="Weight", value=f"{poke_data['weight']}kg")
            embed.add_field(
                name="Abilities", value=poke_data["abilities"][0]["ability"]["name"]
            )
            embed.add_field(name="Base Experience", value=poke_data["base_experience"])
            embed.add_field(name="Species", value=poke_data["species"]["name"])
            embed.set_footer(
                text=f"ID: {poke_data['id']} | Generation: {poke_data['game_indices'][0]['version']['name']} • Requested by: {inter.author.name}"
            )
        except KeyError as key:
            return await errorEmb(inter, f"{key}")
        return await inter.send(embed=embed)

    @commands.slash_command(name="urlshortner", description="Shortens a URL.")
    async def urlshortner(self, inter: ApplicationCommandInteraction, url: str):
        # checking if url starts with http:// or https://, if it does not, adding https:// towards the start
        if not (url.startswith("http://") or url.startswith("https://")):
            url = f"https://{url}"
        response = requests.post("https://roman.vm.net.ua/s", url)
        if response.status_code == 201:
            embed = disnake.Embed(
                color=0xFFFFFF,
                description=f"Your shortend URL is: {response.text}, or click [here]({response.text}) to visit it.",
            )
            embed.set_footer(text=f"Requested by: {inter.author.name}")
            return await inter.send(embed=embed)
        else:
            return await errorEmb(
                inter, "An unexpected error occurred! Please try again later."
            )


def setup(bot):
    bot.add_cog(Fun(bot))
