from contextlib import asynccontextmanager
import json
import os
import requests
import discord
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()



bot = commands.Bot(command_prefix='!')

blocked_dict = {'ur':'reason1', 'mum':'reason2'}

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

    await ctx.send(blocked_dict)

@bot.command(name='AddWord', help='Allows user to add word to list of censored words')
async def on_message(ctx, word):
    if ctx.author == bot.user:
        return

    if word.lower() in blocked_dict:
        await ctx.send("Word already censored")

    else:
        # get definition from dictionaryAPI & send message
        definition = requests.get("https://api.dictionaryapi.dev/api/v2/entries/en/" + word)
        await ctx.send(definition.json()[0]["meanings"][0]["definitions"][0]["definition"])
        #defn = definition.json()
        await ctx.send(definition.json())
        # ['meanings'][0]['definitions'][0]['definition']

        # prompt user to why this term is offensive and who it offends
        await ctx.send("What is the term " + word + " offensive and who does it target?")

        # wait for user to answer

        def check(m):
            return len(m.content)>0 and m.channel == ctx.channel

        msg = await bot.wait_for("message", check=check)

        # wait for a few thumbs up emojis before adding it
        # Should it timeout or non?
        # Error: if you try to add another word while one is waiting for emoji
        # if that second word gets emoji, both get added to list
        await ctx.send('React with a 👍 to add [' + word + '] to the censored list.')

        def check(reaction, user):
            return str(reaction.emoji) == '👍'
        #try:
        reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)
        await ctx.send('👍')
        #except asynccontextmanager.TimeoutError:
        #    await ctx.send('👎')
        #else:
        #    await ctx.send('👍')
        

        # adds word to list and states why
        blocked_dict[word] = msg.content
        await ctx.send("Successfully added [" + word + "] to list of censored words because [" + blocked_dict[word] +"]")
    
bot.run(TOKEN)