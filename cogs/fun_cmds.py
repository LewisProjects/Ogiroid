from http import client
from sqlite3 import Timestamp
from disnake.ext import commands
import disnake
import random
import requests
from discord_together import DiscordTogether
from aiohttp import request
import io
import aiohttp
import asyncio
import time
from datetime import datetime


class Fun(commands.Cog):
    """Fun Commands!"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.togetherControl = await DiscordTogether(
            "OTg0ODAyMDA4NDAzOTU5ODc5.GR1i_b.zc0G9MjPwXA8wcvf7rAx3OJpwvpOmZSKSnqh50"
        )

    @commands.command()
    async def youtube(self, ctx):
        """Watch YouTube in a Discord VC with your friends"""
        if ctx.message.author.voice:
            chan = ctx.message.author.voice.channel.id
            link = await self.togetherControl.create_link(chan, "youtube")
            embed = disnake.Embed(
                title="YouTube",
                description=f"Click __[**HERE**]({link})__ to start the YouTube together session.",
                color=0xFF0000,
                timestamp=datetime.utcnow(),
            )
            embed.set_footer(
                text=f"Command issued by: {ctx.message.author.name}",
                icon_url=ctx.message.author.avatar,
            )
            await ctx.send(embed=embed)
        else:
            e = await ctx.send(
                "**You must be in a voice channel to use this command!**"
            )
            time.sleep(5)
            await e.delete()

    @commands.command()
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def joke(self, ctx):
        """Get a random joke!"""
        response = requests.get("https://some-random-api.ml/joke")
        data = response.json()
        embed = disnake.Embed(title="Joke!", description=data["joke"], color=0xFFFFFF)
        embed.set_footer(
            text=f"Command issued by: {ctx.message.author.name}",
            icon_url=ctx.message.author.avatar,
        )
        await ctx.send(embed=embed)

    @commands.command(
        name="trigger",
        brief="Trigger",
        description="For when you're feeling triggered.",
    )
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def triggered(self, ctx, member: disnake.Member = None):
        """Time to get triggered."""
        if not member:
            member = ctx.author
        async with aiohttp.ClientSession() as trigSession:
            async with trigSession.get(
                f"https://some-random-api.ml/canvas/triggered?avatar={member.avatar.url}"
            ) as trigImg:
                imageData = io.BytesIO(await trigImg.read())
                await ctx.reply(file=disnake.File(imageData, "triggered.gif"))

    @commands.command(
        name="sus",
        brief="Sus-Inator4200",
        description="Check if your friend is kinda ***SUS***",
    )
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def amongus(self, ctx, member: disnake.Member = None):
        """Check if your friends are sus or not"""
        await ctx.send("Testing for sus-ness...")
        if not member:
            member = ctx.author
        impostor = random.choice(["true", "false"])
        apikey = "rwaNgpkDJnwUuJhSZpJnavpFx"
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://some-random-api.ml/premium/amongus?username={member.name}&avatar={member.avatar.url}&impostor={impostor}&key={apikey}"
            ) as resp:
                if 300 > resp.status >= 200:
                    fp = io.BytesIO(await resp.read())
                    await ctx.reply(file=disnake.File(fp, "amogus.gif"))
                else:
                    await ctx.reply("Couldnt get image :(")
                await session.close()

    @commands.command(
        name="invert", brief="invert", description="Invert the colours of your icon"
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def invert(self, ctx, member: disnake.Member = None):
        """Invert your profile picture."""
        if not member:
            member = ctx.author
        async with aiohttp.ClientSession() as trigSession:
            async with trigSession.get(
                f"https://some-random-api.ml/canvas/invert/?avatar={member.avatar.url}"
            ) as trigImg:
                imageData = io.BytesIO(await trigImg.read())
                await ctx.reply(file=disnake.File(imageData, "invert.png"))

    @commands.command(
        name="pixelate", brief="pixelate", description="Turn yourself into 144p!"
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def pixelate(self, ctx, member: disnake.Member = None):
        """Turn yourself into pixels"""
        if not member:
            member = ctx.author
        async with aiohttp.ClientSession() as trigSession:
            async with trigSession.get(
                f"https://some-random-api.ml/canvas/pixelate/?avatar={member.avatar.url}"
            ) as trigImg:
                imageData = io.BytesIO(await trigImg.read())
                await ctx.reply(file=disnake.File(imageData, "pixelate.png"))

    @commands.command(name="jail", brief="jail", description="Go to jail!")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def jail(self, ctx, member: disnake.Member = None):
        """Go to horny jail"""
        if not member:
            member = ctx.author
        async with aiohttp.ClientSession() as trigSession:
            async with trigSession.get(
                f"https://some-random-api.ml/canvas/jail?avatar={member.avatar.url}"
            ) as trigImg:
                imageData = io.BytesIO(await trigImg.read())
                await ctx.reply(file=disnake.File(imageData, "jail.png"))

    @commands.command()  # Credit: AlexFlipNote - https://github.com/AlexFlipnote
    async def beer(
        self, ctx, user: disnake.Member = None, *, reason: commands.clean_content = ""
    ):
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
            await self.bot.wait_for(
                "raw_reaction_add", timeout=30.0, check=reaction_check
            )
            await msg.edit(
                content=f"**{user.name}** and **{ctx.author.name}** are enjoying a lovely beer together 🍻"
            )
        except asyncio.TimeoutError:
            await msg.delete()
            await ctx.send(
                f"well, doesn't seem like **{user.name}** wanted a beer with you **{ctx.author.name}** ;-;"
            )
        except disnake.Forbidden:
            # Yeah so, bot doesn't have reaction permission, drop the "offer" word
            beer_offer = f"**{user.name}**, you got a 🍺 from **{ctx.author.name}**"
            beer_offer = (
                f"{beer_offer}\n\n**Reason:** {reason}" if reason else beer_offer
            )
            await msg.edit(content=beer_offer)

    @commands.command(
        aliases=["slots", "bet"]
    )  # Credit: AlexFlipNote - https://github.com/AlexFlipnote
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

    @commands.command(
        name="8ball", brief="8ball", description="Ask the magic 8ball a question"
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def eightball(self, ctx, *, question):
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
        await ctx.send(f"Question: {question}\nAnswer: **{random.choice(responses)}**")


def setup(bot):
    bot.add_cog(Fun(bot))
