from disnake import Embed
from disnake.ext import commands
import disnake
import random
from discord_together import DiscordTogether
import io
import asyncio
import akinator as ak
import time
from datetime import datetime
import os
from dotenv import load_dotenv

from cogs.utils.http import HTTPSession

load_dotenv("../secrets.env")


class Fun(commands.Cog):
    """Fun Commands!"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        TOKEN = os.getenv("TOKEN")
        self.togetherControl = await DiscordTogether(TOKEN)

    @commands.slash_command(name="youtube", description="Watch YouTube in a Discord VC with your friends")
    async def youtube(self, ctx):
        """Watch YouTube in a Discord VC with your friends"""
        if ctx.author.voice:
            chan = ctx.author.voice.channel.id
            link = await self.togetherControl.create_link(chan, "youtube")
            embed = disnake.Embed(
                title="YouTube",
                description=f"Click __[here]({link})__ to start the YouTube together session.",
                color=0xFF0000,
                timestamp=datetime.utcnow(),
            )
            embed.set_footer(
                text=f"Command issued by: {ctx.author.name}",
                icon_url=ctx.author.avatar,
            )
            await ctx.send(embed=embed)
        else:
            e = await ctx.send("**You must be in a voice channel to use this command!**")
            time.sleep(5)
            await e.delete()

    @commands.slash_command()
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def joke(self, inter):
        """Get a random joke!"""
        response = await self.bot.session.get("https://some-random-api.ml/joke")
        data = await response.json()
        embed = disnake.Embed(title="Joke!", description=data["joke"], color=0xFFFFFF)
        embed.set_footer(
            text=f"Command issued by: {inter.author.name}",
            icon_url=inter.message.author.avatar,
        )
        await inter.send(embed=embed)

    @commands.slash_command(
        name="trigger",
        brief="Trigger",
        description="For when you're feeling triggered.",
    )
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def triggered(self, inter, member: disnake.Member = None):
        """Time to get triggered."""
        if not member:
            member = inter.author
        trigImg = await self.bot.session.get(f"https://some-random-api.ml/canvas/triggered?avatar={member.avatar.url}")
        imageData = io.BytesIO(await trigImg.read())
        await inter.send(file=disnake.File(imageData, "triggered.gif"))

    @commands.slash_command(
        name="sus",
        brief="Sus-Inator4200",
        description="Check if your friend is kinda ***SUS***",
    )
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def amongus(self, inter, member: disnake.Member = None):
        """Check if your friends are sus or not"""
        await inter.send("Testing for sus-ness...")
        if not member:
            member = inter.author
        impostor = random.choice(["true", "false"])
        apikey = os.getenv("SRA_API_KEY")
        uri = f"https://some-random-api.ml/premium/amongus?username={member.name}&avatar={member.avatar.url}&impostor={impostor}&key={apikey}"
        resp = await self.bot.session.get(uri)
        if 300 > resp.status >= 200:
            fp = io.BytesIO(await resp.read())
            await inter.send(file=disnake.File(fp, "amogus.gif"))
        else:
            await inter.send("Couldnt get image :(")

    @commands.slash_command(name="invert", brief="invert", description="Invert the colours of your icon")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def invert(self, inter, member: disnake.Member = None):
        """Invert your profile picture."""
        if not member:
            member = inter.author
        trigImg = await self.bot.session.get(f"https://some-random-api.ml/canvas/invert/?avatar={member.avatar.url}")
        imageData = io.BytesIO(await trigImg.read())
        await inter.send(file=disnake.File(imageData, "invert.png"))

    @commands.slash_command(name="pixelate", brief="pixelate", description="Turn yourself into 144p!")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def pixelate(self, inter, member: disnake.Member = None):
        """Turn yourself into pixels"""
        if not member:
            member = inter.author
        trigImg = await self.bot.session.get(f"https://some-random-api.ml/canvas/pixelate/?avatar={member.avatar.url}")
        imageData = io.BytesIO(await trigImg.read())
        await inter.send(file=disnake.File(imageData, "pixelate.png"))

    @commands.slash_command(name="jail", brief="jail", description="Go to jail!")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def jail(self, inter, member: disnake.Member = None):
        """Go to horny jail"""
        if not member:
            member = inter.author

        trigImg = await self.bot.session.get(f"https://some-random-api.ml/canvas/jail?avatar={member.avatar.url}")
        imageData = io.BytesIO(await trigImg.read())
        await inter.send(file=disnake.File(imageData, "jail.png"))

    @commands.slash_command(
        name="beer", description="Give someone a beer! 🍻"
    )  # Credit: AlexFlipNote - https://github.com/AlexFlipnote
    async def beer(self, ctx, user: disnake.Member = None, *, reason):
        """Give someone a beer! 🍻"""
        if not user or user.id == ctx.author.id:
            return await ctx.send(f"**{ctx.author.name}**: paaaarty!🎉🍺")
        if user.id == self.bot.user.id:
            return await ctx.send("*drinks beer with you* 🍻")
        if user.bot:
            return await ctx.send(
                f"I would love to give beer to the bot **{ctx.author.name}**, but I don't think it will respond to you :/"
            )
        beer_offer = f"**{user.name}**, you got a 🍺 offer from **{ctx.author.name}**"
        beer_offer = f"{beer_offer}\n\n**Reason:** {reason}" if reason else beer_offer
        msg = await ctx.send(beer_offer)

        def reaction_check(m):
            if m.message_id == msg.id and m.user_id == user.id and str(m.emoji) == "🍻":
                return True
            return False

        try:
            await msg.add_reaction("🍻")
            await self.bot.wait_for("raw_reaction_add", timeout=30.0, check=reaction_check)
            await msg.edit(content=f"**{user.name}** and **{ctx.author.name}** are enjoying a lovely beer together 🍻")
        except asyncio.TimeoutError:
            await msg.delete()
            await ctx.send(f"well, doesn't seem like **{user.name}** wanted a beer with you **{ctx.author.name}** ;-;")
        except disnake.Forbidden:
            # Yeah so, bot doesn't have reaction permission, drop the "offer" word
            beer_offer = f"**{user.name}**, you got a 🍺 from **{ctx.author.name}**"
            beer_offer = f"{beer_offer}\n\n**Reason:** {reason}" if reason else beer_offer
            await msg.edit(content=beer_offer)

    @commands.slash_command(aliases=["slots", "bet"])  # Credit: AlexFlipNote - https://github.com/AlexFlipnote
    async def slot(self, ctx):
        """Roll the slot machine"""
        emojis = "💻💾💿🖥🖨🖱🌐⌨"
        a, b, c = [random.choice(emojis) for g in range(3)]
        slotmachine = f"**[ {a} | {b} | {c} ]\n{ctx.author.name}**,"

        if a == b == c:
            await ctx.send(f"{slotmachine} All matching, you won! 🎉")
        elif (a == b) or (a == c) or (b == c):
            await ctx.send(f"{slotmachine} 2 in a row, you won! 🎉")
        else:
            await ctx.send(f"{slotmachine} No match, you lost 😢")

    @commands.slash_command(name="8ball", brief="8ball", description="Ask the magic 8ball a question")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def eightball(self, inter, *, question):
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
        await inter.send(f"Question: {question}\nAnswer: **{random.choice(responses)}**")

    @commands.slash_command(
        name="askogiroid",
        description="Ogiroid will guess the character you are thinking off.",
    )
    # Credit for this code goes to: Yash230306 - https://github.com/Yash230306/Akinator-Discord-Bot/blob/main/bot.py
    async def askogiroid(self, ctx):
        async with ctx.author.typing():
            intro = disnake.Embed(
                title="Ogiroid",
                description=f"Hello {ctx.author.mention}!",
                color=0xFFFFFF,
            )
            intro.set_thumbnail(
                url="https://media.discordapp.net/attachments/985729550732394536/987287532146393109/discord-avatar-512-NACNJ.png"
            )
            intro.set_footer(text="Think about a real or fictional character. I will try to guess who it is")
            bye = disnake.Embed(
                title="Ogiroid",
                description="Bye, " + ctx.author.mention,
                color=0xFFFFFF,
            )
            bye.set_footer(text="Ogiroid left the chat!")
            bye.set_thumbnail(
                url="https://media.discordapp.net/attachments/985729550732394536/987287532146393109/discord-avatar-512-NACNJ.png"
            )
            await ctx.send(embed=intro)

            def check(msg):
                return (
                    msg.author == ctx.author
                    and msg.channel == ctx.channel
                    and msg.content.lower() in ["y", "n", "p", "b", "yes", "no", "probably", "idk", "back"]
                )

            try:
                aki = ak.Akinator()
                q = aki.start_game(language="en")
                while aki.progression <= 80:
                    question = disnake.Embed(title="Question", description=q, color=0xFFFFFF)
                    question.set_thumbnail(
                        url="https://media.discordapp.net/attachments/985729550732394536/987287532146393109/discord-avatar-512-NACNJ.png"
                    )
                    question.set_footer(text="Your answer:(y/n/p/idk/b)")
                    question_sent = await ctx.send(embed=question)
                    try:
                        msg = await self.bot.wait_for("message", check=check, timeout=30)
                    except asyncio.TimeoutError:
                        # await question_sent.delete()
                        await ctx.send("Sorry you took too long to respond!(waited for 30sec)")
                        await ctx.send(embed=bye)
                        return
                    # await question_sent.delete()
                    if msg.content.lower() in ["b", "back"]:
                        try:
                            q = aki.back()
                        except ak.CantGoBackAnyFurther:
                            await ctx.send(e)
                            continue
                    else:
                        try:
                            q = aki.answer(msg.content.lower())
                        except ak.InvalidAnswerError as e:
                            await ctx.send(e)
                            continue
                aki.win()
                answer = disnake.Embed(
                    title=f"Your character: {aki.first_guess['name']}",
                    description=f"Your character is: {aki.first_guess['description']}",
                    color=0xFFFFFF,
                )
                answer.set_footer(text="Was I correct? (y/n)")
                await ctx.send(embed=answer)
                # await ctx.send(f"It's {aki.first_guess['name']} ({aki.first_guess['description']})! Was I correct?(y/n)\n{aki.first_guess['absolute_picture_path']}\n\t")
                try:
                    correct = await self.bot.wait_for("message", check=check, timeout=30)
                except asyncio.TimeoutError:
                    await ctx.send("Sorry you took too long to respond! [30 seconds+]")
                    await ctx.send(embed=bye)
                    return
                if correct.content.lower() == "y":
                    yes = disnake.Embed(title="Yeah!!!", color=0xFFFFFF)
                    yes.set_thumbnail(
                        url="https://media.discordapp.net/attachments/985729550732394536/987287532146393109/discord-avatar-512-NACNJ.png"
                    )
                    await ctx.send(embed=yes)
                else:
                    no = disnake.Embed(title="Oh Noooooo!!!", color=0xFFFFFF)
                    no.set_thumbnail(
                        url="https://media.discordapp.net/attachments/985729550732394536/987287532146393109/discord-avatar-512-NACNJ.png"
                    )
                    await ctx.send(embed=no)
                await ctx.send(embed=bye)
            except Exception as e:
                await ctx.send(e)

    @commands.slash_command(name="bored", brief="activity", description="Returns an activity")
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def bored(self, inter):
        """Returns an activity"""
        async with HTTPSession() as activitySession:
            async with activitySession.get(
                f"https://boredapi.com/api/activity", ssl=False
            ) as activityData:  # keep as http
                activity = await activityData.json()
                await inter.send(activity["activity"])


def setup(bot):
    bot.add_cog(Fun(bot))
