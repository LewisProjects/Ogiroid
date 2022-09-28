import os
import textwrap

import disnake
import requests
from PIL import Image, ImageDraw, ImageFont
from disnake.ext import commands
from utils.bot import OGIROID


class Quote(commands.Cog):
    """Commands involving Quote! :)"""

    def __init__(self, bot: OGIROID):
        self.bot = bot

    # Command to get information about a Quote user
    @commands.slash_command(name="quote", description="Generates an image with a quote and random background")
    async def quote(self, ctx, category: str):
        def draw_multiple_line_text(image, text, font, text_color, text_start_height):
            draw = ImageDraw.Draw(image)
            image_width, image_height = image.size
            y_text = text_start_height
            lines = textwrap.wrap(text, width=45)
            for line in lines:
                nothing1, nothing2, line_width, line_height = font.getbbox(line)
                # draw shadow on text
                draw.text(((image_width - line_width) / 2 + 2, y_text + 2),
                          line, font=font, fill=(0, 0, 0))
                draw.text(((image_width - line_width) / 2, y_text),
                          line, font=font, fill=text_color)
                y_text += line_height
            # Return the bottom pixel of the text
            return y_text

        """Generates an image with a quote and random background"""
        await ctx.respond("Getting quote...")
        # Use api.quotable.io/random to get a random quote
        main = requests.get('https://api.quotable.io/random')
        data = main.json()
        quote = data['content']
        author = data['author']

        await ctx.respond("Getting background image...")
        # Use unsplash.com to get a random image
        resolution = '1080x1080'
        image = Image.open(requests.get(f'https://source.unsplash.com/random/{resolution}?{category}', stream=True).raw)
        image = Image.open(requests.get(f'https://source.unsplash.com/random/{resolution}?{category}',
                                        stream=True).raw)

        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype('fonts/Roboto-Italic.ttf', 150)
        font2 = ImageFont.truetype('fonts/Roboto-Bold.ttf', 150)
        if len(quote) > 350:
            text_start_height = (image.height - font.getbbox(quote)[3]) / 2 - 500
        elif len(quote) > 250:
            text_start_height = (image.height - font.getbbox(quote)[3]) / 2 - 200
        elif len(quote) > 150:
            text_start_height = (image.height - font.getbbox(quote)[3]) / 2 - 50
        else:
            text_start_height = (image.height - font.getbbox(quote)[3]) / 2
        end = draw_multiple_line_text(image, quote, font, text_color=(255, 255, 255),
                                      text_start_height=text_start_height)
        # Draw the author shadow
        draw.text(((image.width - font2.getbbox(author)[2]) / 2 + 2, end + 50),
                  author, font=font2, fill=(0, 0, 0))
        # Draw the author
        draw.text(((image.width - font2.getbbox(author)[2]) / 2, end + 50), author, font=font2, fill=(255, 255, 255))
        image.save('temp.png')
        await ctx.respond("Sending image...")
        await ctx.send(file=disnake.File('temp.png'))
        os.remove('temp.png')


def setup(bot):
    bot.add_cog(Quote(bot))
