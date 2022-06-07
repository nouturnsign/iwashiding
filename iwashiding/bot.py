import os as _os
import re as _re
import requests as _requests
import bs4 as _bs4
from dotenv import load_dotenv as _load_dotenv
from discord.ext import commands as _commands
import discord as _discord

COMMAND_PREFIX = ";"
emotes = {"PogChamp": "https://static-cdn.jtvnw.net/emoticons/v2/305954156/static/light/1.0",
          ":)":"https://static-cdn.jtvnw.net/emoticons/v2/1/static/light/1.0",
          ":(":"https://static-cdn.jtvnw.net/emoticons/v2/555555558/static/light/1.0",
          ":O":"https://static-cdn.jtvnw.net/emoticons/v2/555555580/static/light/1.0",
          "BibleThump":"https://static-cdn.jtvnw.net/emoticons/v2/86/static/light/1.0",
          ":D":"https://static-cdn.jtvnw.net/emoticons/v2/3/static/light/1.0",
          ":P":"https://static-cdn.jtvnw.net/emoticons/v2/12/static/light/1.0",
          ":|":"https://static-cdn.jtvnw.net/emoticons/v2/555555563/static/light/1.0",
          "<3":"https://static-cdn.jtvnw.net/emoticons/v2/555555584/static/light/1.0"}
emotes.update(_requests.get('https://raw.githubusercontent.com/nouturnsign/iwashiding/master/top_emotes.json').json()['emotes'])
bot = _commands.Bot(command_prefix=COMMAND_PREFIX)

_load_dotenv()
DISCORD_TOKEN = _os.environ['DISCORD_TOKEN']

@bot.event
async def on_message(message):
    
    if message.author == bot.user:
        return
    
    if message.content.startswith(COMMAND_PREFIX + 'demo'):
        await demo(await bot.get_context(message))
        return
    if message.content.startswith(COMMAND_PREFIX + 'emote '):
        await emote(await bot.get_context(message), message.content[message.content.index(' ') + 1:])
        return
    if message.content.startswith(COMMAND_PREFIX + 'catjam'):
        await catjam(await bot.get_context(message))
        return
    potential_emotes = _re.findall(r"(:(?:\w|[0-9])+:)", message.content)
    if len(potential_emotes) == 0:
        # no emotes to process
        return
    
    for potential_emote in potential_emotes:
        
        potential_emote = potential_emote[1:-1]
        ctx = await bot.get_context(message)
        await emote(ctx, potential_emote)

@bot.command()
async def demo(ctx):
    await ctx.send('You should see the PogChamp lizard.')
    await ctx.send(emotes["PogChamp"])
    

@bot.command()
async def catjam(ctx):
    await ctx.send(embed = _discord.Embed().set_image(url="https://cdn.betterttv.net/emote/61fe27dd06fd6a9f5be371a2/1x.gif"))    

@bot.command()
async def emote(ctx, emote):
    
    if emote not in emotes:
        await ctx.send('Emote unavailable.')
        # r = _requests.get(f'https://www.frankerfacez.com/emoticons/?q={emote}&sort=count-desc&days=0')
        # tr = _bs4.BeautifulSoup(r.content, 'html.parser').find('tbody').find('tr')
        # if tr.get_text() == 'No Emotes Found':
        #     await ctx.send('No Emotes Found')
        #     return
        # name = tr.find('td', {'class': 'emote-name'}).a.get_text()
        # src = tr.find('td', {'class': 'emoticon dark'}).img['src']
        # emotes[name] = src
    
        # if emote != name:
        #     await ctx.send(f'{emote} seems to match {name}. Did you mean {name}?') 
        #     return
    
    await ctx.send(emotes[emote])

bot.run(DISCORD_TOKEN)