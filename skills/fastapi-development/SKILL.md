---
name: fastapi-development
description: "Use when building or extending a FastAPI web backend, including real-time WebSocket gateways, file uploads, sync-after-gap reconnect reconciliation, and AI/bot participant integration."
version: 1.4.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [fastapi, python, web, api, scaffolding, sqlalchemy]
    related_skills: [systematic-debugging, writing-plans, test-driven-development]
---

# FastAPI Development

## When to Use

Use when creating, scaffolding, or extending a FastAPI web backend. Covers project structure, database models, auth, routes, and common pitfalls.

## Overview

Build FastAPI web applications with SQLAlchemy models, JWT auth, and REST API routes. This skill covers project scaffolding, common pitfalls, and the debugging patterns that cost time.

## Project Structure

```
backend/
├── main.py              # FastAPI app, router aggregation, startup hooks
├── auth.py              # JWT + password hashing, get_current_user dependency
├── models/
│   ├── __init__.py      # DB engine, session, init_db, re-exports all models
│   └── database.py      # SQLAlchemy models (Base, User, etc.)
├── api/
│   ├── __init__.py
│   ├── auth_routes.py   # Register, login, /me
│   ├── servers.py       # Server + channel CRUD
│   └── messages.py      # Message CRUD + reactions
└── requirements.txt
```

## Critical Pitfall: write_file Content

**Never include shell commands in write_file content.** The `write_file` tool writes the ENTIRE content string to the file verbatim. Appending `echo "Done"` or `EOF` to the content writes those as file content, causing syntax errors.

```python
# WRONG — echo "Done" becomes part of the file
write_file(path="file.py", content="...code...\necho \"Done\"")

# RIGHT — content is only the file content
write_file(path="file.py", content="...code...")
```

Always verify file content after writing by parsing it (e.g., `python3 -c "import ast; ast.parse(open('file.py').read())"`).

## Critical Pitfall: Import Resolution

When running FastAPI from the `backend/` directory, **use absolute imports**, not relative imports:

```python
# WRONG — fails with "attempted relative import with no known parent package"
from .models import get_db, User
from .auth import hash_password

# RIGHT — works when running from backend/ directory
from models import get_db, User
from auth import hash_password
```

For files in subdirectories (e.g., `api/`), import from the parent package level:

```python
# In backend/api/auth_routes.py
from models import get_db, User      # NOT from .models or from ..models
from auth import get_current_user    # NOT from .auth or from ..auth
```

**Why:** When running `uvicorn main:app` from the `backend/` directory, Python's `sys.path` includes `backend/` but not `backend/api/`. Relative imports (`from .`) require the module to be part of a package, which doesn't work when running as a script.

## Scaffolding Pattern

### 1. Models First

Define SQLAlchemy models in `models/database.py`. Use `DeclarativeBase` with `Mapped` type annotations (SQLAlchemy 2.0 style). Export all models and session helpers from `models/__init__.py`.

Key patterns:
- Use `func.now()` for timestamps
- Use `cascade="all, delete-orphan"` for child relationships
- Use association tables for many-to-many
- Use `Mapped[Optional[str]]` for nullable fields

### 2. Auth Second

Create `auth.py` with:
- `hash_password` / `verify_password` (passlib bcrypt)
- `create_access_token` / `decode_token` (python-jose JWT)
- `get_current_user` dependency (FastAPI `Depends`)
- `SECRET_KEY` from environment with a default for dev

### 3. Routes Third

Create route files in `api/` directory. Each file defines an `APIRouter` with a prefix:

```python
router = APIRouter(prefix="/api/servers", tags=["servers"])
```

Use Pydantic models for request/response validation. Always include `from_attributes = True` in response models for ORM compatibility.

### 4. Main App Last

Aggregate routers in `main.py`:

```python
app.include_router(auth_router)
app.include_router(servers_router)
app.include_router(messages_router)
```

