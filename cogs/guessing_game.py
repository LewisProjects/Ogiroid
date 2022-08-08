import asyncio
import random
import time

import disnake
import textdistance
from disnake.ext import commands

from utils.CONSTANTS import COUNTRIES
from utils.DBhandelers import FlagQuizHandler
from utils.assorted import getPosition
from utils.bot import OGIROID
from utils.exceptions import FlagQuizUserNotFound, FlagQuizUsersNotFound
from utils.shortcuts import QuickEmb, errorEmb


class GuessingGame(commands.Cog, name="Guessing Games"):
    def __init__(self, bot: OGIROID):
        self.bot = bot
        self.countries = COUNTRIES
        self.flag_quiz: FlagQuizHandler = None

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.wait_until_ready()
        self.flag_quiz: FlagQuizHandler = FlagQuizHandler(self.bot, self.bot.db)

    @commands.slash_command(name="guess", description="I will magically guess your number.")
    @commands.guild_only()
    async def guess(self, ctx, *, answer=None):
        card1 = "https://cdn.discordapp.com/attachments/745162323953713223/937001823590576138/unknown.png"
        card1num = 16
        card2 = "https://cdn.discordapp.com/attachments/745162323953713223/937001823821238423/unknown.png"
        card2num = 4
        card3 = "https://cdn.discordapp.com/attachments/745162323953713223/937001824018378802/unknown.png"
        card3num = 8
        card4 = "https://cdn.discordapp.com/attachments/745162323953713223/937001824274235392/unknown.png"
        card4num = 1
        card5 = "https://cdn.discordapp.com/attachments/745162323953713223/937001824483942450/unknown.png"
        card5num = 2
        card6 = "https://cdn.discordapp.com/attachments/745162323953713223/937001824735625257/unknown.png"
        card6num = 32

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and len(m.content) <= 100

        await ctx.send("I will magically guess your number. \n **Think of a number between 1-63**\n *We will begin shortly...*")

        time.sleep(5)
        embed = disnake.Embed(title="Number Guesser", color=0x729FCF)
        embed.add_field(
            name="1/6\n",
            value='\n```yaml\n If your number is on this image, reply with "yes", else "no"  \n```',
        )
        embed.set_image(url=card1)
        await ctx.send(embed=embed)

        entry = await self.bot.wait_for("message", check=check, timeout=60.0)
        ent = entry.content
        answer = ent.lower()

        if answer == "yes":
            num1 = card1num
            pass
        elif answer == "no":
            num1 = 0
            pass
        else:
            await ctx.send("Invalid answer, please start over.")
            return

        embed = disnake.Embed(title="Number Guesser", color=0x77BC65)
        embed.add_field(
            name="2/6\n",
            value='\n```yaml\n If your number is on this image, reply with "yes", else "no"  \n```',
        )
        embed.set_image(url=card2)
        await ctx.send(embed=embed)

        entry = await self.bot.wait_for("message", check=check, timeout=60.0)
        answer = entry.content

        if answer == "yes":
            num2 = card2num
            pass
        elif answer == "no":
            num2 = 0
            pass
        else:
            await ctx.send("Invalid answer, please start over.")
            return

        embed = disnake.Embed(title="Number Guesser", color=0xFF972F)
        embed.add_field(
            name="3/6\n",
            value='\n```yaml\n If your number is on this image, reply with "yes", else "no"  \n```',
        )
        embed.set_image(url=card3)
        await ctx.send(embed=embed)

        entry = await self.bot.wait_for("message", check=check, timeout=60.0)
        answer = entry.content

        if answer == "yes":
            num3 = card3num
            pass
        elif answer == "no":
            num3 = 0
            pass
        else:
            await ctx.send("Invalid answer, please start over.")
            return

        embed = disnake.Embed(title="Number Guesser", color=0xE16173)
        embed.add_field(
            name="4/6\n",
            value='\n```yaml\n If your number is on this image, reply with "yes", else "no"  \n```',
        )
        embed.set_image(url=card4)
        await ctx.send(embed=embed)

        entry = await self.bot.wait_for("message", check=check, timeout=60.0)
        answer = entry.content

        if answer == "yes":
            num4 = card4num
            pass
        elif answer == "no":
            num4 = 0
            pass
        else:
            await ctx.send("Invalid answer, please start over.")
            return

        embed = disnake.Embed(title="Number Guesser", color=0xFFD428)
        embed.add_field(
            name="5/6\n",
            value='\n```yaml\n If your number is on this image, reply with "yes", else "no"  \n```',
        )
        embed.set_image(url=card5)
        await ctx.send(embed=embed)

        entry = await self.bot.wait_for("message", check=check, timeout=60.0)
        answer = entry.content

        if answer == "yes":
            num5 = card5num
            pass
        elif answer == "no":
            num5 = 0
            pass
        else:
            await ctx.send("Invalid answer, please start over.")
            return

        embed = disnake.Embed(title="Number Guesser", color=0xBBE33D)
        embed.add_field(
            name="6/6\n",
            value='\n```yaml\n If your number is on this image, reply with "yes", else "no"  \n```',
        )
        embed.set_image(url=card6)
        await ctx.send(embed=embed)

        entry = await self.bot.wait_for("message", check=check, timeout=60.0)
        answer = entry.content
        if answer == "yes":
            num6 = card6num
            pass
        elif answer == "no":
            num6 = 0
            pass
        else:
            await ctx.send("Invalid answer, please start over.")
            return

        await ctx.send("Hmmm.. Is your number: *drumroll please*")
        number = num1 + num2 + num3 + num4 + num5 + num6
        if number == 0:
            number = "You can't pick 0, I said between 1 and 63 :middle_finger:"
            time.sleep(5)
        await ctx.send(f"`{number}`")

    @commands.slash_command(name="flagquiz", description="Guess the flags.")
    async def guess_the_flag(self, inter):
        await QuickEmb(inter, "Starting the quiz..").send()
        channel = inter.channel
        country_list = list(self.countries.items())
        random.shuffle(country_list)
        countries = dict(country_list)

        def check(m):
            return m.author == inter.author and m.channel == inter.channel and len(m.content) <= 100

        correct = 0
        tries = 0
        for emoji, country in countries.items():
            tries += 1
            retry = True
            while retry:
                embed = disnake.Embed(
                    title="Guess the Flag.",
                    description="To skip onto the next write ``skip``. To give up write ``give up``\n"
                    f"Current Score: {correct}/{tries - 1}",
                    color=0xFFFFFF,
                )
                await channel.send(embed=embed)
                await channel.send(emoji)
                try:
                    guess = await self.bot.wait_for("message", check=check, timeout=60.0)
                except asyncio.exceptions.TimeoutError:
                    await QuickEmb(channel, "Due to no response the quiz ended early.").error().send()
                    await self.flag_quiz.add_data(inter.author.id, tries - 1, correct)
                    return

                # Checks if the guess is similar to the actual name to account typos
                if type(country) == list:
                    for name in country:
                        if textdistance.hamming.normalized_similarity(guess.content.lower(), name.lower()) >= 0.7:
                            await QuickEmb(channel, f"Correct. The country indeed was {country[0]}").success().send()
                            correct += 1
                            retry = False
                else:
                    if textdistance.hamming.normalized_similarity(guess.content.lower(), country.lower()) >= 0.7:
                        await QuickEmb(channel, f"Correct. The country indeed was {country}").success().send()
                        correct += 1
                        retry = False
                    elif guess.content.lower() == "skip":
                        await QuickEmb(channel, f"The country was {country}").send()
                        retry = False
                    elif guess.content.lower() == "give up":
                        await guess.reply("Are you sure you want to quit? Type yes to confirm.")
                        try:
                            response = await self.bot.wait_for("message", check=check, timeout=60.0)
                        except asyncio.exceptions.TimeoutError:
                            await QuickEmb(channel, "Due to no response the quiz ended.").error().send()
                        else:
                            if response.content.lower() in ["yes", "y", "yeah", "yeah", "yep", "yup", "sure", "ok", "ye"]:
                                pass
                            else:
                                continue
                        await QuickEmb(channel, f"Your Score: {correct}/{tries}. Thanks for playing.").send()
                        await self.flag_quiz.add_data(guess.author.id, tries - 1, correct)
                        return
                    else:
                        embed = QuickEmb(channel, "Incorrect")
                        await embed.error().send()

        await self.flag_quiz.add_data(inter.author.id, tries, correct)
        await channel.send(f"Great Job on finishing the entire Quiz. Score: {correct}/{tries}")

    @commands.slash_command(name="flagquiz-leaderboard", description="Leaderboard for the flag quiz.")
    async def flag_quiz_leaderboard(
        self,
        inter,
        sortby: str = commands.Param(choices={"Correct Guesses": "correct", "Guesses": "tries", "Fully Completed": "completed"}),
    ):
        try:
            leaderboard = await self.flag_quiz.get_leaderboard(order_by=sortby)
        except FlagQuizUsersNotFound:
            return await QuickEmb(inter, "No users have taken the quiz yet.").error().send()
        translator = {"correct": "Correct Guesses", "tries": "Guesses", "completed": "Fully Completed"}

        leaderboard_string = ""
        leaderboard_header = "Place  ***-***  User  ***-***  Correct Guesses/Total Guesses  ***-***  Completed   "
        i = 0
        for user in leaderboard:
            i += 1
            username = self.bot.get_user(user.user_id)
            leaderboard_string += f"{getPosition(i)} **-** {username} **-** {user.correct}/{user.tries} **-** {user.completed}\n"
        embed = disnake.Embed(
            title="Flag Quiz All time Leaderboard",
            description=f"The top 10 Flag Quiz Users are on this Leaderboard. Sorted by: {translator[sortby]}\n",
            color=disnake.Color.random(seed=inter.user.id),
        )
        embed.add_field(name=leaderboard_header, value=leaderboard_string)

        await inter.send(embed=embed)

    @commands.slash_command(name="flagquiz-user", description="Get Flag Quiz User Stats about a particular user.")
    async def flag_quiz_user(self, inter, user: disnake.User = None):
        if user:
            user_id = user.id
        else:
            user_id = inter.author.id
        try:
            player = await self.flag_quiz.get_user(user_id)
        except FlagQuizUserNotFound:
            await errorEmb(inter, "This user never took part in the flag quiz or doesn't exist.")
            return

        player = player[0]
        user = self.bot.get_user(player.user_id)
        embed = disnake.Embed(title=f"{user.display_name} Flag Quiz Stats", color=0xFFFFFF)
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name=f"Player:", value=f"{user}")
        embed.add_field(name="Correct Guesses / Total Guesses", value=f"{player.correct} / {player.tries}", inline=False)
        embed.add_field(name="Got all 199 Flags correct in one Run", value=f"{player.completed} times")
        await inter.send(embed=embed)


def setup(bot):
    bot.add_cog(GuessingGame(bot))
