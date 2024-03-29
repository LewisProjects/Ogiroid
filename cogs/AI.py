import base64
import time
from io import BytesIO
from better_profanity import profanity
import disnake
from disnake.ext import commands

from utils.bot import OGIROID


class AI(commands.Cog):
    def __init__(self, bot: OGIROID):
        self.bot = bot

    @commands.slash_command(description="Generates ai art")
    async def ai_art(self, inter: disnake.ApplicationCommandInteraction, text: str):
        if profanity.contains_profanity(text):
            return await inter.send(f"NSFW requests are not allowed!", ephemeral=True)
        if "bot" in inter.channel.name or "command" in inter.channel.name:
            hidden = False
        else:
            hidden = True
        ETA = int(time.time() + 15)
        await inter.send(
            f"This might take a bit of time... ETA: <t:{ETA}:R>",
            ephemeral=hidden,
        )
        response = await self.bot.session.post(
            "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0",
            json={"inputs": text},
            headers={"Authorization": f"Bearer {self.bot.config.tokens.huggingface}"},
        )
        images = [disnake.File(BytesIO(await response.read()), "image.png")]

        await inter.edit_original_response(files=images, content="Here you go!")


def setup(bot):
    bot.add_cog(AI(bot))
