from contextlib import asynccontextmanager
import json
import os
import requests
import discord
from dotenv import load_dotenv
from discord.ext import commands
from google.cloud import language_v1

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r"apikey.json"
load_dotenv()

GUILD = "Hackerbois"
bot = commands.Bot(command_prefix='!')
client = language_v1.LanguageServiceClient()

sensitive_categories = ['/Sensitive Subjects', 'Social Issues & Advocacy/Discrimination & Identity Relations', '/People & Society']
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

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    document = language_v1.Document(
        content=message.content, type_=language_v1.Document.Type.PLAIN_TEXT
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
        print(content)

    
    document = {"content": content, "type_": language_v1.Document.Type.PLAIN_TEXT}
   
    response = client.classify_text(request = {'document': document})
    
    print(sentiment.score, sentiment.magnitude)
    print(response.categories)

    #Very negative, regardless of topic, should be banned
    if(sentiment.score <=0.89 and sentiment.magnitude >=0.89):
        await message.author.send("Category 1: Obviously very negative")

    #Clearly about sensitive topic, should be banned
    for category in response.categories:
        if category.name in sensitive_categories and category.confidence >= 0.89:
            await message.author.send("Category 2: Obviously sensitive topic")

    #Both negative and sensitive
    if(sentiment.score <= -0.7 and sentiment.magnitude >= 0.8):
        for category in response.categories:
            if category.name in sensitive_categories and category.confidence >= 0.6:
                await message.author.send("Category 3: Both negative and sensitive")
    
    #Fixing the overriding issue
    await bot.process_commands(message)

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

        
bot.run(TOKEN)
