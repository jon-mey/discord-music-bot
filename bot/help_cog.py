from discord.ext import commands

class help_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.help_message = """
```
General commands:
/help - shows all the available commands
/play <link> - plays the given audio clip, supports youtube links. Possible options: (-start, -end, -tempo, -pitch, -repeat, -reverse)
/queue - shows the current music queue
/skip - skips the current song being played
/clear - stops the music and clears the queue
/leave - disconnects the bot from the voice channel
/pause - pauses the current song being played or resumes if already paused
/resume - resumes playing the current song
```
"""
        self.text_channel_list = []

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    self.text_channel_list.append(channel)
                
        print(self.text_channel_list)
        # await self.send_to_all(self.help_message)        

    @commands.command(name="help", help="Displays all the available commands")
    async def help(self, ctx):
        await ctx.send(self.help_message)

    async def send_to_all(self, msg):
        for text_channel in self.text_channel_list:
            await text_channel.send(msg)