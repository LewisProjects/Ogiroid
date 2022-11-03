import base64
from io import BytesIO
import time
import disnake
from disnake.ext import commands
from utils.bot import OGIROID


class AI(commands.Cog):
    def __init__(self, bot: OGIROID):
        self.bot = bot

    @commands.slash_command(description="Generates ai art")
    async def ai_art(self, inter: disnake.ApplicationCommandInteraction, text):
        ETA = int(time.time() + 60)
        await inter.send(f"Go grab a coffee this may take a while... ETA: <t:{ETA}:R>", ephemeral=True)
        response = await self.bot.session.post("https://backend.craiyon.com/generate", json={"prompt": text})
        r = await response.json()
        images = r["images"]
        for i in images:
            image = BytesIO(base64.decodebytes(i.encode("utf-8")))
            await inter.send("Have fun", ephemeral=True)
            await inter.send(file=disnake.File(image, "image.png"), ephemeral=True)

        return await inter.delete_original_response()


def setup(bot):
    bot.add_cog(AI(bot))
