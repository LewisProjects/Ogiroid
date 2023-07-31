import io
import os
import random
import textwrap
from io import BytesIO

import disnake
from PIL import Image, ImageDraw, ImageFont
from disnake import ApplicationCommandInteraction
from disnake.ext import commands

from utils.bot import OGIROID


class ImageCommands(commands.Cog, name="Image"):
    """Image Commands!"""

    def __init__(self, bot: OGIROID):
        self.bot = bot

    @commands.slash_command(
        name="trigger",
        brief="Trigger",
        description="For when you're feeling triggered.",
    )
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def triggered(
        self,
        inter: ApplicationCommandInteraction,
        member: disnake.Member = None,
    ):
        """Time to get triggered."""
        if not member:
            member = inter.author
        trigImg = await self.bot.session.get(
            f"https://some-random-api.com/canvas/triggered?avatar={member.display_avatar.url}"
        )
        imageData = io.BytesIO(await trigImg.read())
        await inter.send(file=disnake.File(imageData, "triggered.gif"))

    @commands.slash_command(
        name="sus",
        brief="Sus-Inator4200",
        description="Check if your friend is kinda ***SUS***",
    )
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def amongus(
        self,
        inter: ApplicationCommandInteraction,
        member: disnake.Member = None,
    ):
        """Check if your friends are sus or not"""
        await inter.send("Testing for sus-ness...")
        if not member:
            member = inter.author
        impostor = random.choice(["true", "false"])
        apikey = os.getenv("SRA_API_KEY")
        uri = f"https://some-random-api.com/premium/amongus?username={member.name}&avatar={member.display_avatar.url}&impostor={impostor}&key={apikey}"
        resp = await self.bot.session.get(uri)
        if 300 > resp.status >= 200:
            fp = io.BytesIO(await resp.read())
            await inter.send(file=disnake.File(fp, "amogus.gif"))
        else:
            await inter.send("Couldnt get image :(")

    @commands.slash_command(
        name="invert",
        brief="invert",
        description="Invert the colours of your icon",
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def invert(
        self,
        inter: ApplicationCommandInteraction,
        member: disnake.Member = None,
    ):
        """Invert your profile picture."""
        if not member:
            member = inter.author
        trigImg = await self.bot.session.get(
            f"https://some-random-api.com/canvas/invert/?avatar={member.display_avatar.url}"
        )
        imageData = io.BytesIO(await trigImg.read())
        await inter.send(file=disnake.File(imageData, "invert.png"))

    @commands.slash_command(
        name="pixelate",
        brief="pixelate",
        description="Turn yourself into 144p!",
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def pixelate(
        self,
        inter: ApplicationCommandInteraction,
        member: disnake.Member = None,
    ):
        """Turn yourself into pixels"""
        if not member:
            member = inter.author
        trigImg = await self.bot.session.get(
            f"https://some-random-api.com/canvas/pixelate/?avatar={member.display_avatar.url}"
        )
        imageData = io.BytesIO(await trigImg.read())
        await inter.send(file=disnake.File(imageData, "pixelate.png"))

    @commands.slash_command(
        name="jail", brief="jail", description="Go to jail!"
    )
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def jail(
        self,
        inter: ApplicationCommandInteraction,
        member: disnake.Member = None,
    ):
        """Go to horny jail"""
        if not member:
            member = inter.author

        trigImg = await self.bot.session.get(
            f"https://some-random-api.com/canvas/jail?avatar={member.display_avatar.url}"
        )
        imageData = io.BytesIO(await trigImg.read())
        await inter.send(file=disnake.File(imageData, "jail.png"))

    @commands.slash_command(
        name="urltoqr", description="Converts a URL to a QR code."
    )
    async def urltoqr(
        self, inter: ApplicationCommandInteraction, url: str, size: int
    ):
        url = url.replace("http://", "").replace("https://", "")
        qr = f"https://api.qrserver.com/v1/create-qr-code/?size={size}x{size}&data={url}"
        embed = disnake.Embed(title=f"URL created for: {url}", color=0xFFFFFF)
        embed.set_image(url=qr)
        embed.set_footer(text=f"Requested by: {inter.author.name}")
        return await inter.send(embed=embed)

    @staticmethod
    def draw_multiple_line_text(
        image, text, font, text_color, text_start_height
    ):
        draw = ImageDraw.Draw(image)
        image_width, image_height = image.size
        y_text = text_start_height
        lines = textwrap.wrap(text, width=45)
        for line in lines:
            nothing1, nothing2, line_width, line_height = font.getbbox(line)
            # draw shadow on text
            draw.text(
                ((image_width - line_width) / 2 + 2, y_text + 2),
                line,
                font=font,
                fill=(0, 0, 0),
            )
            draw.text(
                ((image_width - line_width) / 2, y_text),
                line,
                font=font,
                fill=text_color,
            )
            y_text += line_height
        # Return the bottom pixel of the text
        return y_text

    # Command to get information about a Quote user
    @commands.slash_command(
        name="quote",
        description="Generates an image with a quote and random background",
    )
    async def quote(self, inter):
        """Generates an image with a quote and random background"""
        await inter.response.defer()
        # Use api.quotable.io/random to get a random quote
        main = await self.bot.session.get("https://api.quotable.io/random")
        data = await main.json()
        quote = data["content"]
        author = data["author"]

        # Use unsplash.com to get a random image
        resolution = "1080x1080"
        response = await self.bot.session.get(
            f"https://source.unsplash.com/random/{resolution}"
        )
        image_bytes = io.BytesIO(await response.read())
        image = Image.open(image_bytes)

        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype("utils/data/Roboto-Italic.ttf", 50)
        font2 = ImageFont.truetype("utils/data/Roboto-Bold.ttf", 50)
        if len(quote) > 350:
            text_start_height = (
                image.height - font.getbbox(quote)[3]
            ) / 2 - 500
        elif len(quote) > 250:
            text_start_height = (
                image.height - font.getbbox(quote)[3]
            ) / 2 - 200
        elif len(quote) > 150:
            text_start_height = (
                image.height - font.getbbox(quote)[3]
            ) / 2 - 50
        else:
            text_start_height = (image.height - font.getbbox(quote)[3]) / 2
        end = self.draw_multiple_line_text(
            image,
            quote,
            font,
            text_color=(255, 255, 255),
            text_start_height=text_start_height,
        )
        # Draw the author shadow
        draw.text(
            ((image.width - font2.getbbox(author)[2]) / 2 + 2, end + 50),
            author,
            font=font2,
            fill=(0, 0, 0),
        )
        # Draw the author
        draw.text(
            ((image.width - font2.getbbox(author)[2]) / 2, end + 50),
            author,
            font=font2,
            fill=(255, 255, 255),
        )
        with BytesIO() as image_binary:
            image.save(image_binary, "PNG")
            image_binary.seek(0)
            await inter.send(
                file=disnake.File(fp=image_binary, filename="image.png")
            )


def setup(bot):
    bot.add_cog(ImageCommands(bot))
