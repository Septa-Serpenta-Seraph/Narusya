#!/usr/bin/env python3
"""
Mountain Time Timestamp Injector
Outputs current time in Santa Fe (Mountain Time) in various formats.

Usage:
    python3 mt_timestamp.py              # Full formatted output
    python3 mt_timestamp.py --compact    # Compact single-line
    python3 mt_timestamp.py --file       # Write to timestamp file
    python3 mt_timestamp.py --json       # JSON output
"""

import argparse
import json
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

TIMESTAMP_FILE = os.path.expanduser("~/.hermes/cache/mt_timestamp.txt")
MT_TZ = ZoneInfo("America/Denver")


def get_mt_time() -> dict:
    """Get current Mountain Time with metadata."""
    now_mt = datetime.now(MT_TZ)
    now_utc = datetime.now(timezone.utc)
    
    # Determine if DST is active
    is_dst = now_mt.dst().total_seconds() != 0
    tz_name = "MDT" if is_dst else "MST"
    utc_offset = "-0600" if is_dst else "-0700"
    
    return {
        "datetime": now_mt,
        "date": now_mt.strftime("%A, %B %d, %Y"),
        "time_12h": now_mt.strftime("%I:%M %p"),
        "time_24h": now_mt.strftime("%H:%M"),
        "timezone": tz_name,
        "utc_offset": utc_offset,
        "iso": now_mt.isoformat(),
        "utc": now_utc.isoformat(),
        "is_dst": is_dst,
        "day_of_week": now_mt.strftime("%A"),
        "full": now_mt.strftime(f"%A, %B %d, %Y at %I:%M %p {tz_name}"),
    }


def format_output(data: dict, compact: bool = False) -> str:
    """Format the timestamp for display."""
    if compact:
        return f"⏰ {data['time_12h']} {data['timezone']} | {data['date']}"
    
    return f"""⏰ Current time in Santa Fe, NM:
   {data['date']}
   {data['time_12h']} {data['timezone']} ({data['time_24h']} in 24h)
   UTC offset: {data['utc_offset']}
   Daylight saving: {'Yes' if data['is_dst'] else 'No'}"""


def write_timestamp_file(data: dict):
    """Write timestamp to cache file for quick access."""
    os.makedirs(os.path.dirname(TIMESTAMP_FILE), exist_ok=True)
    
    content = f"""# Mountain Time Timestamp (auto-updated)
# Last updated: {data['iso']}

⏰ {data['full']}
Time: {data['time_12h']} {data['timezone']} ({data['time_24h']})
Date: {data['date']}
DST: {'Active' if data['is_dst'] else 'Inactive'}
"""
    
    with open(TIMESTAMP_FILE, 'w') as f:
        f.write(content)
    
    print(f"✅ Written to {TIMESTAMP_FILE}")


def main():
    parser = argparse.ArgumentParser(description="Mountain Time timestamp for Narusya")
    parser.add_argument("--compact", action="store_true", help="Compact output")
    parser.add_argument("--file", action="store_true", help="Write to cache file")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--check-file", action="store_true", help="Read cached timestamp")
    
    args = parser.parse_args()
    
    if args.check_file:
        if os.path.exists(TIMESTAMP_FILE):
            with open(TIMESTAMP_FILE) as f:
                print(f.read())
        else:
            print("No cached timestamp found. Run without --check-file first.")
        return
    
    data = get_mt_time()
    
    if args.json:
        # Convert datetime to string for JSON
        json_data = {k: str(v) if 'datetime' in str(type(v)) else v for k, v in data.items()}
        print(json.dumps(json_data, indent=2))
        return
    
    if args.file:
        write_timestamp_file(data)
        return
    
    if args.compact:
        print(format_output(data, compact=True))
    else:
        print(format_output(data))


if __name__ == "__main__":
    main()
