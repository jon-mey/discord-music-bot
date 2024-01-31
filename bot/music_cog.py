import asyncio
import discord

from discord.ext import commands
from discord.ext import tasks
from yt_dlp import YoutubeDL
from azure.identity import ClientSecretCredential
from azure.mgmt.containerinstance import ContainerInstanceManagementClient
from os import getenv

azure_resource_group = getenv("AZURE_RESOURCE_GROUP")
azure_container_name = getenv("AZURE_CONTAINER_NAME")
azure_tenant_id = getenv("AZURE_TENANT_ID")
azure_subscription_id = getenv("AZURE_SUBSCRIPTION_ID")
azure_client_id = getenv("AZURE_CLIENT_ID")
azure_client_secret = getenv("AZURE_CLIENT_SECRET")

request_command_name = getenv("DISCORD_REQUEST_COMMAND_NAME")
text_channel_id = int(getenv("DISCORD_CHANNEL_ID"))
max_inactivity_time_minutes = 30

class music_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.audio = None
        self.music_queue = [] # 2d array containing {song:, channel:}
        self.ytdlp_options = {'format': 'bestaudio', 'verbose': True}
        self.voice_client: discord.VoiceClient = None
        self.text_channel: discord.TextChannel = None
        self.inactivity_time = 0
        self.stop_due_to_inactivity = False
        
        self.check_activity.start()
    
    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            for channel in guild.text_channels:
                if channel.id == text_channel_id:
                    self.text_channel = channel
        
        await self.text_channel.send("Greetings. Type /help to show all available commands.")      

    def cog_unload(self):
        self.check_activity.cancel()

    @tasks.loop(seconds=1.0)
    async def check_activity(self):
        if self.voice_client != None and self.voice_client.is_playing():
            self.inactivity_time = 0
        else:
            self.inactivity_time += 1
        
        if self.inactivity_time / 60 > max_inactivity_time_minutes:
            print('Inactivity threshold reached, stopping container.')            
            self.stop_due_to_inactivity = True

            credential = ClientSecretCredential(
                tenant_id=azure_tenant_id, 
                client_id=azure_client_id, 
                client_secret=azure_client_secret)

            aci_client = ContainerInstanceManagementClient(
                credential=credential,
                subscription_id=azure_subscription_id)
    
            aci_client.container_groups.stop(azure_resource_group, azure_container_name)
            
            self.check_activity.cancel()
            
    @check_activity.after_loop
    async def after_check_activity(self):
        print('Check activity loop ended')
        
        if self.text_channel != None and self.stop_due_to_inactivity:
            await self.text_channel.send("Stopping after %d minutes of inactivity. Use /%s to request re-join." % (max_inactivity_time_minutes, request_command_name))

    def search_yt(self, url):
        with YoutubeDL(self.ytdlp_options) as ydl:
            try: 
                info = ydl.extract_info(url, download=False)
                info = ydl.sanitize_info(info)
            except Exception: 
                return False
        
        return {'url': info['url'], 'title': info['title'], 'duration': info['duration']}

    def play_next_item(self):
        if self.audio != None:
            self.audio.cleanup()

        data = self.music_queue.pop(0)
        self.audio = discord.FFmpegOpusAudio(source=data['song']['url'], before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', options=data['ffmpeg_options'])
        self.voice_client.play(self.audio, after=lambda error: asyncio.run_coroutine_threadsafe(self.play_next(), self.bot.loop))

    async def play_next(self):
        if len(self.music_queue) > 0:
            self.play_next_item()
        else:
            await self.voice_client.disconnect()

    async def start_playing(self, ctx):
        channel = self.music_queue[0]['channel']
            
        if self.voice_client == None or self.voice_client.is_connected() == False:
            self.voice_client = await channel.connect()
            await ctx.guild.change_voice_state(channel=channel, self_mute=False, self_deaf=True)
                
            if self.voice_client == None:
                await ctx.send('Could not connect to the voice channel.')
                return
        else:
            await self.voice_client.move_to(channel)
            
        self.play_next_item()

    @commands.command(name="play", aliases=["p", "playing"], help="Plays a given song from youtube")
    async def play(self, ctx, *args):
        voice_channel = ctx.author.voice.channel
        
        if voice_channel is None:
            await ctx.send('You must be in a voice channel.')
            return
      
        url_part = args[0]
        url_part = url_part.split("?si")[0]
        url_part = url_part.split("&list")[0]

        start, end, tempo, pitch = None, None, None, None

        # Parsing the components to extract values
        for i in range(len(args)):
            if args[i] == "-start":
                start = args[i + 1]
            elif args[i] == "-end":
                end = args[i + 1]
            elif args[i] == "-tempo":
                tempo = args[i + 1]
            elif args[i] == "-pitch":
                pitch = args[i + 1]

        await ctx.send('Downloading metadata for <%s>...' % url_part)
        clip = self.search_yt(url_part)

        if type(clip) == type(True):
            await ctx.send('Error while downloading song metadata.')
        else:
            duration = clip['duration']
            minutes = duration // 60
            seconds = duration % 60
            data = {'song': clip, 'channel': voice_channel}
            ffmpeg_options = '-vn'

            if start:
                ffmpeg_options += f" -ss {start}"
            if end:
                ffmpeg_options += f" -to {end}"

            ffmpeg_filters = []
            if tempo:
                ffmpeg_filters.append(f"tempo={tempo}")
            if pitch:
                ffmpeg_filters.append(f"pitch={pitch}")

            filter_string = ",".join(ffmpeg_filters)

            if filter_string:
                ffmpeg_options += f' -af "rubberband={filter_string}"'

            data['ffmpeg_options'] = ffmpeg_options

            await ctx.send(f"\"{clip['title']}\" ({minutes:02d}:{seconds:02d}) added to the queue.")
            self.music_queue.append(data)
                    
            if self.voice_client == None or self.voice_client.is_playing() == False:
                await self.start_playing(ctx)

    @commands.command(name="pause", help="Pauses the current song")
    async def pause(self, ctx, *args):
        if self.voice_client == None:
            return

        if self.voice_client.is_playing():
            self.voice_client.pause()
        elif self.voice_client.is_paused():
            self.voice_client.resume()

    @commands.command(name = "resume", aliases=["r"], help="Resumes playing")
    async def resume(self, ctx, *args):
        if self.voice_client == None:
            return
        
        if self.voice_client.is_paused():
            self.voice_client.resume()

    @commands.command(name="skip", aliases=["s"], help="Skips the current song")
    async def skip(self, ctx):
        if self.voice_client != None:
            if len(self.music_queue) > 0:
                await ctx.send('Skipping...')

            self.voice_client.pause()     
            await self.play_next()

    @commands.command(name="queue", aliases=["q"], help="Shows the current songs in queue")
    async def queue(self, ctx):
        retval = ""
        for i in range(0, len(self.music_queue)):
            # display a max of 5 songs in the current queue
            if (i > 4): break
            retval += '%d. %s\n' % ((i + 1), self.music_queue[i]['song']['title'])

        if retval != "":
            await ctx.send(retval)
        else:
            await ctx.send('No music in queue.')

    @commands.command(name="clear", aliases=["c", "bin"], help="Stops the music and clears the queue")
    async def clear(self, ctx):
        if self.voice_client != None and self.voice_client.is_playing():
            self.voice_client.stop()
            
        self.music_queue = []
        await ctx.send('Queue cleared')

    @commands.command(name="leave", aliases=["disconnect", "l", "d"], help="Removes the bot from the voice channel")
    async def leave(self, ctx):
        await self.voice_client.disconnect()
