import asyncio

import disnake
import requests
from disnake.ext import commands
from utils.bot import OGIROID


class YouTube(commands.Cog):
    def __init__(self, bot: OGIROID):
        self.bot = bot
        self.get_channel = self.bot.get_channel
        self.youtube_channel_id = self.bot.config.guilds.youtube
        self.youtube_channel_url = f"https://www.youtube.com/channel/{self.youtube_channel_id}"
        self.youtube_api_key = "TODO: GET THIS FROM THE .ENV FILE"
        self.youtube_api_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={self.youtube_channel_id}&maxResults=1&order=date&type=video&key={self.youtube_api_key}"

    # Send a message to the channel when a new video is uploaded
    @commands.Cog.listener()
    async def on_ready(self):
        while True:
            channel = self.get_channel(986722646135824465)
            await self.youtuber(channel)
            await asyncio.sleep(60 * 30)

    async def youtuber(self, channel):
        # Get the latest video from the channel
        response = requests.get(self.youtube_api_url).json()
        video_id = response["items"][0]["id"]["videoId"]
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        video_title = response["items"][0]["snippet"]["title"]
        # Cut the title after a hastag
        if "#" in video_title:
            video_title = video_title.split("#")[0]
        video_thumbnail = response["items"][0]["snippet"]["thumbnails"]["high"]["url"]

        # Send the message
        embed = disnake.Embed(
            title=video_title,
            url=video_url,
            color=0xFF0000,
        )
        YOUTUBE_ROLE = 1015394921756233838
        embed.set_image(url=video_thumbnail)
        embed.set_footer(text="New video uploaded!",
                         icon_url="https://cdn.discordapp.com/attachments/986722646135824465/1032691307803586634/unknown.png")
        await channel.send(f"Hey, Lewis posted a new video! <@&{YOUTUBE_ROLE}>", embed=embed)


def setup(bot):
    bot.add_cog(YouTube(bot))