Add CORS middleware, health check, and DB init on startup.

## Testing Approach

Test by running the server and making HTTP requests:

```bash
cd backend && .venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
# In another terminal:
curl -s http://localhost:8000/health
curl -s -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@test.com","password":"password123"}'
```

Verify file syntax after every write:

```bash
python3 -c "import ast; ast.parse(open('file.py').read()); print('OK')"
```

## Security Pitfalls

14. **Default JWT secret is a known string** — `os.getenv("SECRET_KEY", "change-me-...")` allows anyone to forge tokens if the env var is unset. In production, fail hard on startup if `SECRET_KEY` is not set: `if not os.getenv("SECRET_KEY"): raise RuntimeError("SECRET_KEY must be set")`. Never ship with a default.
15. **`int(user_id)` without validation** — `int("abc")` raises `ValueError` → 500 error instead of 401. Wrap in try/except and return 401: `try: uid = int(user_id) except (ValueError, TypeError): raise credentials_exception`.
16. **No rate limiting on auth endpoints** — Register and login are brute-forceable. Add rate limiting (e.g., `slowapi`) or at minimum, account lockout after N failed attempts.
17. **Association tables must be exported from `models/__init__.py`** — When you create association tables (e.g., `server_members`, `conversation_participants`) in `models/database.py`, you must import and re-export them from `models/__init__.py`. API modules that reference these tables will fail with `ImportError` if they're not exported. Pattern: `from .database import ..., server_members, conversation_participants` in `__init__.py`, then `from models import server_members` in API modules.
18. **Combine ownership + membership in one query** — Instead of checking `user in server.members or server.owner_id == user.id` (which loads all members), use a single SQL query with `or_`: `db.query(Server).outerjoin(server_members, Server.id == server_members.c.server_id).filter(or_(server_members.c.user_id == user.id, Server.owner_id == user.id))`. This is both faster and avoids lazy-loading pitfalls.
19. **Bot token generation needs ownership check** — Any authenticated user can generate a bot token and impersonate the AI. Require admin/owner role: `if not current_user.is_admin: raise HTTPException(403)`.
20. **CORS with credentials + wildcard methods** — `allow_methods=["*"]` with `allow_credentials=True` is overly permissive. Specify exact methods (`["GET", "POST", "PATCH", "DELETE"]`) and headers in production.
21. **No transaction rollback** — If `db.commit()` fails, the session is left in a broken state. Wrap DB writes in try/except with `db.rollback()`:
    ```python
    try:
        db.add(msg)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
    ```
22. **@everyone default role permissions** — When creating a server, the default `@everyone` role should have basic permissions (read + send = 3), not 0. With permissions=0, new members can't read or send messages until the owner manually grants permissions. Like Discord's @everyone, grant read + send by default.
23. **Ship a .env.example** — Always include a `.env.example` file documenting all environment variables (SECRET_KEY, DATABASE_URL, CORS_ORIGINS, etc.) with example values. This is the first thing a new contributor looks for.

## Performance Pitfalls

20. **`in` on SQLAlchemy relationships triggers full load** — `if user not in server.members` loads ALL members. Use a query instead: `exists = db.query(ServerMember).filter_by(server_id=server.id, user_id=user.id).first()`. Or use `selectinload` for eager loading.
21. **Dead WebSocket connections accumulate** — `broadcast_to_channel` catches exceptions but doesn't remove dead connections. Track and remove failed connections:
    ```python
    dead = set()
    for ws in connections:
        try: await ws.send_json(msg)
        except: dead.add(ws)
    connections -= dead
    ```
22. **No pagination on frontend** — Messages are loaded once. For large channels, implement cursor-based pagination with `before` parameter and "load more" button.
23. **`localStorage` parsing on every render** — Parsing JSON from localStorage in a render loop (e.g., for DM participant names) is wasteful. Store parsed values in state.
24. **N+1 in mention polling** — When polling for pending mentions, the naive approach queries each message's channel, server, and bot-reply status individually. Use eager loading (`joinedload` for author/channel) and batch-fetch servers in one query. Use `Message.id > mention.id` (not timestamp) for the "already replied" check. Limit the reply check with `.limit(1)` since you only need a boolean.

