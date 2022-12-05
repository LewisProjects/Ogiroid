import datetime

import disnake
import datetime as dt
from disnake.ext import commands, tasks
import random

from utils.DBhandlers import BirthdayHandler
from utils.exceptions import UserAlreadyExists, UserNotFound
from utils.shortcuts import QuickEmb, sucEmb, errorEmb
from utils.CONSTANTS import months, congrats_messages
from utils.bot import OGIROID


class Birthday(commands.Cog):
    def __init__(self, bot: OGIROID):
        self.bot = bot
        self.birthday: BirthdayHandler = None
        self.birthday_check.start()

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.bot.ready_:
            self.birthday: BirthdayHandler = BirthdayHandler(self.bot, self.bot.db)

    def cog_unload(self):
        self.birthday_check.cancel()

    @commands.slash_command(name="birthday")
    async def birthday(self, inter: disnake.ApplicationCommandInteraction):
        pass

    @birthday.sub_command(
        name="set", description="Set your birthday. Cant be removed without Staff."
    )
    async def set(
        self,
        inter,
        day: int = commands.Param(
            name="day",
            ge=1,
            le=31,
            description="The day of your birthday. Select carefully.",
        ),
        month: str = commands.Param(
            name="month",
            description="The month of your birthday. Select carefully.",
            choices=months,
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

    @commands.has_permissions(manage_roles=True)
    @birthday.sub_command(
        name="edit", description="Edit a users birthday. Can only be done by Staff."
    )
    async def edit(
        self,
        inter,
        day: int = commands.Param(
            name="day", ge=1, le=31, description="The day of the birthday."
        ),
        month: str = commands.Param(
            name="month",
            description="The month of the birthday.",
            choices=months,
        ),
        user: disnake.User = commands.Param(
            name="user", description="User to edit the birthday of."
        ),
    ):
        try:
            await self.birthday.update_user(user.id, f"{day}/{month}")
            return await sucEmb(inter, f"Birthday has been updated to {day}/{month}")
        except UserNotFound:
            return await errorEmb(inter, "The User doesn't have a birthday set")

    @commands.has_permissions(manage_roles=True)
    @birthday.sub_command(
        name="remove", description="Remove a birthday. Can only be done by Staff."
    )
    async def remove(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.User = commands.Param(
            name="user", description="Removes the birthday of this user"
        ),
    ):
        try:
            await self.birthday.delete_user(user.id)
        except UserNotFound:
            return await errorEmb(inter, "This user doesn't have a birthday set")

        await sucEmb(inter, "The birthday has been removed")

    @birthday.sub_command(name="get", description="Get the birthday of a user")
    async def get(
        self, inter, user: disnake.User = commands.Param(name="user", default=None)
    ):
        if user is None:
            user = inter.author
        else:
            user = await self.bot.fetch_user(user.id)

        birthday = await self.birthday.get_user(user.id)
        if birthday is None:
            return await errorEmb(inter, "This user doesn't have a birthday set")

        next_birthday = datetime.datetime.strptime(
            birthday.birthday + f"/{dt.datetime.now().year}", "%d/%m/%Y"
        )
        if next_birthday < datetime.datetime.now():
            next_birthday = datetime.datetime.strptime(
                birthday.birthday + f"/{dt.datetime.now().year + 1}", "%d/%m/%Y"
            )
        await QuickEmb(
            inter,
            f"{user.mention}'s birthday is in {(next_birthday - datetime.datetime.now()).days} Days."
            f" <t:{str(next_birthday.timestamp()).split('.')[0]}:D>",
        ).send()

    # @tasks.loop(time=[dt.time(dt.datetime.utcnow().hour, dt.datetime.utcnow().minute, dt.datetime.utcnow().second + 10)])
    # ^ use this when testing birthdays
    @tasks.loop(time=[dt.time(8, 0, 0)])
    # loops every day at 8:00 UTC time
    async def birthday_check(self):
        channel = self.bot.get_channel(self.bot.config.channels.birthdays)
        guild = self.bot.get_guild(self.bot.config.guilds.main_guild)
        if channel is None:
            return
        today = dt.datetime.utcnow().strftime("%d/%m")
        # Gets all users from the db
        users = await self.birthday.get_users()
        for user in users:
            member = await guild.fetch_member(user.user_id)
            # if the member is None, the user is not in the server anymore
            if member is None:
                continue

            # if the birthday is today, congratulate the user
            if user.birthday == today:
                await member.add_roles(guild.get_role(self.bot.config.roles.birthday))
                congrats_msg = await channel.send(
                    f"{random.choice(congrats_messages)} {member.mention}! 🎂"
                )
                await congrats_msg.add_reaction("🥳")
            # If the birthday isn't today and the user still has the birthday role, remove it
            elif (
                user.birthday != today
                and member.get_role(self.bot.config.roles.birthday) is not None
            ):
                await member.remove_roles(
                    guild.get_role(self.bot.config.roles.birthday)
                )


def setup(bot):
    bot.add_cog(Birthday(bot))
