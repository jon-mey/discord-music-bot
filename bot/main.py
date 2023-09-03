import logging
import discord
from discord.ext import commands

from os import getenv
from help_cog import help_cog
from music_cog import music_cog

async def setup():
    await bot.add_cog(help_cog(bot))
    await bot.add_cog(music_cog(bot))

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='/', intents=intents)
logging.basicConfig(level=logging.INFO)

bot.remove_command('help') # remove the default help command so that we can write out own
bot.setup_hook = setup
bot.run(getenv("DISCORD_TOKEN"))