## Real-time Pitfalls

24. **Bot messages don't broadcast via WebSocket** — When a bot posts via REST API, it must also broadcast to the channel via the WebSocket manager. Otherwise, bot messages only appear on page refresh. Call `await manager.broadcast_to_channel(channel_id, msg_data)` after creating the bot message.
25. **DMs need WebSocket support** — DM conversations should subscribe to a DM-specific channel ID for real-time updates. Without this, new DMs only appear on refresh.
26. **WebSocket route returns 404 on HTTP GET** — This is expected. `/ws` only handles WebSocket upgrades. Don't test it with `curl` or `urllib` — use a WebSocket client library.
27. **Unclean WebSocket disconnect leaves "online" status** — If a client crashes, the `finally` block never runs. Add a background task or heartbeat to detect and clean up stale connections.
28. **WebSocket message length not validated** — REST endpoints enforce max content length via Pydantic, but WebSocket handlers accept arbitrary-length messages. Add `if len(content) > 4000: await websocket.send_json({"type": "error", "message": "Message too long"}); continue` after parsing the message payload.
29. **DM real-time broadcast needs participant IDs** — When sending a DM, fetch all participant IDs from the `conversation_participants` table BEFORE broadcasting. Then call `manager.send_to_user(pid, dm_data)` for each participant. Don't try to derive participants from the message object — it may not have the full relationship loaded.
30. **Bot bridge login uses username, not email** — The OAuth2 login endpoint expects a `username` field. If your bridge accepts `--email`, it will only work if the user's email happens to be their username. Accept `--username` as primary and `--email` as alias. Document this clearly in the bridge's help text.

## Database Pitfalls

28. **`create_all()` doesn't ALTER existing tables** — `init_db()` only creates missing tables. Adding a column requires manual migration or dropping the table. Use Alembic for production schema changes.
29. **`conversation_participants` table defined after model** — The association table must be defined before or alongside the model that references it. Use string references (`secondary="conversation_participants"`) and define the table at module level before the class.
30. **No `__repr__` on models** — Add `__repr__` for debugging: `def __repr__(self): return f"<User(id={self.id}, username={self.username})>"`.
31. **Integer position for ordering** — Reordering channels/messages requires updating all positions. Use fractional or gap-based ordering for efficient reordering.
31. **Frontend DM real-time WebSocket listener** — DMView must connect to WebSocket and listen for `type: "dm"` messages filtered by `conversation_id`. Deduplicate by message ID to avoid showing duplicates (the REST response and WS broadcast may both deliver the same message). On reconnect, re-fetch messages from REST to catch anything missed.
32. **Frontend attachment display** — Render attachments inline: images as `<img>` previews (max 300×200, clickable), other files as download links with filename + size. Use `window.location.origin` prefix for relative URLs.
33. **Frontend file upload button** — Use a hidden `<input type="file">` triggered by a button click. Show uploading state (⏳/📎). Upload via FormData, then send message with attachment metadata. Handle errors with user feedback.
34. **Frontend reconnect sync** — On WebSocket close (non-1000), re-fetch messages from REST after a short delay (1s). This catches any messages missed during the disconnection. Don't rely solely on the backend sync mechanism — the frontend should also reconcile.
36. **Bot token chicken-and-egg** — The bot token endpoint requires an authenticated human user. The bridge logs in as a human to get a bot token. For true "Hermes as backbone" architecture, the bot should be able to self-bootstrap (e.g., a pre-configured bot secret). Current design is fine for polling bridge but limits autonomous operation.
37. **WebSocket in-memory only** — ConnectionManager stores connections in a dict. Multiple uvicorn workers won't share WebSocket state — broadcasts won't cross instances. This is a scaling ceiling, not a bug. For horizontal scaling, use Redis pub/sub or a shared connection store.
38. **Flag placeholder responses** — When a bridge script has a placeholder response (echo instead of LLM call), flag it prominently with `=== PLACEHOLDER ===` markers and a TODO comment. Easy to miss in code review.
40. **Frontend single-file monolith** — The entire frontend in one App.jsx (1000+ lines) becomes unmaintainable as features grow (DMs, threads, reactions, etc.). Split into components (ChannelList, MessageView, DMView, etc.) even with a simple folder structure. Start early — refactoring later is painful.
41. **No soft-delete** — Deleted messages are permanently removed. Consider `is_deleted: bool` for audit/moderation trails.

