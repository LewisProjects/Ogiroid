import disnake
import datetime as dt
from disnake.ext import commands, tasks
from utils.DBhandlers import BirthdayHandler
from utils.exceptions import UserAlreadyExists, UserNotFound
from utils.shortcuts import QuickEmb, sucEmb, errorEmb

from utils.bot import OGIROID


class Birthday(commands.Cog):
    def __init__(self, bot: OGIROID):
        self.bot = bot
        self.birthday: BirthdayHandler = None

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.bot.ready_:
            self.birthday: BirthdayHandler = BirthdayHandler(self.bot, self.bot.db)

    def cog_unload(self):
        self.birthday_check.cancel()

    @commands.slash_command(name="birthday")
    async def birthday(self, inter: disnake.ApplicationCommandInteraction):
        pass

    @birthday.sub_command(name="set", description="Set your birthday")
    async def set(
        self,
        inter,
        day: int = commands.Param(name="day", ge=1, le=31, description="The day of your birthday"),
        month: str = commands.Param(
            name="month",
            description="The month of your birthday",
            choices={
                "January": "01",
                "February": "02",
                "March": "03",
                "April": "04",
                "May": "05",
                "June": "06",
                "July": "07",
                "August": "08",
                "September": "09",
                "October": "10",
                "November": "11",
                "December": "12",
            },
        ),
    ):
        if month is None or day is None:
            return await errorEmb(inter, "You need to provide a month and a day")
        if day < 1 or day > 31:
            return await errorEmb(inter, "The day must be between 1 and 31")

        birth_date = f"{day}/{month}"
        try:
            await self.birthday.create_user(inter.author.id, birth_date)
        except UserAlreadyExists:
            return await errorEmb(inter, "You already have a birthday set")

        await sucEmb(inter, f"Your birthday has been set to {birth_date}")

    @birthday.sub_command(name="remove", description="Remove your birthday")
    async def remove(self, inter):
        try:
            await self.birthday.delete_user(inter.author.id)
        except UserNotFound:
            return await errorEmb(inter, "You don't have a birthday set")

        await sucEmb(inter, "Your birthday has been removed")

    @birthday.sub_command(name="get", description="Get the birthday of a user")
    async def get(self, inter, user: disnake.User = commands.Param(name="user", default=None)):
        if user is None:
            user = inter.author
        else:
            user = await self.bot.fetch_user(user.id)

        birthday = await self.birthday.get_user(user.id)
        if birthday is None:
            return await errorEmb(inter, "This user doesn't have a birthday set")
        await QuickEmb(inter, f"{user.mention}'s birthday is {birthday.birthday}").send()

    @tasks.loop(time=[dt.time(12, 0, 0)])
    async def birthday_check(self):
        channel = self.bot.get_channel(self.bot.config.channels.birthdays)
        guild = self.bot.get_guild(self.bot.config.guilds.main_guild)
        if channel is None:
            return
        today = dt.datetime.utcnow().strftime("%d/%m")
        users = await self.birthday.get_users()
        for user in users:
            if user.birthday.split("/") == today:
                member = await guild.fetch_member(user.user_id)
                if member is not None:
                    await channel.send(f"Happy birthday {member.mention}!")


def setup(bot):
    bot.add_cog(Birthday(bot))
