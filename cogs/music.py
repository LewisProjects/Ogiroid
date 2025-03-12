import disnake
from disnake.ext import commands
import lavalink
import re

# Regex to check if query is a URL
URL_REGEX = re.compile(r'https?://(?:www\.)?.+')

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lavalink = lavalink.Client(bot.user.id)
        # Add your Lavalink node details below
        self.lavalink.add_node('localhost', 2333, 'youshallnotpass', 'us', 'default-node')
        self.bot.add_listener(self.lavalink.voice_update_handler, 'on_socket_response')
        self.lavalink.add_event_hook(self.track_hook)
        self.skip_votes = {}  # Dictionary to track vote-skip per guild
        self.last_track_title = None  # Store the last track title for auto-play

    @commands.Cog.listener()
    async def on_ready(self):
        print("🎵 Music system is ready!")

    async def track_hook(self, event):
        """Handle track events: update now playing, reset vote skip,
        and auto-play a related track when the queue ends."""
        if isinstance(event, lavalink.events.TrackStartEvent):
            self.last_track_title = event.track.info['title']
            await event.player.text_channel.send(f"🎶 Now playing: **{event.track.info['title']}**")
            # Reset vote-skip list when a new track starts
            self.skip_votes[event.player.guild_id] = []
        elif isinstance(event, lavalink.events.QueueEndEvent):
            await event.player.text_channel.send("🎵 Queue ended! Attempting auto-play of a related track...")
            if self.last_track_title:
                # Simple auto-play: search YouTube with the last track's title plus a modifier
                query = f"ytsearch:{self.last_track_title} remix"
                results = await self.lavalink.get_tracks(query)
                if results and results['tracks']:
                    track = results['tracks'][0]
                    event.player.add(requester=event.player.text_channel.id, track=track)
                    await event.player.play()
                    await event.player.text_channel.send(f"🎶 Auto-playing: **{track['info']['title']}**")
                else:
                    await event.player.text_channel.send("❌ No related tracks found for auto-play.")

    @commands.command(name="join")
    async def join_voice(self, ctx):
        """Joins the voice channel."""
        if ctx.author.voice is None:
            return await ctx.send("❌ You must be in a voice channel!")
        channel = ctx.author.voice.channel
        await ctx.guild.change_voice_state(channel=channel)
        await ctx.send(f"✅ Joined {channel.name}!")

    @commands.command(name="play")
    async def play_song(self, ctx, *, query: str):
        """Plays a song from YouTube or Spotify."""
        player = self.lavalink.player_manager.create(ctx.guild.id, endpoint=str(ctx.guild.region))
        if not ctx.voice_client:
            await ctx.invoke(self.join_voice)

        search_query = query if URL_REGEX.match(query) else f"ytsearch:{query}"
        results = await self.lavalink.get_tracks(search_query)
        if not results or not results['tracks']:
            return await ctx.send("❌ No results found.")

        track = results['tracks'][0]
        player.add(requester=ctx.author.id, track=track)
        await ctx.send(f"🎶 Added **{track['info']['title']}** to the queue!")
        if not player.is_playing:
            await player.play()

    @commands.command(name="pause")
    async def pause(self, ctx):
        """Pauses the current song."""
        player = self.lavalink.player_manager.get(ctx.guild.id)
        if player.is_playing:
            await player.set_pause(True)
            await ctx.send("⏸️ Music paused.")

    @commands.command(name="resume")
    async def resume(self, ctx):
        """Resumes the song."""
        player = self.lavalink.player_manager.get(ctx.guild.id)
        if player.paused:
            await player.set_pause(False)
            await ctx.send("▶️ Music resumed.")

    @commands.command(name="skip")
    async def skip(self, ctx):
        """Skips the current song immediately."""
        player = self.lavalink.player_manager.get(ctx.guild.id)
        if not player.is_playing:
            return await ctx.send("❌ No music is playing!")
        await player.skip()
        await ctx.send("⏭️ Skipped the song.")

    @commands.command(name="voteskip")
    async def vote_skip(self, ctx):
        """Starts a vote to skip the current track."""
        player = self.lavalink.player_manager.get(ctx.guild.id)
        if not player.is_playing:
            return await ctx.send("❌ No music is playing!")
        
        guild_id = ctx.guild.id
        if guild_id not in self.skip_votes:
            self.skip_votes[guild_id] = []

        # Prevent duplicate votes
        if ctx.author.id in self.skip_votes[guild_id]:
            return await ctx.send("⚠️ You have already voted to skip this track.")

        self.skip_votes[guild_id].append(ctx.author.id)

        # Determine required votes (more than half of non-bot members in voice channel)
        voice_channel = ctx.author.voice.channel if ctx.author.voice else None
        if not voice_channel:
            return await ctx.send("❌ You must be in a voice channel to vote skip.")
        total_members = len([member for member in voice_channel.members if not member.bot])
        votes = len(self.skip_votes[guild_id])
        required_votes = total_members // 2 + 1

        await ctx.send(f"🗳️ {ctx.author.mention} voted to skip. [{votes}/{required_votes} votes]")
        if votes >= required_votes:
            await player.skip()
            await ctx.send("⏭️ Vote skip passed, skipping track.")

    @commands.command(name="stop")
    async def stop(self, ctx):
        """Stops the music and clears the queue."""
        player = self.lavalink.player_manager.get(ctx.guild.id)
        player.queue.clear()
        await player.stop()
        await ctx.send("🛑 Stopped music and cleared the queue.")

    @commands.command(name="queue")
    async def show_queue(self, ctx):
        """Shows the current music queue."""
        player = self.lavalink.player_manager.get(ctx.guild.id)
        if not player.queue:
            return await ctx.send("❌ The queue is empty!")
        queue_list = "\n".join([f"{idx+1}. {track['info']['title']}" for idx, track in enumerate(player.queue)])
        await ctx.send(f"🎶 **Queue:**\n{queue_list}")

    @commands.command(name="volume")
    async def set_volume(self, ctx, volume: int):
        """Sets the music volume (0-100)."""
        if volume < 0 or volume > 100:
            return await ctx.send("❌ Volume must be between 0 and 100.")
        player = self.lavalink.player_manager.get(ctx.guild.id)
        await player.set_volume(volume)
        await ctx.send(f"🔊 Volume set to {volume}%")

    @commands.command(name="bassboost")
    async def bassboost(self, ctx, mode: str):
        """Toggles bass boost. Use 'on' or 'off'."""
        player = self.lavalink.player_manager.get(ctx.guild.id)
        mode = mode.lower()
        if mode == "on":
            # Apply bass boost by increasing gain for the lower frequency bands
            bands = [{"band": i, "gain": 0.3} for i in range(3)] + [{"band": i, "gain": 0.0} for i in range(3, 15)]
            await player.set_eq(bands)
            await ctx.send("🎚️ Bass boost enabled.")
        elif mode == "off":
            # Reset equalizer settings
            bands = [{"band": i, "gain": 0.0} for i in range(15)]
            await player.set_eq(bands)
            await ctx.send("🎚️ Bass boost disabled.")
        else:
            await ctx.send("❌ Invalid mode. Use 'on' or 'off'.")

def setup(bot):
    bot.add_cog(Music(bot))