## File Uploads & Static Serving

When adding file/image attachments to a FastAPI app:

### Upload Endpoint

Use FastAPI's `UploadFile` with `File(...)` for multipart uploads:

```python
from fastapi import UploadFile, File
import os, uuid

UPLOAD_DIR = os.path.join(PROJECT_ROOT, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/channels/{channel_id}/upload")
async def upload_file(
    channel_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")

    ext = os.path.splitext(file.filename or "file")[1]
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    with open(file_path, "wb") as f:
        f.write(content)

    return {
        "filename": file.filename,
        "url": f"/uploads/{unique_name}",
        "size": len(content),
        "content_type": file.content_type,
    }
```

### Static File Mounting

Mount the uploads directory in `main.py` BEFORE the frontend catch-all:

```python
# Serve uploaded files (relative to project root)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
uploads_dir = os.path.join(PROJECT_ROOT, "uploads")
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# Serve frontend (if built) — MUST come after /uploads
frontend_dir = os.path.join(PROJECT_ROOT, "frontend", "dist")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
```

### Path Consistency (Critical)

When files in different directories (e.g., `backend/api/messages.py` and `backend/main.py`) both reference the uploads directory, they must resolve to the SAME absolute path. `os.path.dirname(__file__)` differs per module:

- `backend/api/messages.py` → `os.path.dirname(__file__)` = `backend/api/`
- `backend/main.py` → `os.path.dirname(__file__)` = `backend/`

**Always compute paths relative to the project root**, not relative to the current file:

```python
# WRONG — resolves differently depending on which module runs it
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")

# RIGHT — consistent across all modules
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))  # from backend/api/
# or
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # from backend/
UPLOAD_DIR = os.path.join(PROJECT_ROOT, "uploads")
```

### Linking Attachments to Messages

Upload the file first (get URL), then send the message with attachment metadata:

```python
# In create_message handler:
msg = Message(channel_id=channel_id, author_id=current_user.id, content=req.content)
db.add(msg)
db.commit()
db.refresh(msg)

if req.attachments:
    for att in req.attachments:
        db.add(Attachment(
            message_id=msg.id,
            filename=att.get("filename", "file"),
            url=att.get("url", ""),
            size=att.get("size", 0),
            content_type=att.get("content_type"),
        ))
    db.commit()
```

### .gitignore

Always add `uploads/` to `.gitignore` — uploaded files should not be committed.

## Sync-After-Gap (Reconnect Reconciliation)

When a client reconnects after being offline, it must reconcile missed messages. Implement both WebSocket and REST paths:

### WebSocket Sync

Add a `sync` message type to the WebSocket handler:

```python
elif msg_type == "sync":
    channel_id = data.get("channel_id")
    last_seen_id = data.get("last_seen_message_id", 0)

    # Verify access (same as message handler)
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel: ...
    server = db.query(Server).filter(Server.id == channel.server_id).first()
    if not member: ...

    # Fetch missed messages
    messages = (
        db.query(Message)
        .filter(Message.channel_id == channel_id)
        .filter(Message.id > last_seen_id)
        .order_by(Message.created_at.asc())
        .limit(200)
        .all()
    )

    await websocket.send_json({
        "type": "sync_response",
        "channel_id": channel_id,
        "last_seen_message_id": last_seen_id,
        "missed_count": len(messages),
        "messages": [serialize(m) for m in messages],
    })
```

