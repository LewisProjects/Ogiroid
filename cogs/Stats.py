import disnake
from disnake.ext import commands, tasks

from utils.bot import OGIROID


class Stats(commands.Cog):
    def __init__(self, bot: OGIROID):
        self.bot = bot
        self.update_stats.start()

    def cog_unload(self):
        self.update_stats.cancel()

    @tasks.loop(hours=1)
    async def update_stats(self):
        # add command usage to db
        commands_ran = self.bot.commands_ran
        total_commands_ran = self.bot.total_commands_ran

        for guild_id, guild_commands_ran in commands_ran.items():
            for command, count in guild_commands_ran.items():
                await self.bot.db.execute(
                    "INSERT INTO commands (guild_id, command, command_used) VALUES ($1, $2, $3) ON CONFLICT (guild_id, command) DO UPDATE SET command_used = commands.command_used + $3;",
                    guild_id,
                    command,
                    count,
                )

        for guild_id, count in total_commands_ran.items():
            await self.bot.db.execute(
                "INSERT INTO total_commands (guild_id, total_commands_used) VALUES ($1, $2) ON CONFLICT (guild_id) DO UPDATE SET total_commands_used = total_commands.total_commands_used + $2;",
                guild_id,
                count,
            )

        # reset command usage
        self.bot.commands_ran = {}
        self.bot.total_commands_ran = {}

    @commands.slash_command(description="Stats about the commands that have been ran")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def cmdstats(self, inter):
        await inter.response.defer()
        cmdsran = await self.bot.db.fetch(
            "SELECT command, command_used FROM commands WHERE guild_id = $1 ORDER BY command_used DESC LIMIT 10;",
            inter.guild.id,
        )
        cmdsran = dict(cmdsran)

        total_commands_ran = await self.bot.db.fetchval(
            "SELECT total_commands_used FROM total_commands WHERE guild_id = $1;",
            inter.guild.id,
        )
        sortdict = dict(sorted(cmdsran.items(), key=lambda x: x[1], reverse=True))
        value_iterator = iter(sortdict.values())
        key_iterator = iter(sortdict.keys())
        emby = disnake.Embed(
            title=f"{self.bot.user.display_name} command Stats",
            description=f"{total_commands_ran} Commands ran in total.\n",
            color=self.bot.config.colors.white,
        )
        if len(cmdsran) == 0:
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
