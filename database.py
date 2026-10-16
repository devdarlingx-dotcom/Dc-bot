import os
import json
import time
import aiosqlite
from config import DATABASE_PATH

async def init_db():
    """Initializes the SQLite tables if they do not exist."""
    dir_name = os.path.dirname(DATABASE_PATH)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
        
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id INTEGER PRIMARY KEY,
                autorole_id INTEGER,
                welcome_channel_id INTEGER,
                welcome_message TEXT,
                updates_channel_id INTEGER
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS reaction_roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER,
                channel_id INTEGER,
                role_id INTEGER,
                emoji_or_custom_id TEXT,
                mode TEXT DEFAULT 'button',
                title TEXT
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS giveaways (
                message_id INTEGER PRIMARY KEY,
                channel_id INTEGER,
                guild_id INTEGER,
                prize TEXT,
                end_time REAL,
                winners_count INTEGER,
                ended INTEGER DEFAULT 0,
                participants TEXT DEFAULT '[]'
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS script_updates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                script_name TEXT,
                version TEXT,
                changelog TEXT,
                download_url TEXT,
                created_at REAL
            )
        """)
        await db.commit()

# --- Guild Settings ---
async def get_guild_settings(guild_id: int) -> dict:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM guild_settings WHERE guild_id = ?", (guild_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return {
                "guild_id": guild_id,
                "autorole_id": None,
                "welcome_channel_id": None,
                "welcome_message": None,
                "updates_channel_id": None
            }

async def set_autorole(guild_id: int, role_id: int | None):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT INTO guild_settings (guild_id, autorole_id)
            VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET autorole_id = excluded.autorole_id
        """, (guild_id, role_id))
        await db.commit()

async def set_welcome_channel(guild_id: int, channel_id: int | None, custom_msg: str | None = None):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT INTO guild_settings (guild_id, welcome_channel_id, welcome_message)
            VALUES (?, ?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET 
                welcome_channel_id = excluded.welcome_channel_id,
                welcome_message = COALESCE(excluded.welcome_message, guild_settings.welcome_message)
        """, (guild_id, channel_id, custom_msg))
        await db.commit()

async def set_updates_channel(guild_id: int, channel_id: int | None):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT INTO guild_settings (guild_id, updates_channel_id)
            VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET updates_channel_id = excluded.updates_channel_id
        """, (guild_id, channel_id))
        await db.commit()

# --- Reaction / Button Roles ---
async def add_reaction_role(message_id: int, channel_id: int, role_id: int, emoji_or_custom_id: str, mode: str = "button", title: str = ""):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT INTO reaction_roles (message_id, channel_id, role_id, emoji_or_custom_id, mode, title)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (message_id, channel_id, role_id, emoji_or_custom_id, mode, title))
        await db.commit()

async def get_reaction_role(message_id: int, emoji_or_custom_id: str) -> dict | None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM reaction_roles WHERE message_id = ? AND emoji_or_custom_id = ?",
            (message_id, emoji_or_custom_id)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def get_reaction_role_by_button_id(custom_id: str) -> dict | None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM reaction_roles WHERE emoji_or_custom_id = ?",
            (custom_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def get_all_reaction_roles() -> list[dict]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM reaction_roles") as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

# --- Giveaways ---
async def create_giveaway(message_id: int, channel_id: int, guild_id: int, prize: str, end_time: float, winners_count: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT INTO giveaways (message_id, channel_id, guild_id, prize, end_time, winners_count, ended, participants)
            VALUES (?, ?, ?, ?, ?, ?, 0, '[]')
        """, (message_id, channel_id, guild_id, prize, end_time, winners_count))
        await db.commit()

async def get_giveaway(message_id: int) -> dict | None:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM giveaways WHERE message_id = ?", (message_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                data = dict(row)
                data["participants"] = json.loads(data["participants"])
                return data
            return None

async def get_active_giveaways() -> list[dict]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM giveaways WHERE ended = 0") as cursor:
            rows = await cursor.fetchall()
            result = []
            for r in rows:
                d = dict(r)
                d["participants"] = json.loads(d["participants"])
                result.append(d)
            return result

async def toggle_giveaway_participant(message_id: int, user_id: int) -> tuple[bool, int]:
    """Toggles a user's entry. Returns (is_entered_now, total_count)."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT participants, ended FROM giveaways WHERE message_id = ?", (message_id,)) as cursor:
            row = await cursor.fetchone()
            if not row or row["ended"] == 1:
                return (False, 0)
            participants = json.loads(row["participants"])
            
            if user_id in participants:
                participants.remove(user_id)
                entered = False
            else:
                participants.append(user_id)
                entered = True
                
            await db.execute(
                "UPDATE giveaways SET participants = ? WHERE message_id = ?",
                (json.dumps(participants), message_id)
            )
            await db.commit()
            return (entered, len(participants))

async def end_giveaway(message_id: int):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("UPDATE giveaways SET ended = 1 WHERE message_id = ?", (message_id,))
        await db.commit()

# --- Script Updates ---
async def save_script_update(script_name: str, version: str, changelog: str, download_url: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT INTO script_updates (script_name, version, changelog, download_url, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (script_name, version, changelog, download_url, time.time()))
        await db.commit()

async def get_recent_script_updates(limit: int = 5) -> list[dict]:
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM script_updates ORDER BY id DESC LIMIT ?", (limit,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]
