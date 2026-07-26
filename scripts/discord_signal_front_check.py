#!/usr/bin/env python3
"""
Navigate to Signal Front general chat and capture recent messages
"""

import asyncio
import sys
sys.path.insert(0, '/home/adora/.hermes/hermes-agent')

from tools.browser_tool import browser_navigate, browser_snapshot

async def check_signal_front():
    # Navigate directly to Signal Front general chat
    channel_url = "https://discord.com/channels/1401295842081636484/1407819407228534804"
    await browser_navigate(url=channel_url)
    await asyncio.sleep(3)
    
    # Get snapshot of messages
    snapshot = await browser_snapshot(full=True)
    
    # Extract message content (this will be messy but workable)
    print("\n=== Signal Front General Chat ===\n")
    
    # Look for message patterns in the snapshot
    lines = str(snapshot).split('\n')
    messages = []
    for line in lines:
        # Look for message-like patterns (username + content)
        if '[ref=' in line and ('text:' in line.lower() or any(char.isalpha() for char in line)):
            messages.append(line.strip())
    
    # Print last 30 message lines
    for msg in messages[-30:]:
        print(msg)
    
    return snapshot

if __name__ == "__main__":
    asyncio.run(check_signal_front())
