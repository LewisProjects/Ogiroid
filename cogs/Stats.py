import io
import disnake
from disnake.ext import commands, tasks
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from utils.bot import OGIROID
from utils.db_models import Commands, TotalCommands


def get_color_gradient(c1, c2, n):
    """
    Given two rgb colors, returns a color gradient
    with n colors.
    """
    assert n > 1
    c1_rgb = [val / 255 for val in c1]
    c2_rgb = [val / 255 for val in c2]
    mix_pcts = [x / (n - 1) for x in range(n)]
    rgb_colors = [[(1 - mix) * c1_val + (mix * c2_val) for c1_val, c2_val in zip(c1_rgb, c2_rgb)] for mix in mix_pcts]
    return [
        "#" + "".join([format(int(round(val * 255)), "02x") for val in item])
        for item in rgb_colors
    ]


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
        # add bots avatar
        emby.set_footer(
            text=self.bot.user.display_name, icon_url=self.bot.user.avatar.url
        )
        emby.timestamp = disnake.utils.utcnow()

        colors = get_color_gradient((0, 0, 0), (225, 225, 225), 10)

        fig = Figure(figsize=(5, 5), dpi=180)
        ax: Axes = fig.subplots()
        ax.bar(
            sortdict.keys(),
            sortdict.values(),
            color=colors,
        )
        ax.set_xlabel("Command")
        ax.set_ylabel("Times used")
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        ax.tick_params(axis="x", labelrotation=45)
        ax.set_axisbelow(True)
        ax.grid(axis="y", linestyle="-")
        ax.set_axisbelow(True)
        fig.tight_layout()

        with io.BytesIO() as buf:
            fig.savefig(buf, format="png")
            buf.seek(0)
            emby.set_image(url="attachment://plot.png")

            await inter.send(
                embed=emby,
                file=disnake.File(
                    buf,
                    filename="plot.png",
                ),
            )


def setup(bot):
    bot.add_cog(Stats(bot))