### REST Sync Endpoint

```python
@router.get("/channels/{channel_id}/messages/since/{last_seen_id}")
def get_messages_since(channel_id, last_seen_id, current_user, db):
    # Same access check + query as above
    ...
```

### Frontend Reconnect Flow

1. On WebSocket reconnect, for each subscribed channel, send `sync` with `last_seen_message_id`
2. On `sync_response`, append missed messages to the local message list
3. Deduplicate by message ID (in case of partial overlap)
4. Update `last_seen_message_id` to the highest received ID

33. **`isMobile()` evaluated at render, not on resize** — Mobile/desktop layout doesn't respond to window resize. Use a resize listener or CSS media queries instead.
34. **No loading states** — Most operations (create server, send message) don't show loading indicators. Add `loading` state to buttons and forms.
36. **Pass user data as props, not localStorage parsing** — When a component needs the current user's ID (e.g., for DM participant name resolution), pass it as a prop from the parent component instead of parsing `localStorage` in a render loop. `localStorage.getItem('quetzalcoatl_user')` may not exist, and JSON.parse on every render is wasteful. Store parsed values in state or pass as props.

## Comprehensive Testing Checklist

After implementing features, run a full test suite covering all endpoint types. Use Python's `urllib` for REST and `websockets` library for WebSocket tests:

```python
import asyncio, json, urllib.request, urllib.parse

BASE = "http://localhost:8000"
TOKEN = None  # Set after login

def test(name, fn):
    try:
        ok = fn()
        print(f"{'✅' if ok else '❌'} {name}")
    except Exception as e:
        print(f"❌ {name}: {str(e)[:80]}")

# Auth
def t_login():
    global TOKEN
    form = urllib.parse.urlencode({"username": "test", "password": "test123"}).encode()
    req = urllib.request.Request(f"{BASE}/api/auth/login", data=form, headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
    with urllib.request.urlopen(req) as r:
        TOKEN = json.loads(r.read())["access_token"]
        return True

# REST endpoints
def t_create_server():
    data = {"name": "Test Server"}
    req = urllib.request.Request(f"{BASE}/api/servers", data=json.dumps(data).encode(), headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req) as r:
        return r.status == 200

# WebSocket
async def _ws_test():
    import websockets
    async with websockets.connect(f"ws://localhost:8000/ws?token={TOKEN}") as ws:
        await ws.send(json.dumps({"type": "ping"}))
        resp = json.loads(await ws.recv())
        return resp["type"] == "pong"

def t_ws():
    return asyncio.run(_ws_test())

# Run all
test("Auth: login", t_login)
test("Server: create", t_create_server)
test("WebSocket: ping/pong", t_ws)
```

### Test Categories (minimum coverage)
1. **Auth**: register, login, /me, unauthenticated rejection, no SECRET_KEY
2. **CRUD**: create, list, get, update, delete for each resource
3. **Membership**: member access, non-member rejection, owner bypass
4. **WebSocket**: connect, subscribe, message, typing, sync, disconnect cleanup
5. **File uploads**: upload, static serve, attachment linking
6. **Security**: input validation (max length), unauthenticated rejection, rate limiting
7. **Bot API**: token gen, pending mentions, history, channels
8. **DMs**: create conversation, send, list, delete, 1:1 dedup

### Key Testing Pitfalls
- **Reaction endpoints** may take `emoji` as a query param, not JSON body — check the route signature
- **DM create** field is `user_ids`, not `participant_ids` — check the Pydantic model
- **Auth register** returns 400 if user exists — handle in tests or use unique usernames
- **WebSocket tests** require `websockets` library (not `websocket-client`) — install via `pip install websockets`
- **Static file 404** usually means path resolution mismatch between upload and serve modules — check `os.path.dirname(__file__)` per module
- **Frontend build** must be rebuilt after frontend changes: `cd frontend && npm run build`

