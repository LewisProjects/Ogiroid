import secrets
import string

from disnake.ext import commands

from utils.bot import OGIROID


class Password(commands.Cog):
    """Generates a random password"""

    def __init__(self, bot: OGIROID):
        self.bot = bot

    @commands.slash_command(
        name="password",
        aliases=["pass"],
        description="Generates a random password & DM's it!",
    )
    async def password(self, inter, length: int):
        """Generate a random password & DMs it!"""
        if length > 100:
            length = 100
        password = "".join(
            secrets.choice(string.ascii_letters + string.digits)
            for _ in range(length)
        )
        # try to DM if fails send the password to the channel
        try:
            await inter.author.send(f"Your password is: ||{password}||")
            await inter.response.send_message("Your password has been sent!")
        # If DMs are closed, send the password to the channel
        except:
            await inter.response.send_message(
                f"Your password is: ||{password}||", ephemeral=True
            )


def setup(bot):
    bot.add_cog(Password(bot))
