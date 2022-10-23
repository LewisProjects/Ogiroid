import disnake
import datetime as dt
from disnake.ext import commands, tasks

from utils.bot import OGIROID


class Lewis(commands.Cog, name="Lewis"):

    def __init__(self, bot: OGIROID):
        self.bot = bot
        self.upload_check.start()
        self.youtube_channel_id = "UCWI-ohtRu8eEeDj93hmUsUQ"
        self.youtube_channel_url = f"https://www.youtube.com/channel/{self.youtube_channel_id}"
        self.youtube_api_key = self.bot.config.tokens.yt_api_key
        self.youtube_api_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={self.youtube_channel_id}&maxResults=1&order=date&type=video&key={self.youtube_api_key}"

    def cog_unload(self):
        self.upload_check.cancel()

    @tasks.loop(minutes=30)
    async def upload_check(self):
        if self.youtube_api_key is None:
            print("No YouTube API key found, skipping upload check")
            return
        check_time = dt.datetime.utcnow()
        channel = self.bot.get_channel(self.bot.config.channels.uploads)
        if channel is None:
            return

        response = await self.bot.session.get(self.youtube_api_url)
        response = await response.json()

        video_id = response["items"][0]["id"]["videoId"]
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        # Credits to Simon for the idea and part of the code

        video_release_time = response["items"][0]["snippet"]["publishedAt"]
        year = video_release_time.split("-")[0]
        month = video_release_time.split("-")[1]
        day = video_release_time.split("-")[2].split("T")[0]
        hour = video_release_time.split("T")[1].split(":")[0]
        minute = video_release_time.split("T")[1].split(":")[1]
        second = video_release_time.split("T")[1].split(":")[2].split("Z")[0]
        time = dt.datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))
        if check_time - time < dt.timedelta(minutes=30):
            return await channel.send(f"Hey, Lewis posted a new video! <@&{self.bot.config.roles.yt_announcements}>\n{video_url}")
        else:
            return

def setup(bot):
    bot.add_cog(Lewis(bot))