1. **Trailing shell commands in write_file content** — writes them as file content (see above)
2. **Relative imports** — fail when running as script; use absolute imports
3. **Missing `__init__.py`** — subdirectories need `__init__.py` to be importable packages
4. **SQLAlchemy 2.0 style** — use `Mapped[]` and `mapped_column()`, not the old `Column()` style (though both work)
5. **CORS origins** — set `CORS_ORIGINS` env var or default to `*` for dev
6. **SQLite thread safety** — use `check_same_thread=False` in engine config
7. **Password hashing** — use passlib bcrypt, not plain text or weak hashing
8. **JWT secret** — use environment variable in production, not the dev default
9. **Validation error format** — FastAPI returns 422 errors with `detail` as an array of objects (each with `loc`, `msg`, `type`), NOT a string. Frontend code must handle both: `if (typeof err.detail === 'string') use it; else if (Array.isArray(err.detail)) join the `.msg` fields`. Otherwise the UI shows `[object Object]`.
10. **passlib on Python 3.14+** — passlib's bcrypt backend fails with `ValueError: password cannot be longer than 72 bytes` in `detect_wrap_bug`. Replace passlib with direct `bcrypt` library: `bcrypt.hashpw(password.encode(), bcrypt.gensalt())` and `bcrypt.checkpw(password.encode(), hash)`. Pin `bcrypt>=4.0` in requirements.
11. **Mobile access / relative URLs** — when the frontend is served by the same backend, use `window.location.origin` for API base URL, not `http://localhost:8000`. On mobile, `localhost` resolves to the phone, not the server. Same for WebSocket: `ws://${window.location.host}/ws`.
12. **Uvicorn port conflicts on restart** — When restarting the server, old processes may still hold port 8000. Kill them first: `pkill -f uvicorn` then wait 2s before starting. Check with `pgrep -f uvicorn` or `curl http://localhost:8000/health`. Multiple uvicorn processes cause "address already in use" errors.
13. **Mention dedup by ID not timestamp** — When tracking whether a bot has responded to a mention, use `Message.id > mention.id` (auto-incrementing IDs) instead of `created_at > mention.created_at`. SQLite may store timestamps at second precision, causing bot replies created in the same second to be missed.
14. **Static file mount order** — When serving both uploaded files and a frontend SPA, mount `/uploads` BEFORE the `/` catch-all. If `/` is mounted first, it will intercept all requests including `/uploads/*`. Use `app.mount("/uploads", StaticFiles(...))` then `app.mount("/", StaticFiles(directory=frontend_dir, html=True))`.
15. **Path resolution across modules** — `os.path.dirname(__file__)` resolves differently per module. Files in `backend/api/` and `backend/` that reference the same directory (e.g., uploads) will compute different paths. Always resolve relative to project root using `os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))` from `backend/api/` or `os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))` from `backend/`.

## WebSocket Gateway (Real-time)

FastAPI supports WebSocket natively. Pattern for a real-time messaging gateway:

```python
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        self.active: dict[int, set[WebSocket]] = {}  # user_id -> connections
        self.subscribers: dict[int, set[int]] = {}     # channel_id -> user_ids

    async def connect(self, ws, user_id):
        await ws.accept()
        self.active.setdefault(user_id, set()).add(ws)

    def disconnect(self, ws, user_id):
        self.active[user_id].discard(ws)
        if not self.active[user_id]:
            del self.active[user_id]

    async def broadcast(self, channel_id, message, exclude=None):
        for uid in self.subscribers.get(channel_id, set()):
            if uid == exclude: continue
            for ws in self.active.get(uid, set()):
                try: await ws.send_json(message)
                except: pass

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    user = authenticate_token(token)  # your auth function
    if not user: await websocket.close(code=4001); return
    await manager.connect(websocket, user.id)
    try:
        while True:
            data = await websocket.receive_json()
            if data["type"] == "subscribe":
                await manager.subscribe(user.id, data["channel_id"])
            elif data["type"] == "message":
                # Save to DB, then broadcast
                msg = create_message(data["channel_id"], user.id, data["content"])
                await manager.broadcast(data["channel_id"], msg)
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket, user.id)
```

