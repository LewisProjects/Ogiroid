import asyncio
import html
import random

import disnake
import textdistance
from disnake import Option
from disnake.ext import commands

from utils.CONSTANTS import COUNTRIES, TRIVIA_CATEGORIES
from utils.DBhandlers import FlagQuizHandler
from utils.assorted import getPosition
from utils.bot import OGIROID
from utils.exceptions import UserNotFound, UsersNotFound
from utils.shortcuts import QuickEmb, errorEmb


class Trivia(commands.Cog, name="Trivia"):
    def __init__(self, bot: OGIROID):
        self.bot = bot
        self.countries = COUNTRIES
        self.flag_quiz: FlagQuizHandler = None

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.wait_until_ready()
        self.flag_quiz: FlagQuizHandler = FlagQuizHandler(self.bot, self.bot.db)

    @commands.slash_command(name="flagquiz", description="Guess the flags.")
    async def guess_the_flag(self, inter):
        await inter.response.defer()
        await QuickEmb(inter, "Starting the quiz..").send()
        channel = inter.channel
        country_list = list(self.countries.items())
        random.shuffle(country_list)
        countries = dict(country_list)
        correct = 0
        tries = 0
        try:
            user = await self.flag_quiz.get_user(inter.author.id)
        except UserNotFound:
            await self.flag_quiz.add_user(inter.author.id)
            user = await self.flag_quiz.get_user(inter.author.id)

        def check(m):
            return m.author == inter.author and m.channel == inter.channel and len(m.content) <= 100

        for emoji, country in countries.items():
            tries += 1
            retry = True
            while retry:
                user = await self.flag_quiz.add_data(user_id=inter.author.id, user=user, correct=correct, tries=tries)
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
                    await self.flag_quiz.add_data(inter.author.id, tries - 1, correct, user=user)
                    return

                # Checks if the guess is similar to the actual name to account typos
                if type(country) == list:
                    for name in country:
                        if textdistance.hamming.normalized_similarity(guess.content.lower(), name.lower()) >= 0.7:
                            await QuickEmb(channel, f"Correct. The country indeed was {country[0]}").success().send()
                            correct += 1
                            retry = False
                            break
                elif textdistance.hamming.normalized_similarity(guess.content.lower(), country.lower()) >= 0.7:
                    await QuickEmb(channel, f"Correct. The country indeed was {country}").success().send()
                    correct += 1
                    retry = False

                if guess.content.lower() == "skip":
                    if type(country) == list:
                        country = country[0]
                    await QuickEmb(channel, f"The country was {country}").send()
                    retry = False
                elif guess.content.casefold() == "give up":
                    await guess.reply("Are you sure you want to quit? Type yes to confirm.")
                    try:
                        response = await self.bot.wait_for("message", check=check, timeout=60.0)
                    except asyncio.exceptions.TimeoutError:
                        await QuickEmb(channel, "Due to no response the quiz ended.").error().send()
                    else:
                        if response.content.casefold() not in [
                            "yes",
                            "y",
                            "yeah",
                            "yeah",
                            "yep",
                            "yup",
                            "sure",
                            "ok",
                            "ye",
                        ]:
                            continue
                    await QuickEmb(channel, f"Your Score: {correct}/{tries - 1}. Thanks for playing.").send()
                    await self.flag_quiz.add_data(guess.author.id, tries - 1, correct, user=user)
                    return
                #If retry is still True (not changed) then the guess was incorrect
                elif retry:
                    await errorEmb(inter, "Incorrect")

        await self.flag_quiz.add_data(inter.author.id, tries, correct, user=user)
        await channel.send(f"Great Job on finishing the entire Quiz. Score: {correct}/{tries}")

    @commands.slash_command(name="flagquiz-leaderboard", description="Leaderboard for the flag quiz.")
    async def flag_quiz_leaderboard(
        self,
        inter,
        sortby: str = commands.Param(choices={"Correct Guesses": "correct", "Guesses": "tries", "Fully Completed": "completed"}),
    ):
        try:
            leaderboard = await self.flag_quiz.get_leaderboard(order_by=sortby)
        except UsersNotFound:
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
        except UserNotFound:
            await errorEmb(inter, "This user never took part in the flag quiz or doesn't exist.")
            return

        user = self.bot.get_user(player.user_id)
        embed = disnake.Embed(title=f"{user.display_name} Flag Quiz Stats", color=0xFFFFFF)
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name=f"Player:", value=f"{user}")
        embed.add_field(name="Correct Guesses / Total Guesses", value=f"{player.correct} / {player.tries}", inline=False)
        embed.add_field(name="Got all 199 Flags correct in one Run", value=f"{player.completed} times")
        await inter.send(embed=embed)

    @commands.slash_command(
        name="trivia",
        description="A quick bit of Trivia.",
        options=[
            Option(
                name="category",
                description="The category of the questions",
                choices=[
                    "Any",
                    "General Knowledge",
                    "Entertainment: Books",
                    "Entertainment: Film",
                    "Entertainment: Music",
                    "Entertainment: Musicals & Theatres",
                    "Entertainment: Television",
                    "Entertainment: Video Games",
                    "Entertainment: Board Games",
                    "Science & Nature",
                    "Science: Computers",
                    "Science: Mathematics",
                    "Mythology",
                    "Sports",
                    "Geography",
                    "History",
                    "Politics",
                    "Art",
                    "Celebrities",
                    "Animals",
                    "Vehicles",
                    "Entertainment: Comics",
                    "Science: Gadgets",
                    "Entertainment: Japanese Anime & Manga",
                    "Entertainment: Cartoon & Animations",
                ],
            ),
            Option(name="amount", description="Amount of Questions", min_value=1),
            Option(
                name="difficulty",
                description="Difficulty of the questions",
                choices={"Easy": "easy", "Medium": "medium", "Hard": "hard"},
            ),
            Option(
                name="kind",
                description="Type of the questions",
                choices={"Multiple Choice": "multiple", "True/False": "boolean", "Any": "any"},
            ),
        ],
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def trivia(self, inter, category="Any", difficulty=None, amount: int = 5, kind="multiple"):
        if int(amount) <= 1:
            return await QuickEmb(inter, "The amount of questions needs to be at least 1").error().send()

        def check(m):
            return m.author == inter.author and m.channel == inter.channel

        correct = 0
        questions = 0
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
        if category == "Any" or category is None:
            response = await self.bot.session.get(
                f"https://opentdb.com/api.php?amount={amount}{f'&difficulty={difficulty}' if difficulty else ''}{f'&type={kind}' if kind != 'any' else ''}"
            )
        else:
            category_id = None
            for item in TRIVIA_CATEGORIES:
                if item["name"] == category:
                    category_id = item["id"]

            if category_id is None:
                return await QuickEmb(inter, "Invalid Category").error().send()

            response = await self.bot.session.get(
                f"https://opentdb.com/api.php?amount={amount}&category={category_id}{f'&difficulty={difficulty}' if difficulty else ''}{f'&type={kind}' if kind != 'any' else ''}"
            )
        data = await response.json()
        embed = disnake.Embed(title="Created Quiz", colour=0xFFFFFF)
        embed.set_author(name=inter.author, icon_url=inter.author.display_avatar)
        embed.set_thumbnail(url=inter.author.display_avatar)
        embed.add_field(name="Category:", value=category + "   ")
        embed.add_field(name="Difficulty:", value=difficulty if difficulty else "Any Difficulty")
        embed.add_field(name="Amount of Questions:", value=amount, inline=False)
        embed.add_field(name="Type:", value=kind, inline=False)
        await inter.send(embed=embed)

        n = 0
        channel = inter.channel
        for question in data["results"]:
            n += 1
            answer = question["correct_answer"]
            answers = question["incorrect_answers"]
            answers.append(answer)
            random.shuffle(answers)

            components = []
            answers_string = ""
            for i in range(len(answers)):
                answers_string += f"{emojis[i]}: {html.unescape(answers[i])}\n"
                components.append(disnake.ui.Button(emoji=emojis[i], custom_id=f"{i}"))

            embed = disnake.Embed(title=html.unescape(question["question"]), description=answers_string, color=0xFFFFFF)
            await channel.send(embed=embed, components=components)
            try:
                user_inter = await self.bot.wait_for("button_click", check=check, timeout=60.0)
            except asyncio.exceptions.TimeoutError:
                return await QuickEmb(channel, "Due to no response the quiz ended early.").error().send()

            user_answer = answers[int(user_inter.component.custom_id)]
            questions += 1
            if user_answer == answer:
                correct += 1
                if n == len(data["results"]):
                    await QuickEmb(user_inter, f"Correct the answer indeed is {html.unescape(answer)}.").success().send()
                else:
                    await QuickEmb(
                        user_inter,
                        f"Correct the answer indeed is {html.unescape(answer)}. Your score so far is {correct} / {questions}",
                    ).success().send()
            else:
                if n == len(data["results"]):
                    await QuickEmb(user_inter, f"Incorrect the correct answer is {html.unescape(answer)}.").error().send()
                else:
                    await QuickEmb(
                        user_inter,
                        f"Incorrect the correct answer is {html.unescape(answer)}. Your score so far is {correct} / {questions}",
                    ).error().send()

        await QuickEmb(channel, f"Thanks for playing. Your final Score is {correct} / {questions}.").send()


def setup(bot):
    bot.add_cog(Trivia(bot))
