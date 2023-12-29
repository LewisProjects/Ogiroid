import disnake
from disnake.ext import commands, tasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from utils.bot import OGIROID
from utils.db_models import Commands, TotalCommands
from sqlalchemy.dialects.postgresql import insert as pg_insert


class Stats(commands.Cog):
    def __init__(self, bot: OGIROID):
        self.bot = bot
        self.update_stats.start()

    def cog_unload(self):
        self.update_stats.cancel()

    @tasks.loop(hours=1)
    async def update_stats(self):
        # add command usage to db
        commands_ran = self.bot.commands_ran.copy()
        total_commands_ran = self.bot.total_commands_ran.copy()

        for guild_id, guild_commands_ran in commands_ran.items():
            for command, count in guild_commands_ran.items():
                async with self.bot.db.begin() as session:
                    stmt = pg_insert(Commands).values(
                        guild_id=guild_id, command=command, command_used=count
                    )
                    stmt = stmt.on_conflict_do_update(
                        index_elements=["guild_id", "command"],
                        set_={"command_used": Commands.command_used + count},
                    )
                    await session.execute(stmt)

        for guild_id, count in total_commands_ran.items():
            async with self.bot.db.begin() as session:
                stmt = pg_insert(TotalCommands).values(
                    guild_id=guild_id, total_commands_used=count
                )
                stmt = stmt.on_conflict_do_update(
                    index_elements=["guild_id"],
                    set_={
                        "total_commands_used": TotalCommands.total_commands_used + count
                    },
                )
                await session.execute(stmt)

        # reset command usage
        self.bot.commands_ran = {}
        self.bot.total_commands_ran = {}

    @commands.slash_command(description="Stats about the commands that have been ran")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def cmdstats(self, inter):
        await inter.response.defer()

        async with self.bot.db.begin() as session:
            session: AsyncSession = session
            cmdsran = await session.execute(
                select(Commands.command, Commands.command_used).filter_by(
                    guild_id=inter.guild.id
                )
            )
            cmdsran = dict(cmdsran.all())

            stmt = select(TotalCommands.total_commands_used).filter_by(
                guild_id=inter.guild.id
            )
            total_commands_ran = await session.execute(stmt)
            total_commands_ran = total_commands_ran.scalar()

        sortdict = dict(sorted(cmdsran.items(), key=lambda x: x[1], reverse=True))
        value_iterator = iter(sortdict.values())
        key_iterator = iter(sortdict.keys())
        emby = disnake.Embed(
            title=f"{self.bot.user.display_name} command Stats",
            description=f"{total_commands_ran} Commands ran in total.\nUpdated hourly.",
            color=self.bot.config.colors.white,
        )
        if len(cmdsran) < 2:
            return await inter.send(
                embed=disnake.Embed(
                    title=f"{self.bot.user.display_name} command Stats",
                    description=f"{total_commands_ran} Commands ran in total.\n",
                    color=self.bot.config.colors.white,
                )
            )

        text = (
            f"🥇: /{next(key_iterator)} ({next(value_iterator)} uses)\n"
            + f"🥈: /{next(key_iterator)} ({next(value_iterator)} uses)\n"
            + f"🥉: /{next(key_iterator)} ({next(value_iterator)} uses)\n"
        )
        i = 2
        for key in key_iterator:
            text += f"🏅: /{key} ({next(value_iterator)} uses)\n"
            i += 1
            # total 10
            if i == 10:
                break

        emby.add_field(name="Top 10 commands ran", value=text)

        await inter.send(embed=emby)


def setup(bot):
    bot.add_cog(Stats(bot))
