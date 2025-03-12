import disnake
from disnake.ext import commands
import json
import os

WARNINGS_FILE = "warnings.json"

def load_warnings():
    if not os.path.exists(WARNINGS_FILE):
        return {}
    with open(WARNINGS_FILE, "r") as f:
        return json.load(f)

def save_warnings(warnings):
    with open(WARNINGS_FILE, "w") as f:
        json.dump(warnings, f, indent=4)

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.warnings = load_warnings()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        banned_words = ["suicide"]

        # Check if the message contains banned words
        if any(word in message.content.lower() for word in banned_words):
            await message.delete()
            user_id = str(message.author.id)

            # Track warnings
            if user_id not in self.warnings:
                self.warnings[user_id] = 0
            self.warnings[user_id] += 1
            save_warnings(self.warnings)

            # Send a warning message
            warning_count = self.warnings[user_id]
            await message.channel.send(f"{message.author.mention}, you have been warned for using inappropriate language. Total warnings: {warning_count}/3.")

            # Take action after 3 warnings
            if warning_count >= 3:
                await message.author.timeout(duration=60*5, reason="Excessive inappropriate language")
                await message.channel.send(f"{message.author.mention} has been temporarily muted for 5 minutes due to multiple warnings.")

    # Command to check a user's warnings
    @commands.command(name="warnings")
    @commands.has_permissions(manage_messages=True)
    async def check_warnings(self, ctx, member: disnake.Member):
        user_id = str(member.id)
        warning_count = self.warnings.get(user_id, 0)
        await ctx.send(f"{member.mention} has {warning_count} warnings.")

    # Command to clear a user's warnings
    @commands.command(name="clearwarnings")
    @commands.has_permissions(manage_messages=True)
    async def clear_warnings(self, ctx, member: disnake.Member):
        user_id = str(member.id)
        if user_id in self.warnings:
            del self.warnings[user_id]
            save_warnings(self.warnings)
            await ctx.send(f"Cleared all warnings for {member.mention}.")
        else:
            await ctx.send(f"{member.mention} has no warnings.")

# Setup function to add the cog
def setup(bot):
    bot.add_cog(Moderation(bot))
