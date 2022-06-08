import os as _os
import re as _re
import asyncio as _asyncio
import requests as _requests
from dotenv import load_dotenv as _load_dotenv
from discord.ext import commands as _commands
import discord as _discord

from presets import *

emotes.update(_requests.get(TOP_EMOTES_URL).json()['emotes'])
bot = _commands.Bot(
    command_prefix=COMMAND_PREFIX, 
    description=BOT_DESCRIPTION,
    help_command=_commands.DefaultHelpCommand(no_category = 'Commands')
)
emoji_cache = {}
popularity_cache = {}

_load_dotenv()
DISCORD_TOKEN = _os.environ['DISCORD_TOKEN']

@bot.event
async def on_command_error(ctx: _commands.Context, error: _commands.errors) -> _commands.errors:

    if isinstance(error, _commands.errors.CommandNotFound):
        await ctx.send(f'Command not found. Try using `{COMMAND_PREFIX}help`')
    raise error

@bot.event
async def on_connect():
    
    print(BOT_NAME + " connected")

@bot.event
async def on_ready():
    global emoji_cache, popularity_cache
    
    emoji_cache = {emoji.name[len(BOT_NAME + SEP):]:emoji for emoji in bot.emojis if emoji.name.startswith(BOT_NAME)}
    popularity_cache = {name:0 for name in emoji_cache}
    print("Available emojis:", list(emoji_cache.keys()))
    print(BOT_NAME + " ready")

@bot.event
async def on_message(message: _discord.Message):
    
    if not bot.is_ready():
        print('Bot not ready yet!')
        return
    
    author = message.author
    if not isinstance(author, _discord.member.Member):
        # ignore messages from bots
        return

    if message.content.startswith(COMMAND_PREFIX):
        await bot.process_commands(message)
        return
    
    await _replace_with_emotes(message)

@bot.command()
async def demo(ctx: _commands.Context):
    """Demo of sending emotes."""
    
    await ctx.send('You should see the PogChamp lizard.')
    await ctx.send(emotes["PogChamp"])

@bot.command()
async def catjam(ctx: _commands.Context):
    """Sending catJAM as an embeded gif."""
    
    await ctx.send(embed = _discord.Embed().set_image(url="https://cdn.betterttv.net/emote/61fe27dd06fd6a9f5be371a2/1x.gif"))    

@bot.command()
async def emote(ctx: _commands.Context, emote: str):
    """Have the bot send an existing emote as an image/*."""
    
    if emote not in emotes:
        await ctx.send('Emote unavailable.')
        return
    
    await ctx.send(emotes[emote])
    
async def _replace_with_emotes(message: _discord.Message):
    global emoji_cache, popularity_cache

    potential_emotes = [potential_emote 
                        for potential_emote in _re.findall(r"(:(?:\w|[0-9])+:)", message.content) 
                        if not potential_emote.startswith(':' + BOT_NAME + SEP)]
    if len(potential_emotes) == 0:
        # no emotes to process
        return
    print('Found emotes:', potential_emotes)
    
    edited_message = message.content
    ctx = await bot.get_context(message)
    print('Original message', edited_message)
    
    fetchable = {potential_emote[1:-1] for potential_emote in potential_emotes if potential_emote[1:-1] not in emoji_cache}
    await _asyncio.gather(*((add(ctx, name, emotes[name], verbose=False)) for name in fetchable))
    print('Downloaded all new emojis:', fetchable)
    
    for potential_emote in potential_emotes:
        name = potential_emote[1:-1]
        emoji = emoji_cache[name]
        edited_message = _re.sub(":" + name + ":", str(emoji), edited_message)
    print('Edited message:', edited_message)

    author = message.author
    hook = await message.channel.create_webhook(name=BOT_NAME + SEP + "hook")
    print('Created hook:', hook)
    
    await hook.send(
        edited_message,
        username=author.display_name + " // " + BOT_NAME,
        avatar_url=author.avatar_url
    )
    print('Sent message as hook')
    
    await message.delete()
    await hook.delete()
    print('Deleted original message and hook')
    
@bot.command(aliases=['overwrite'])
async def add(ctx: _commands.Context, name: str, url: str, verbose: bool=True):
    """Add or overwrite existing emote, using a name and url."""
    global emoji_cache, popularity_cache
    
    guild = ctx.guild
    
    try:
        image_request = _requests.get(url)
    except Exception:
        print('Bad request from:', url)
        return
        
    if name in emoji_cache:
        await emoji_cache[name].delete()
        if verbose: await ctx.send(f'Deleted existing emoji {name}.')
        print('Deleted existing emoji:', name)
    if image_request.status_code != 200 or not image_request.headers.get('Content-Type', None).startswith('image'):
        if verbose: await ctx.send('Invalid url:', url)
        print('Bad response:', image_request.status_code, 'from:', url)
        return
    
    is_gif = image_request.headers['Content-Type'].endswith('gif')
    try:
        temp_emoji = await guild.create_custom_emoji(name=BOT_NAME + SEP + name, image=image_request.content)
    except _discord.errors.HTTPException:
        least_popular_emoji = emoji_cache[min(popularity_cache.keys(), 
                                              key=lambda name: 
                                                  # flip the .startswith condition (is not is_gif)
                                                  # so that gifs are sorted first when we are looking at a gif
                                                  (str(emoji_cache[name]).startswith('<a') is not is_gif, 
                                                   popularity_cache[name]))]
        await least_popular_emoji.delete()
        print('Deleted emoji:', least_popular_emoji.name)
        try:
            temp_emoji = await guild.create_custom_emoji(name=BOT_NAME + SEP + name, image=image_request.content)
        except Exception as e:
            print(f'Tried creating emoji {name}, but failed for unknown reason: {e}')
            return
        
    emoji_cache[name] = temp_emoji
    popularity_cache[name] = popularity_cache.get(name, 0) + 1
    if verbose: await ctx.send(f'Created emote {temp_emoji}')
    print('Created emoji:', temp_emoji)

@bot.command() 
async def remove(ctx: _commands.Context, emote: str):
    """Remove an existing emote, using a name."""
    global emoji_cache, popularity_cache
    
    if emote not in emoji_cache:
        await ctx.send(f"Emote {emote} has not been added yet.")
        return
    emoji = emoji_cache.pop(emote)
    popularity_cache.pop(emote)
    await emoji.delete()
    await ctx.send(f"Emote {emote} has been removed.")

@bot.command(aliases=['removeall']) 
async def clear(ctx: _commands.Context):
    """Remove all generated emojis."""
    global emoji_cache, popularity_cache
    
    for emoji in emoji_cache.values():
        await emoji.delete()
        print("Deleted:", emoji.name)
    emoji_cache = {}
    popularity_cache = {}
    await ctx.send(f"Cleared all emotes from {BOT_NAME}.")

bot.run(DISCORD_TOKEN)