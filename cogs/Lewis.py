import disnake
from disnake.ext import commands, tasks

from utils.bot import OGIROID


class Lewis(commands.Cog, name="Lewis"):

    def __init__(self, bot: OGIROID):
        self.bot = bot
        self.upload_check.start()
        self.youtube_channel_id = "UCWI-ohtRu8eEeDj93hmUsUQ"
        self.youtube_channel_url = f"https://www.youtube.com/channel/{self.youtube_channel_id}"
        self.youtube_api_key = ""
        self.youtube_api_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={self.youtube_channel_id}&maxResults=1&order=date&type=video&key={self.youtube_api_key}"

    def cog_unload(self):
        self.upload_check.cancel()

    @tasks.loop(seconds=60)
    async def upload_check(self):
        response = await self.bot.session.get(self.youtube_api_url)
        response = await response.json()
        channel = self.bot.get_channel(self.bot.config.channels.uploads)
        if channel is None:
            return
        video_id = response["items"][0]["id"]["videoId"]
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        # Credits to Simon for the idea and code

        return await channel.send(f"Hey, Lewis posted a new video! <@&{self.bot.config.roles.yt_announcements}>\n{video_url}")


def setup(bot):
    bot.add_cog(Lewis(bot))
