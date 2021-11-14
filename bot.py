from contextlib import asynccontextmanager
import json
import os
import requests
import discord
from dotenv import load_dotenv
from discord.ext import commands
from google.cloud import language_v1

load_dotenv()

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r"apikey.json"
GUILD = "Hackerbois"

bot = commands.Bot(command_prefix='!')
client = language_v1.LanguageServiceClient()

sensitive_options = ['/Sensitive Subjects', '/Social Issues & Advocacy/Discrimination & Identity Relations', '/Health/Substance Abuse',
'/Social Issues & Advocacy/Discrimination & Identity Relations', '/Social Issues & Advocacy/Work & Labor Issues', '/Social Issues & Advocacy/Human Rights & Liberties']

#Chosen categories from above options
sensitive_categories = []
blocked_dict = {'ur':'reason1', 'mum':'reason2'}

#Ids of messages containing sensitive_options, for gathering reactions
sensitive_ids = []

#Create sensitive_topics channel
@bot.event
async def on_ready():
    await bot.wait_until_ready()

    for guild in bot.guilds:    
        existing_channel = discord.utils.get(guild.channels, name='sensitive-topics')
        if not existing_channel:
            await guild.create_text_channel('sensitive-topics')
            channel = discord.utils.get(guild.channels, name='sensitive-topics')
            await channel.send("Sensitive topics are topics for which you will get content warnings server-wide.\
            They aren't censored by default, but users can choose to avoid them if they wish.\n React with a 👍! Any topics with more than 50 percent of server-wide votes will be considered sensitive.")
            for option in sensitive_options:
                msg = await channel.send(option)
                sensitive_ids.append(msg.id)

#Check sensitive topics if reaction addee
@bot.event
async def on_raw_reaction_add(payload):

    if payload.message_id in sensitive_ids and payload.emoji.name == '👍':
        channel = bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        reaction = discord.utils.get(message.reactions, emoji=payload.emoji.name)

        if reaction and reaction.count >= len(bot.get_guild(payload.guild_id).members)/2 and message.content not in sensitive_categories:
            sensitive_categories.append(message.content)

#Check sensitive topics if reaction removed
@bot.event
async def on_raw_reaction_remove(payload):

    if payload.message_id in sensitive_ids and payload.emoji.name == '👍':
        channel = bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        reaction = discord.utils.get(message.reactions, emoji=payload.emoji.name)

        if reaction and reaction.count < len(bot.get_guild(payload.guild_id).members)/2 and message.content in sensitive_categories:
            sensitive_categories.pop(message.content)



@bot.event
async def on_member_join(member):
    await member.create_dm()
    await member.dm_channel.send(
        f'Hi {member.name}, welcome to the ' f'{bot.guilds[0].name} server!\nI am HackerBot, here to make sure that this server is a safe space for you. Type !help to see what I can do.'
    )


@bot.command(name='Censored',  help='Lists all censored words')
async def censored(ctx):
    #bot.user is the bot, prevent against recursive response
    if ctx.author == bot.user:
        return

    await ctx.send(blocked_dict)

@bot.command(name='AddWord', help='Allows user to add word to list of censored words')
async def add(ctx, word):
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

@bot.command(name='Sensitive', help='Lists all sensitive topics (content warnings, not censored)')
async def sensitive(ctx):
    #bot.user is the bot, prevent against recursive response
    if ctx.author == bot.user:
        return

    embed=discord.Embed(color=0x00cca3)
    embed.add_field(name="Sensitive Topics", value= ', '.join(sensitive_categories), inline=False)
    await ctx.send(embed=embed)

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

#Sentiment analysis
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    document = language_v1.Document(
        content=message.content, type_=language_v1.Document.Type.PLAIN_TEXT,
    )
    sentiment = client.analyze_sentiment(
        request={"document": document}
    ).document_sentiment

    #Content classification requires 20 tokens, repeat message until that is reached
    content = message.content
    words = content.split()
    while(len(words) < 20):
        content = content + " " + content
        words = content.split()

    document = {"content": content, "type_": language_v1.Document.Type.PLAIN_TEXT}
   
    response = client.classify_text(request = {'document': document})

    #Very negative, regardless of topic, should be banned
    if(sentiment.score <=-0.89 and sentiment.magnitude >=0.89):
        embed=discord.Embed(color=0x00cca3)
        embed.add_field(name="Warning: I have detected the use of negative/offensive language.", value="You wrote: " + message.content, inline=False)
        await message.author.send(embed=embed)
        # await message.author.send("Warning: I have detected the use of negative/offensive language." + "\n" + "You wrote: " + message.content)

    # #Clearly about sensitive topic, should be banned
    # for category in response.categories:
    #     if category.name in sensitive_categories and category.confidence >= 0.89:
    #         await message.author.send("Warning: I have detected the use of negative/offensive language." + "\n" + "You wrote: " + message.content)

    #Both negative and sensitive
    sensitive = False
    categories = []
    if(sentiment.score <= -0.7 and sentiment.magnitude >= 0.8):
        for category in response.categories:
            if category.name in sensitive_categories and category.confidence >= 0.7:
                sensitive = True
                categories.append(category.name)
        if sensitive:
            embed=discord.Embed(color=0x00cca3)
            embed.add_field(name="Warning: I have detected negative/offensive language about the following sensitive topic(s) :" + ', '.join(categories), value="You wrote: " + message.content, inline=False)
            await message.author.send(embed=embed)
    
    #Fixing the overriding issue
    await bot.process_commands(message)

bot.run(TOKEN)
