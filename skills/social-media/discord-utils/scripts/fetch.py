import discord
import asyncio
import argparse
import sys

async def main(target_id, count, auth_key):
    client = discord.Client(intents=discord.Intents.all())

    async with client:
        try:
            await client.login(auth_key)
            channel = await client.fetch_channel(target_id)
            
            print(f"--- Log for #{channel.name} ---")
            async for msg in channel.history(limit=count):
                timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
                # Basic content
                out = f"[{timestamp}] {msg.author.name}: {msg.content}"
                
                # Check for attachments (voice messages are attachments)
                if msg.attachments:
                    attach_info = ", ".join([f"{a.filename} ({a.url})" for a in msg.attachments])
                    out += f" [Attachments: {attach_info}]"
                
                # Check for voice message metadata (if available in this version of discord.py)
                if hasattr(msg, 'flags') and msg.flags.value & 8192: # 1 << 13 is IS_VOICE_MESSAGE
                    out += " [VOICE MESSAGE]"
                
                print(out)
                
        except Exception as e:
             print(f"Ex: {e}")
        finally:
             await client.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cid", type=int, required=True)
    parser.add_argument("--lim", type=int, default=20)
    parser.add_argument("--key", type=str, required=True)
    args = parser.parse_args()

    asyncio.run(main(args.cid, args.lim, args.key))
