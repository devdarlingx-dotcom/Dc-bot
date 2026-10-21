import os
import sys
import asyncio
import discord
from discord.ext import commands
import database
from config import DISCORD_TOKEN, OWNER_ID, make_kawaii_embed, COLOR_ERROR
from web_dashboard.server import start_web_server

def build_intents(privileged: bool = True) -> discord.Intents:
    intents = discord.Intents.default()
    intents.reactions = True
    intents.guilds = True
    if privileged:
        intents.members = True
        intents.message_content = True
    return intents

class DestinyBot(commands.Bot):
    def __init__(self, privileged_intents: bool = True):
        super().__init__(
            command_prefix="!",
            intents=build_intents(privileged=privileged_intents),
            help_command=None
        )
        self.privileged_enabled = privileged_intents

    async def setup_hook(self):
        # 1. Initialize SQLite database
        await database.init_db()
        print("🌸 SQLite Database tables initialized successfully! ✨")

        # 2. Load all feature cogs
        cogs_list = [
            "cogs.autorole",
            "cogs.reaction_roles",
            "cogs.announcements",
            "cogs.moderation",
            "cogs.giveaways",
            "cogs.script_updates",
            "cogs.welcome",
            "cogs.panel"
        ]

        for cog in cogs_list:
            try:
                await self.load_extension(cog)
                print(f"✨ Loaded cog: {cog}")
            except Exception as e:
                print(f"❌ Failed to load cog {cog}: {e}", file=sys.stderr)

        # 3. Start Kawaii Web Dashboard immediately for Railway port health checks
        try:
            asyncio.create_task(start_web_server(self))
        except Exception as e:
            print(f"❌ Failed to start web dashboard: {e}")

        # 4. Synchronize Slash Commands in background so bot is online instantly
        async def sync_bg():
            try:
                synced = await self.tree.sync()
                print(f"🌸 Synchronized {len(synced)} slash commands with Discord! ✨")
            except Exception as e:
                print(f"❌ Slash command sync error: {e}")

        asyncio.create_task(sync_bg())

    async def on_ready(self):
        print("=" * 60)
        print(f"🌸 Destiny Kawaii Bot is READY & ONLINE! ✨")
        print(f"🤖 Bot User: {self.user} (ID: {self.user.id})")
        print(f"👑 Master Owner ID: {OWNER_ID}")
        print(f"🏰 Serving Guilds: {[g.name for g in self.guilds]}")
        print(f"🎀 Privileged Intents: {'Enabled (Full Auto-Role & Welcome)' if self.privileged_enabled else 'Disabled in Portal (Standard Mode)'}")
        print("=" * 60)

        # Set cute Kawaii Discord presence
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="Master 🌸 | /panel ✨"
        )
        await self.change_presence(status=discord.Status.online, activity=activity)

    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        await self.process_commands(message)

async def run_bot():
    if not DISCORD_TOKEN:
        print("❌ Error: DISCORD_TOKEN is missing! Please set it in .env.", file=sys.stderr)
        sys.exit(1)

    privileged = os.getenv("PRIVILEGED_INTENTS", "true").lower() in ("true", "1", "yes")
    print(f"🌸 Starting Destiny Bot (Privileged Intents: {'ON' if privileged else 'OFF - Standard Mode'})... ✨")

    try:
        bot = DestinyBot(privileged_intents=privileged)
        async with bot:
            await bot.start(DISCORD_TOKEN)
    except discord.errors.PrivilegedIntentsRequired:
        print("\n" + "=" * 60)
        print("⚠️ [NOTE] Server Members Intent is not yet turned ON in Discord Developer Portal!")
        print("🌸 Falling back to Standard Mode so your bot, /panel, moderation,")
        print("   giveaways, announcements, and web dashboard work 100%!")
        print("🎀 (To enable Auto-role on join and Welcome cards on join,")
        print("   enable 'Server Members Intent' under Bot tab in Developer Portal)")
        print("=" * 60 + "\n")
        bot = DestinyBot(privileged_intents=False)
        async with bot:
            await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(run_bot())
    except (KeyboardInterrupt, SystemExit):
        print("🌸 Destiny Bot shutdown gracefully. Bye bye! (｡♥‿♥｡)")
