#!/usr/bin/env python3
"""
Nar-Voice — Narusya's voice engine.
Generate speech with presets, play to Discord, save to file.

Usage:
    nar-voice.py speak "Hello world" [--preset deep] [--discord] [--save out.mp3]
    nar-voice.py list-presets
    nar-voice.py join-voice [--guild ID] [--channel ID]
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# === Paths ===
SKILL_DIR = Path(__file__).parent.parent
PRESETS_FILE = SKILL_DIR / "presets.yaml"
DEFAULT_GUILD = "1387534334067736699"  # Cultus Anarchia
DEFAULT_CHANNEL = "1422748377723961486"  # voice-chat


def load_presets():
    """Load presets from YAML. Falls back to JSON if PyYAML missing."""
    with open(PRESETS_FILE) as f:
        content = f.read()
    
    try:
        import yaml
        return yaml.safe_load(content)
    except ImportError:
        # Fallback: try json (won't work for yaml, but at least fails clearly)
        raise RuntimeError("PyYAML required: pip install pyyaml")


def get_preset(config, name=None):
    """Get a preset by name, or the default."""
    if not name:
        name = config.get("default", "deep")
    
    presets = config.get("presets", {})
    if name not in presets:
        available = ", ".join(presets.keys())
        raise ValueError(f"Unknown preset '{name}'. Available: {available}")
    
    return presets[name]


def resolve_path(p):
    """Expand ~ and resolve path."""
    return os.path.expanduser(str(p))


# === Piper TTS ===

def generate_piper(text, preset, config):
    """Generate speech using piper TTS. Returns path to MP3."""
    paths = config.get("paths", {})
    piper_bin = resolve_path(paths.get("piper_binary", "~/.local/bin/piper"))
    voices_dir = resolve_path(paths.get("piper_voices", "~/.local/share/piper-voices/"))
    ffmpeg_bin = resolve_path(paths.get("ffmpeg", "/usr/bin/ffmpeg"))
    
    # Set up environment
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = resolve_path(paths.get("env_ld_library", "~/.local/lib/piper"))
    env["ESPEAK_DATA_PATH"] = resolve_path(paths.get("env_espeak_data", "~/.local/lib/piper/espeak-ng-data"))
    
    model_name = preset.get("model", "en_US-libritts-high")
    model_path = os.path.join(voices_dir, f"{model_name}.onnx")
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found: {model_path}")
    
    pitch = preset.get("pitch", 1.0)
    speed = preset.get("speed", 1.0)
    
    # Step 1: Generate WAV with piper
    tmp_wav = tempfile.NamedTemporaryFile(suffix=".wav", prefix="nar_piper_", delete=False)
    tmp_wav.close()
    
    try:
        # Generate speech
        proc = subprocess.run(
            [piper_bin, "--model", model_path, "--output_file", tmp_wav.name],
            input=text, text=True, capture_output=True, env=env
        )
        if proc.returncode != 0:
            raise RuntimeError(f"Piper failed: {proc.stderr}")
        
        # Step 2: Apply effects with ffmpeg
        # Piper outputs 22050Hz mono
        tmp_mp3 = tempfile.NamedTemporaryFile(suffix=".mp3", prefix="nar_voice_", delete=False)
        tmp_mp3.close()
        
        # Build ffmpeg filter chain
        filters = []
        
        # Pitch shift (asetrate at piper's native 22050Hz, resample to 48kHz)
        if pitch != 1.0:
            filters.append(f"asetrate=22050*{pitch},aresample=48000")
        else:
            filters.append("aresample=48000")
        
        # Speed (atempo, range 0.5-2.0, chain for extreme values)
        if speed != 1.0:
            filters.append(f"atempo={speed}")
        
        # Stereo for Discord
        filters.append("aformat=sample_fmts=s16:sample_rates=48000:channel_layouts=stereo")
        
        filter_str = ",".join(filters)
        
        proc = subprocess.run(
            [ffmpeg_bin, "-y", "-i", tmp_wav.name, "-af", filter_str,
             "-ar", "48000", "-ac", "2", tmp_mp3.name],
            capture_output=True
        )
        if proc.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {proc.stderr.decode()[:200]}")
        
        return tmp_mp3.name
    
    finally:
        # Clean up WAV
        if os.path.exists(tmp_wav.name):
            os.unlink(tmp_wav.name)


# === Edge TTS ===

def generate_edge_tts(text, preset, config):
    """Generate speech using edge-tts. Returns path to MP3."""
    paths = config.get("paths", {})
    edge_tts_bin = resolve_path(paths.get("edge_tts", "~/.hermes/hermes-agent/venv/bin/edge-tts"))
    
    voice = preset.get("voice", "en-US-AriaNeural")
    
    tmp_mp3 = tempfile.NamedTemporaryFile(suffix=".mp3", prefix="nar_edge_", delete=False)
    tmp_mp3.close()
    
    proc = subprocess.run(
        [edge_tts_bin, "--text", text, "--voice", voice, "--write-media", tmp_mp3.name],
        capture_output=True, text=True
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Edge-TTS failed: {proc.stderr}")
    
    if not os.path.exists(tmp_mp3.name) or os.path.getsize(tmp_mp3.name) == 0:
        raise RuntimeError("Edge-TTS produced no output")
    
    # Edge-tts outputs mono mp3 — convert to 48kHz stereo for Discord consistency
    tmp_final = tempfile.NamedTemporaryFile(suffix=".mp3", prefix="nar_voice_", delete=False)
    tmp_final.close()
    
    ffmpeg_bin = resolve_path(paths.get("ffmpeg", "/usr/bin/ffmpeg"))
    proc = subprocess.run(
        [ffmpeg_bin, "-y", "-i", tmp_mp3.name, "-ar", "48000", "-ac", "2", tmp_final.name],
        capture_output=True
    )
    os.unlink(tmp_mp3.name)
    
    if proc.returncode != 0:
        raise RuntimeError(f"FFmpeg conversion failed: {proc.stderr.decode()[:200]}")
    
    return tmp_final.name


# === Discord Playback ===

def play_discord(mp3_path, guild_id=None, channel_id=None, persistent=False):
    """Play audio file to Discord voice channel.
    
    If persistent=True, stays connected for 10 minutes waiting for more clips.
    Use with a persistent server/socket for multi-clip playback.
    """
    guild_id = guild_id or DEFAULT_GUILD
    channel_id = channel_id or DEFAULT_CHANNEL
    
    # Get bot token
    env_path = os.path.expanduser("~/.hermes/.env")
    token = None
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith("DISCORD_BOT_TOKEN="):
                    token = line.split("=", 1)[1].strip()
                    break
    if not token:
        raise RuntimeError("DISCORD_BOT_TOKEN not found in ~/.hermes/.env")
    
    script = f'''
import asyncio, os
TOKEN = {json.dumps(token)}
GUILD_ID = {json.dumps(guild_id)}
CHANNEL_ID = {json.dumps(channel_id)}
MP3_PATH = {json.dumps(mp3_path)}

async def main():
    import discord
    intents = discord.Intents.default()
    client = discord.Client(intents=intents)
    
    @client.event
    async def on_ready():
        guild = client.get_guild(int(GUILD_ID))
        channel = guild.get_channel(int(CHANNEL_ID))
        vc = discord.utils.get(client.voice_clients, guild=guild)
        if not vc or not vc.is_connected():
            vc = await channel.connect()
        
        source = discord.FFmpegPCMAudio(MP3_PATH, options="-vn -ar 48000 -ac 2 -f s16le")
        vc.play(discord.PCMVolumeTransformer(source, volume=1.0))
        while vc.is_playing():
            await asyncio.sleep(0.5)
        
        print("PLAYED", flush=True)
        {"await asyncio.sleep(600)" if persistent else ""}
        await client.close()
    
    await client.start(TOKEN)

asyncio.run(main())
'''
    
    venv_python = os.path.expanduser("~/.hermes/hermes-agent/venv/bin/python")
    proc = subprocess.run(
        [venv_python, "-c", script],
        capture_output=True, text=True, timeout=120
    )
    
    if "PLAYED" not in proc.stdout:
        raise RuntimeError(f"Discord playback failed: {proc.stderr[:300]}")
    
    return True


# === Main Entry Point ===

def speak(text, preset_name=None, discord_mode=False, save_path=None, guild_id=None, channel_id=None):
    """Generate speech and play/save it."""
    config = load_presets()
    preset = get_preset(config, preset_name)
    engine = preset.get("engine", "piper")
    
    print(f"[nar-voice] Engine: {engine} | Preset: {preset_name or config.get('default', 'deep')}", file=sys.stderr)
    print(f"[nar-voice] \"{text[:60]}{'...' if len(text) > 60 else ''}\"", file=sys.stderr)
    
    # Generate
    if engine == "piper":
        mp3_path = generate_piper(text, preset, config)
    elif engine == "edge-tts":
        mp3_path = generate_edge_tts(text, preset, config)
    else:
        raise ValueError(f"Unknown engine: {engine}")
    
    size_kb = os.path.getsize(mp3_path) / 1024
    print(f"[nar-voice] Generated: {mp3_path} ({size_kb:.0f}KB)", file=sys.stderr)
    
    # Output
    if save_path:
        # Save to specified path
        os.rename(mp3_path, save_path)
        print(f"[nar-voice] Saved: {save_path}", file=sys.stderr)
        return save_path
    
    if discord_mode:
        try:
            play_discord(mp3_path, guild_id, channel_id)
            print(f"[nar-voice] Played to Discord ✓", file=sys.stderr)
        finally:
            if os.path.exists(mp3_path):
                os.unlink(mp3_path)
        return True
    
    # Default: return the path (caller handles it)
    return mp3_path


def speak_queue(texts, preset_name=None, discord_mode=False, guild_id=None, channel_id=None):
    """Generate and play multiple clips in a SINGLE Discord connection.
    
    This avoids the connect/disconnect/reconnect problem that causes timeouts.
    """
    config = load_presets()
    preset = get_preset(config, preset_name)
    engine = preset.get("engine", "piper")
    
    # Generate all clips first
    mp3_paths = []
    for text in texts:
        print(f"[nar-voice] Generating: \"{text[:40]}...\"", file=sys.stderr)
        if engine == "piper":
            path = generate_piper(text, preset, config)
        else:
            path = generate_edge_tts(text, preset, config)
        mp3_paths.append(path)
    
    print(f"[nar-voice] Generated {len(mp3_paths)} clips", file=sys.stderr)
    
    if discord_mode:
        # Play all in ONE connection
        try:
            play_discord_queue(mp3_paths, guild_id, channel_id)
            print(f"[nar-voice] Played {len(mp3_paths)} clips to Discord ✓", file=sys.stderr)
        finally:
            for p in mp3_paths:
                if os.path.exists(p):
                    os.unlink(p)
        return True
    
    return mp3_paths


def play_discord_queue(mp3_paths, guild_id=None, channel_id=None):
    """Play multiple audio files in a single Discord voice connection."""
    guild_id = guild_id or DEFAULT_GUILD
    channel_id = channel_id or DEFAULT_CHANNEL
    
    env_path = os.path.expanduser("~/.hermes/.env")
    token = None
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith("DISCORD_BOT_TOKEN="):
                    token = line.split("=", 1)[1].strip()
                    break
    if not token:
        raise RuntimeError("DISCORD_BOT_TOKEN not found")
    
    paths_json = json.dumps(mp3_paths)
    
    script = f'''
import asyncio, os, json
TOKEN = {json.dumps(token)}
GUILD_ID = {json.dumps(guild_id)}
CHANNEL_ID = {json.dumps(channel_id)}
MP3_PATHS = {paths_json}

async def main():
    import discord
    intents = discord.Intents.default()
    client = discord.Client(intents=intents)
    
    @client.event
    async def on_ready():
        guild = client.get_guild(int(GUILD_ID))
        channel = guild.get_channel(int(CHANNEL_ID))
        vc = discord.utils.get(client.voice_clients, guild=guild)
        if not vc or not vc.is_connected():
            vc = await channel.connect()
            print("CONNECTED", flush=True)
        
        for i, path in enumerate(MP3_PATHS):
            if not os.path.exists(path):
                print(f"SKIP {{i}}: {{path}} not found", flush=True)
                continue
            print(f"PLAY {{i}}/{{len(MP3_PATHS)}}: {{os.path.basename(path)}}", flush=True)
            source = discord.FFmpegPCMAudio(path, options="-vn -ar 48000 -ac 2 -f s16le")
            vc.play(discord.PCMVolumeTransformer(source, volume=1.0))
            while vc.is_playing():
                await asyncio.sleep(0.5)
            await asyncio.sleep(0.8)
        
        print("ALL_DONE", flush=True)
        await client.close()
    
    await client.start(TOKEN)

asyncio.run(main())
'''
    
    venv_python = os.path.expanduser("~/.hermes/hermes-agent/venv/bin/python")
    proc = subprocess.run(
        [venv_python, "-c", script],
        capture_output=True, text=True, timeout=300
    )
    
    if "ALL_DONE" not in proc.stdout:
        raise RuntimeError(f"Discord queue playback failed: {proc.stderr[:300]}")
    
    return True


def list_presets():
    """Print available presets."""
    config = load_presets()
    default = config.get("default", "deep")
    presets = config.get("presets", {})
    
    print(f"Default preset: {default}\n")
    print(f"{'Name':<12} {'Engine':<10} {'Voice/Model':<25} {'Pitch':<6} {'Speed':<6} {'Description'}")
    print("-" * 90)
    
    for name, p in presets.items():
        engine = p.get("engine", "?")
        if engine == "piper":
            voice = p.get("model", "?")
            pitch = str(p.get("pitch", 1.0))
            speed = str(p.get("speed", 1.0))
        else:
            voice = p.get("voice", "?")
            pitch = "-"
            speed = "-"
        desc = p.get("description", "")
        marker = " *" if name == default else ""
        print(f"{name:<12} {engine:<10} {voice:<25} {pitch:<6} {speed:<6} {desc}{marker}")


def main():
    parser = argparse.ArgumentParser(description="Nar-Voice: Narusya's voice engine")
    sub = parser.add_subparsers(dest="command")
    
    # speak
    sp = sub.add_parser("speak", help="Generate and play/save speech")
    sp.add_argument("text", help="Text to speak (or path to file with --file)")
    sp.add_argument("--file", "-f", action="store_true", help="Treat text arg as file path containing lines to speak")
    sp.add_argument("--preset", "-p", help="Voice preset name")
    sp.add_argument("--discord", "-d", action="store_true", help="Play to Discord voice")
    sp.add_argument("--save", "-s", help="Save to file path")
    sp.add_argument("--guild", "-g", help="Discord guild ID")
    sp.add_argument("--channel", "-c", help="Discord channel ID")
    sp.add_argument("--queue", "-q", action="store_true", help="Use single-connection queue mode (for multiple clips)")
    
    # list-presets
    sub.add_parser("list-presets", help="Show available presets")
    
    args = parser.parse_args()
    
    if args.command == "speak":
        if args.queue and args.discord:
            # Queue mode: generate all, play in single connection
            if args.file:
                with open(args.text) as f:
                    texts = [line.strip() for line in f if line.strip()]
            else:
                texts = [args.text]
            result = speak_queue(
                texts=texts,
                preset_name=args.preset,
                discord_mode=True,
                guild_id=args.guild,
                channel_id=args.channel,
            )
        else:
            result = speak(
                text=args.text,
                preset_name=args.preset,
                discord_mode=args.discord,
                save_path=args.save,
                guild_id=args.guild,
                channel_id=args.channel,
            )
            if isinstance(result, str) and os.path.exists(result):
                print(result)  # Print path for scripting
    
    elif args.command == "list-presets":
        list_presets()
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
