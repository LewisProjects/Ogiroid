from code import interact
from disnake.ext import commands
import disnake
import string
import secrets


class development_cmds(commands.Cog):
    """All commands currently under development!"""
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot

    @commands.slash_command(
        name="password", aliases=["pass"], description="Generate a random password & DM's it!"
    )
    async def password(inter, length: int):
        """Generate a random password & DM's it!"""
        if length > 100:
            length = 100
        password = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length))
        #Checking if DM's are open, if they are, send the password to the user
        if inter.author.dm_channel is None:
            await inter.author.create_dm()
            await inter.author.dm_channel.send(f"Your password is: `{password}`")
            await inter.response.send_message("Your password has been sent!")
        #If DM's are closed, send the password to the channel
        else:
            await inter.response.send(f"Your DM's are closed and due to safety reasons, your password cannot be sent to you. Please open your DM's and try again.")

def setup(bot):
    bot.add_cog(development_cmds(bot))