from contextlib import asynccontextmanager
import json
import os
import requests
import discord
from dotenv import load_dotenv
from discord.ext import commands

TOKEN = "OTA2NzIyMDY1ODcxMTU1MjAx.YYcwug.ZSmxZBxgW053xXo3h8y-t7umwbQ"
GUILD = "Hackerbois"

load_dotenv()

bot = commands.Bot(command_prefix='!')

blocked_dict = {'ur':'reason1', 'mum':'reason2', "okay": "yayyyyyyyyyyyy:"}

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
    blocked_dict["ur"]
    await ctx.send(blocked_dict)

@bot.command(name='Define', help='Defines the specified word')
async def on_message(ctx, word):
    if ctx.author == bot.user:
        return

    if word.lower() in blocked_dict:
        await ctx.send(blocked_dict[word.lower()])
    

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

@bot.event
async def on_message(msg):
    if msg.author == bot.user:
        return
    
    out_msg = msg.content
    censored_wrds_used = ""
    is_censored = False
    for i,word in enumerate(blocked_dict.keys()):
        if word + " " in msg.content or " " + word in msg.content:
            is_censored = True
            out_msg = out_msg.replace(word, "`" + "*" * len(word) + "`")
            censored_wrds_used += word + ", "
    censored_wrds_used = censored_wrds_used[:-2] # removing last comma
    # delete message with slur
    if is_censored:
        await msg.delete()
        # send message to main channel
        await msg.channel.send(out_msg + "\n" + "**Warning " + msg.author.name + "!** Censored word(s) being used, a private message is sent to you with more information.")
        # send private warning msg describing the slur
        await msg.author.send("Your message to `" + GUILD + "` guild has been blocked since it contains censored word(s) `" +
                                censored_wrds_used + "`\n[DEFINITIONs]\n[REASONs]")
    await bot.process_commands(msg)

@bot.event
async def on_message(msg):
    if msg.author == bot.user:
        return
    
    out_msg = msg.content

    if len(out_msg) < 2 or not(out_msg.startswith("!")):
        return
    
    #print(msg.author.name) #name of person

    if out_msg[1:] in blocked_dict:
        embed=discord.Embed(color=0x00cca3)
        embed.add_field(name=out_msg[1:], value=blocked_dict[out_msg[1:]], inline=False)
        await msg.channel.send(embed=embed)
        #await msg.channel.send(blocked_dict[out_msg[1:]])
    await bot.process_commands(msg)
        
bot.run(TOKEN)
