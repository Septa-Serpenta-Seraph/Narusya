#!/usr/bin/env python3
"""Daily auto-append for Narusya Archive.
Checks state.db for new sessions since last archive run, exports them
to the sessions directory, and updates the master INDEX.md stats."""

import sqlite3
import datetime
import os
import json
import re

DB_PATH = "/home/adora/.hermes/state.db"
ARCHIVE_DIR = "/home/adora/Desktop/Narusya-Archive"
SESSIONS_DIR = os.path.join(ARCHIVE_DIR, "sessions")
MARKER_PATH = os.path.join(ARCHIVE_DIR, ".last_archive_state.json")

def sanitize_filename(name):
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name)[:80]

def get_last_archive_state():
    if os.path.exists(MARKER_PATH):
        with open(MARKER_PATH) as f:
            return json.load(f)
    return {'last_session_id': None, 'last_message_count': 0, 'last_run': None}

def save_last_archive_state(state):
    with open(MARKER_PATH, 'w') as f:
        json.dump(state, f)

def main():
    print(f"[{datetime.datetime.now().strftime('%H:%M')}] Daily archive check starting...")
    
    state = get_last_archive_state()
    
    if not os.path.exists(DB_PATH):
        print("No state.db found. Skipping.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM messages WHERE content IS NOT NULL AND content != ''")
    current_msg_count = cur.fetchone()[0]
    
    cur.execute("""
        SELECT s.id, s.source, s.model, s.started_at, s.ended_at,
               s.end_reason, s.message_count, s.title, s.estimated_cost_usd
        FROM sessions s ORDER BY s.started_at ASC
    """)
    
    all_sessions = []
    for row in cur.fetchall():
        all_sessions.append({
            'id': row[0], 'source': row[1], 'model': row[2],
            'started_at': row[3], 'ended_at': row[4], 'end_reason': row[5],
            'msg_count': row[6] or 0, 'title': row[7],
            'estimated_cost_usd': row[8]
        })
    
    conn.close()
    
    # Find new sessions (not yet archived). archived_ids maps
    # session_id -> message_count at last archive; a session is "new" if it's
    # unseen or has grown since. The old single last_session_id marker is
    # kept for backward compat and used once to bootstrap the map.
    last_id = state.get('last_session_id')
    archived_map = {k: v for k, v in (state.get('archived_map') or {}).items()}
    if last_id is not None and not archived_map:
        # Bootstrap: prior runs tracked only last_session_id, and everything
        # except the then-live last session has already been exported.
        archived_map = {s['id']: s['msg_count'] for s in all_sessions if s['id'] != last_id}
    new_sessions = []
    daily_cache = {}

    for session in all_sessions:
        dt = datetime.datetime.fromtimestamp(session['started_at'])
        date_key = dt.strftime('%Y-%m-%d')
        filename = f"{date_key}_{sanitize_filename(dt.strftime('%A'))}.md"
        filepath = os.path.join(SESSIONS_DIR, filename)

        if date_key not in daily_cache:
            daily_cache[date_key] = {
                "path": filepath,
                "sessions": [],
                "exists": os.path.exists(filepath)
            }
        daily_cache[date_key]["sessions"].append(session)

        if archived_map.get(session['id'], 0) < session['msg_count']:
            if session['msg_count'] > 0:
                new_sessions.append(session)
    
    # Update indexes (even on quiet days, so stats stay current)
    update_session_index(daily_cache, all_sessions)
    update_master_index(all_sessions)

    if not new_sessions:
        print("No new sessions since last archive run.")
        return
    
    print(f"Found {len(new_sessions)} new sessions to archive.")
    
    # For new sessions: either create new daily file or append to existing
    for session in new_sessions:
        dt = datetime.datetime.fromtimestamp(session['started_at'])
        date_key = dt.strftime('%Y-%m-%d')
        filepath = daily_cache[date_key]["path"]
        
        cost = session.get('estimated_cost_usd') or 0
        cost_str = f"${cost:.4f}" if cost > 0 else "$0.00"
        title = session.get('title') or "Untitled Session"
        sess_time = dt.strftime('%H:%M:%S')
        
        entry = f"---\n\n## Session: {title}\n\n"
        entry += f"```\nID: {session['id']}\n"
        entry += f"Time: {sess_time}\nSource: {session['source']}\n"
        entry += f"Model: {session['model']}\nMessages: {session['msg_count']}\n"
        entry += f"Estimated Cost: {cost_str}\n"
        if session.get('end_reason'):
            entry += f"Ended: {session['end_reason']}\n"
        entry += f"```\n\n"
        
        # Get messages for full export
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            SELECT role, content, timestamp, tool_name
            FROM messages WHERE session_id = ?
            AND content IS NOT NULL AND content != ''
            ORDER BY id ASC
        """, (session['id'],))
        messages = cur.fetchall()
        conn.close()
        
        if messages:
            entry += f"<details><summary>Full conversation ({len(messages)} messages)</summary>\n\n"
            for msg in messages:
                ts = datetime.datetime.fromtimestamp(msg[2]).strftime('%H:%M:%S')
                role, content, tool_name = msg[0], msg[1], msg[3]
                
                if role == 'tool' and tool_name:
                    preview = content[:500] + ("..." if len(content) > 500 else "")
                    entry += f"### [{ts}] tool: {tool_name}\n\n```\n{preview}\n```\n\n"
                elif role == 'assistant':
                    preview = content[:1000] + ("..." if len(content) > 1000 else "")
                    entry += f"### [{ts}] assistant\n\n{preview}\n\n"
                elif role == 'user':
                    preview = content[:500] + ("..." if len(content) > 500 else "")
                    entry += f"### [{ts}] user\n\n{preview}\n\n"
            entry += "</details>\n\n"
        
        if daily_cache[date_key]["exists"]:
            with open(filepath, 'a') as f:
                f.write(entry)
        else:
            day_name = dt.strftime('%A')
            with open(filepath, 'w') as f:
                f.write(f"# {date_key} ({day_name})\n\n")
                f.write(entry)
    
    # Update sessions INDEX.md (redundant on this path, cheap; kept for clarity)
    update_session_index(daily_cache, all_sessions)
    update_master_index(all_sessions)

    # Save state
    state['last_session_id'] = all_sessions[-1]['id']
    state['last_message_count'] = current_msg_count
    state['last_run'] = datetime.datetime.now().isoformat()
    state['sessions_archived_today'] = len(new_sessions)
    for s in new_sessions:
        archived_map[s['id']] = s['msg_count']
    state['archived_map'] = archived_map
    save_last_archive_state(state)
    
    print(f"Successfully archived {len(new_sessions)} new sessions.")

def update_session_index(daily_cache, all_sessions):
    idx_path = os.path.join(SESSIONS_DIR, "INDEX.md")
    total_sessions = len(all_sessions)
    total_messages = sum(s['msg_count'] for s in all_sessions)
    
    dates = sorted(daily_cache.keys())
    
    with open(idx_path, 'w') as f:
        f.write(f"# Session Archive Index\n\n")
        f.write(f"**Total sessions:** {total_sessions}  \n")
        f.write(f"**Total messages exported:** {total_messages}  \n")
        f.write(f"**Date range:** {dates[0]} to {dates[-1]}  \n")
        f.write(f"**Days with sessions:** {len(dates)}  \n")
        f.write(f"**Last updated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}  \n\n---\n\n")
        
        current_date = None
        for session in sorted(all_sessions, key=lambda x: x['started_at']):
            dt = datetime.datetime.fromtimestamp(session['started_at'])
            date_key = dt.strftime('%Y-%m-%d')
            if date_key != current_date:
                current_date = date_key
                dn = dt.strftime('%A')
                f.write(f"\n## {date_key} ({dn})\n\n")
            
            cost = session.get('estimated_cost_usd') or 0
            cost_str = f"${cost:.4f}" if cost > 0 else "$0.00"
            title = session.get('title') or "Untitled Session"
            st = dt.strftime('%H:%M:%S')
            fn = f"{date_key}_{sanitize_filename(dt.strftime('%A'))}.md"
            f.write(f"- [{st}] **{title}** - `{session['source']}` / `{session['model']}` - {session['msg_count']} msgs - {cost_str}  \n")
            f.write(f"  [{fn}](./{fn})\n")

def update_master_index(all_sessions):
    idx_path = os.path.join(ARCHIVE_DIR, "INDEX.md")

    total_sessions = len(all_sessions)
    total_messages = sum(s['msg_count'] for s in all_sessions)
    dates = sorted({datetime.datetime.fromtimestamp(s['started_at']).strftime('%Y-%m-%d') for s in all_sessions})
    date_min, date_max = (dates[0], dates[-1]) if dates else ("-", "-")
    now_str = datetime.datetime.now().strftime('%Y-%m-%d')

    if not os.path.exists(idx_path):
        content = (
            "# Narusya Archive — Master Index\n\n"
            "**Total sessions:** 0\n"
            "**Total Messages ** | 0\n"
            "**Date range:** - to -\n"
            "**Last Updated:** -\n\n"
            "Daily exports live in [sessions/](./sessions/) — see "
            "[sessions/INDEX.md](./sessions/INDEX.md) for the full session list.\n"
        )
    else:
        with open(idx_path, 'r') as f:
            content = f.read()

    # Line-based rewrite of the stats block — regex tweaks kept missing
    # whitespace-sensitive matches before, leaving stale/zero values behind.
    replacements = {
        '**Total sessions:**': f'**Total sessions:** {total_sessions}',
        '**Total Messages ** |': f'**Total Messages ** | {total_messages}',
        '**Date range:**': f'**Date range:** {date_min} to {date_max}',
        '**Last Updated:**': f'**Last Updated:** {now_str}',
    }
    lines = []
    for line in content.splitlines():
        stripped = line.strip()
        for key, value in replacements.items():
            if stripped.startswith(key):
                line = value
                break
        lines.append(line)
    content = "\n".join(lines) + "\n"

    with open(idx_path, 'w') as f:
        f.write(content)

if __name__ == "__main__":
    main()
