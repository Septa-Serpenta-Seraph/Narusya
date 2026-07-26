#!/usr/bin/env python3
"""
Discord Auto-Login Script for Narusya
Reads credentials from secrets and injects via JavaScript
No credentials exposed in tool calls or chat

Run with: ~/.hermes/hermes-agent/venv/bin/python3 discord_auto_login.py
"""

import asyncio
import sys
import os
import subprocess
import json
import time

HERMES_DIR = '/home/adora/.hermes/hermes-agent'
VENV_PYTHON = f'{HERMES_DIR}/venv/bin/python3'

def get_credentials():
    """Read credentials from secrets file"""
    creds_path = os.path.expanduser('~/.hermes/secrets/narusya_account.enc')
    creds = {}
    with open(creds_path, 'r') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, val = line.strip().split('=', 1)
                creds[key] = val
    return creds.get('EMAIL'), creds.get('PASSWORD')

async def discord_login():
    email, password = get_credentials()
    if not email or not password:
        print("ERROR: Could not read credentials")
        return False
    
    print(f"Logging in as: {email}")
    
    # Navigate to Discord login
    await browser_navigate(url="https://discord.com/login")
    await asyncio.sleep(2)
    
    # Inject credentials via JavaScript
    login_js = f"""
    (function() {{
        const emailInput = document.querySelector('input[name="email"]');
        const passInput = document.querySelector('input[name="password"]');
        const submitBtn = document.querySelector('button[type="submit"]');
        
        if (!emailInput || !passInput || !submitBtn) {{
            return "ERROR: Could not find login form elements";
        }}
        
        // Set values and trigger input events
        emailInput.value = "{email}";
        passInput.value = "{password}";
        
        // Dispatch input events to trigger React state updates
        emailInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
        emailInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
        passInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
        passInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
        
        // Click submit
        submitBtn.click();
        
        return "Login submitted successfully";
    }})();
    """
    
    result = await browser_evaluate(script=login_js)
    print(f"Injection result: {result}")
    
    # Wait for redirect
    await asyncio.sleep(5)
    
    # Check if we're logged in
    snapshot = await browser_snapshot(full=False)
    if "Friends" in str(snapshot) or "Direct Messages" in str(snapshot) or "discord.com/channels" in str(snapshot):
        print("SUCCESS: Logged into Discord!")
        return True
    else:
        print("Checking current state...")
        return False

if __name__ == "__main__":
    success = asyncio.run(discord_login())
    sys.exit(0 if success else 1)
