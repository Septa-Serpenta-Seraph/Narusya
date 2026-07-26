#!/usr/bin/env python3
import asyncio
import os
import sys
import discord
from discord.ext import commands

TOKEN = os.getenv('DISCORD_BOT_TOKEN')
if not TOKEN:
    print("Missing DISCORD_BOT_TOKEN", file=sys.stderr)
    sys.exit(1)

GUILD_ID = 1447174038551134299
CHANNEL_ID = 1447174038979084464

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user}")
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        print("Guild not found", file=sys.stderr)
        await bot.close()
        return
    channel = guild.get_channel(CHANNEL_ID)
    if not channel:
        print("Channel not found", file=sys.stderr)
        await bot.close()
        return
    try:
        vc = await channel.connect()
        print(f"Joined voice channel {channel.name}")
    except Exception as e:
        print(f"Voice error: {e}", file=sys.stderr)

@bot.command()
async def play(ctx, *, filepath: str):
    """Play an audio file in the current voice channel."""
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if not voice_client:
        await ctx.send("I'm not in a voice channel.")
        return
    try:
        source = discord.FFmpegPCMAudio(filepath)
        voice_client.play(source, after=lambda e: print(f'Player error: {e}') if e else None)
        await ctx.send(f"Playing: {filepath}")
    except Exception as e:
        await ctx.send(f"Error playing file: {e}")

async def main():
    try:
        await bot.start(TOKEN)
    except discord.errors.LoginFailure:
        print("Invalid token", file=sys.stderr)
        sys.exit(1)

asyncio.run(main())
