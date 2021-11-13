import os

import discord
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()
# TOKEN = os.getenv('DISCORD_TOKEN')
##DON'T COMMIT THIS TO GITHUB PLS
TOKEN = "OTA2NzIyMDY1ODcxMTU1MjAx.YYcwug.P_eNYINfgDakwrGdWP0-ZFhkZPM"
GUILD = "Hackerbois"

bot = commands.Bot(command_prefix='!')

blocked_words = ['ur', 'mum']

@bot.event
async def on_ready():
    #python vars not block scoped in loop
    for guild in bot.guilds:
        if guild.name == GUILD:
            break

    print(
        f'{bot.user} is connected to guild: ' f'{guild.name}'
    )

    members = '\n - '.join([member.name for member in guild.members])
    print(f'Guild Members:\n - {members}')

@bot.command(name='Censored',  help='Lists all censored words')
async def on_message(ctx):
    #bot.user is the bot, prevent against recursive response
    if ctx.author == bot.user:
        return

    await ctx.send(blocked_words)

@bot.command(name='AddWord', help='Allows user to add word to list of censored words')
async def on_message(ctx, word):
    if ctx.author == bot.user:
        return

    if word.lower() in blocked_words:
        await ctx.send("Word already censored")

    else:
        blocked_words.append(word)
        await ctx.send("Successfully added " + word + " to list of censored words")
    
bot.run(TOKEN)