**Key points:**
- Authenticate via query param token (not headers — WebSocket can't set custom headers in browser)
- Use `send_json()` / `receive_json()` for structured messages
- Always handle `WebSocketDisconnect` and clean up connections
- Broadcast to channel subscribers, not all connected users
- The frontend must use `window.location.host` for the WebSocket URL, not `localhost`

## AI / Bot Participant Integration

When making an AI (Hermes, Narusya, etc.) a native participant in a chat platform:

### Database Model
Add `is_bot: bool = False` to the User model. Bot users are created with a system password and seeded on startup.

### Bot API Endpoints (prefix: `/api/bot`)
- `POST /api/bot/token` — Generate JWT for bot user (requires authenticated human user)
- `POST /api/bot/message` — Post message as bot (requires bot token). Auto-joins server if needed.
- `GET /api/bot/history/{channel_id}` — Fetch recent messages for context (bot-only)
- `GET /api/bot/pending` — Poll for messages mentioning the bot that haven't been responded to
- `GET /api/bot/channels` — List channels the bot has access to
- `POST /api/bot/join/{server_id}` — Add bot to a server

### Mention Detection
Check message content for trigger strings (`@hermes`, `@narusya`, `@bot`). Store pending mentions. Clear a mention when the bot posts a reply in the same channel with `Message.id > mention.id`.

### Bot Bridge (Polling Service)
A standalone Python script that:
1. Logs in with user credentials
2. Gets a bot token via `/api/bot/token`
3. Polls `/api/bot/pending` every N seconds
4. Fetches channel history for context
5. Generates response (replace placeholder with LLM call)
6. Posts via `/api/bot/message` with `reply_to_id` set

### Frontend Bot Display
- Bot messages: distinct avatar (🐍), colored username, "BOT" badge, highlighted background
- Mention highlighting: split message text on `@\w+` and wrap mentions in styled spans
- `is_bot` flag on message data drives the styling

### Key Pattern: Bot Auto-Join
When the bot posts to a channel, check if it's a server member. If not, add it automatically. This allows the bot to respond in any channel without manual setup.

```python
server = db.query(Server).filter(Server.id == channel.server_id).first()
if bot not in server.members and server.owner_id != bot.id:
    server.members.append(bot)
    db.commit()
```

**Use `is_bot` flag, not hardcoded IDs:** When checking if a user is the bot, use `user.is_bot` boolean instead of `user.id == 7` or similar hardcoded values. Hardcoded IDs break when the bot user's ID changes (e.g., different database, re-seeding).

## PWA (Progressive Web App) Setup

When building a web app that should be installable on mobile devices, add PWA support:

### 1. Web Manifest (`frontend/public/manifest.json`)
```json
{
  "name": "App Name",
  "short_name": "App",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#36393f",
  "theme_color": "#5865f2",
  "icons": [
    { "src": "/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icon-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

### 2. Service Worker (`frontend/public/sw.js`)
Cache static assets for offline use. Register in `index.html`:
```html
<link rel="manifest" href="/manifest.json">
<script>
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js');
  }
</script>
```

### 3. Vite Config
Ensure `public/` assets are copied to `dist/` during build. Vite does this by default.

### 4. Mobile Access
- API base URL must use `window.location.origin`, not `localhost` (see Pitfall #11)
- WebSocket URL must use `window.location.host`
- Test by opening `http://<server-ip>:8000` on a phone and using "Add to Home Screen"

## Direct Messages (DM) System

