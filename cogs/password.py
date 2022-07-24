from disnake.ext import commands
import disnake
import string
import secrets


class Password(commands.Cog):
    """Generates a random password"""
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot

    @commands.slash_command(
        name="password", aliases=["pass"], description="Generate a random password & DM's it!"
    )
    async def password(self, inter, length: int):
        """Generate a random password & DM's it!"""
        if length > 100:
            length = 100
        password = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length))
        #Checking if DM's are open, if they are, send the password to the user
        try:
            await inter.author.send(f"Your password is: `{password}`")
            await inter.response.send_message("Your password has been sent!")
        #If DM's are closed, send the password to the channel
        except:
            await inter.response.send_message(f"Your password is: `{password}`", ephemeral=True)

def setup(bot):
    bot.add_cog(Password(bot))