When adding 1:1 and group direct messaging to a chat platform:

### Database Models

```python
class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    is_group: Mapped[bool] = mapped_column(Boolean, default=False)
    name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # group name
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    participants: Mapped[List["User"]] = relationship("User", secondary="conversation_participants")
    messages: Mapped[List["DirectMessage"]] = relationship("DirectMessage", back_populates="conversation", cascade="all, delete-orphan")

class DirectMessage(Base):
    __tablename__ = "direct_messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(Integer, ForeignKey("conversations.id"), nullable=False)
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

# Association table
conversation_participants = Table(
    "conversation_participants", Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("conversation_id", Integer, ForeignKey("conversations.id"), primary_key=True),
    Column("joined_at", DateTime, default=func.now()),
)
```

### API Endpoints (prefix: `/api/dms`)

- `GET /conversations` — list user's DM conversations (ordered by updated_at desc)
- `POST /conversations` — create conversation. For 1:1, deduplicate: check if a non-group conversation already exists between the two users before creating.
- `GET /conversations/{id}/messages` — paginated DM history (same pattern as channel messages)
- `POST /conversations/{id}/messages` — send DM. Update conversation.updated_at on send.
- `DELETE /conversations/{id}/messages/{id}` — delete own DM
- `GET /users/search?q=` — search users by username prefix for starting new DMs

### Key Pattern: 1:1 Deduplication

```python
if not req.is_group and len(all_user_ids) == 2:
    other_id = (all_user_ids - {current_user.id}).pop()
    existing = db.query(Conversation).filter(
        Conversation.is_group == False,
        Conversation.participants.any(User.id == current_user.id),
        Conversation.participants.any(User.id == other_id),
    ).first()
    if existing:
        return existing  # return existing conversation instead of creating
```

### Frontend DM View

A DM view component (similar to channel MessageView) that:
- Loads messages via `api.getDMMessages(convId)`
- Sends via `api.sendDM(convId, { content })`
- Shows participant names in the header
- Supports bot badge display (same as channel messages)

### Frontend Integration

Add DM conversations to the sidebar alongside channels:
- List conversations with 💬 prefix
- "+ New DM" button that searches users and creates a conversation
- Toggle between channel view and DM view based on selection
- Mobile: DMs appear in the channel list section

### DM Real-time Broadcast

DM messages should broadcast via WebSocket to all participants for real-time delivery:

```python
# After creating the DM message and committing:
participant_ids = [p.user_id for p in db.query(conversation_participants).filter(
    conversation_participants.c.conversation_id == conversation_id
).all()]

try:
    from gateway.websocket import manager
    import asyncio
    dm_data = {
        "type": "dm",
        "id": msg.id,
        "conversation_id": msg.conversation_id,
        "author_id": msg.author_id,
        "author_username": msg.author.username,
        "content": msg.content,
        "created_at": msg.created_at.isoformat(),
    }
    for pid in participant_ids:
        asyncio.ensure_future(manager.send_to_user(pid, dm_data))
except Exception:
    pass  # Best-effort
```

**Key point:** Fetch participant IDs from the association table BEFORE broadcasting. Don't rely on the message's relationship being loaded.

## Architecture Diagrams (README)

Use Mermaid diagrams in the README for GitHub-native rendering. Three useful types:

1. **Architecture diagram** (`graph TB`) — shows component relationships, color-coded by layer
2. **Data model** (`erDiagram`) — entity-relationship diagram for database tables
3. **Feature roadmap** (`graph LR`) — flowchart showing feature tiers and dependencies

Mermaid renders natively on GitHub — no image files needed. Use `style` directives for color coding.

## Dependencies

```
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
sqlalchemy>=2.0.0
python-jose[cryptography]>=3.3.0
bcrypt>=4.0.0
pydantic>=2.9.0
python-multipart>=0.0.12
aiofiles>=24.1.0
websockets>=12.0
```
