import os
import jinja2
from aiohttp import web
import database
from config import PORT, DASHBOARD_SECRET, make_kawaii_embed, COLOR_PINK

class WebDashboard:
    def __init__(self, bot):
        self.bot = bot
        self.app = web.Application()
        base_dir = os.path.dirname(__file__)
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(os.path.join(base_dir, "templates")),
            enable_async=True
        )
        self.setup_routes(base_dir)

    def setup_routes(self, base_dir):
        self.app.router.add_static("/static", os.path.join(base_dir, "static"))
        self.app.router.add_get("/", self.handle_index)
        self.app.router.add_post("/login", self.handle_login)
        self.app.router.add_post("/api/announce", self.handle_announce)
        self.app.router.add_post("/api/script-update", self.handle_script_update)
        self.app.router.add_post("/api/settings", self.handle_settings)
        self.app.router.add_get("/health", self.handle_health)

    def is_authenticated(self, request: web.Request) -> bool:
        secret_query = request.query.get("secret")
        if secret_query == DASHBOARD_SECRET:
            return True
        secret_cookie = request.cookies.get("destiny_auth")
        return secret_cookie == DASHBOARD_SECRET

    async def handle_health(self, request: web.Request):
        return web.json_response({
            "status": "sparkly",
            "bot": "Destiny",
            "online": self.bot.is_ready()
        })

    async def handle_login(self, request: web.Request):
        data = await request.post()
        secret = data.get("secret", "").strip()
        if secret == DASHBOARD_SECRET:
            response = web.HTTPFound("/")
            response.set_cookie("destiny_auth", secret, max_age=86400 * 30, httponly=True)
            return response
        else:
            template = self.jinja_env.get_template("dashboard.html")
            html = await template.render_async(
                authenticated=False,
                error="Invalid secret key! Access denied."
            )
            return web.Response(text=html, content_type="text/html")

    async def handle_index(self, request: web.Request):
        authenticated = self.is_authenticated(request)
        template = self.jinja_env.get_template("dashboard.html")

        if not authenticated:
            html = await template.render_async(authenticated=False, error=None)
            return web.Response(text=html, content_type="text/html")

        # Get first available guild
        guild = self.bot.guilds[0] if self.bot.guilds else None
        guild_members = guild.member_count if guild else 0
        bot_ping = round(self.bot.latency * 1000) if self.bot.latency else 0

        channels = []
        roles = []
        autorole_name = "Disabled"
        current_autorole_id = None
        current_welcome_channel_id = None

        if guild:
            channels = [{"id": str(c.id), "name": c.name} for c in guild.text_channels]
            roles = [{"id": str(r.id), "name": r.name} for r in guild.roles if r.name != "@everyone"]
            
            settings = await database.get_guild_settings(guild.id)
            current_autorole_id = str(settings.get("autorole_id")) if settings.get("autorole_id") else None
            current_welcome_channel_id = str(settings.get("welcome_channel_id")) if settings.get("welcome_channel_id") else None

            if current_autorole_id:
                r_obj = guild.get_role(int(current_autorole_id))
                if r_obj:
                    autorole_name = r_obj.name

        html = await template.render_async(
            authenticated=True,
            guild_members=guild_members,
            bot_ping=bot_ping,
            autorole_name=autorole_name,
            current_autorole_id=current_autorole_id,
            current_welcome_channel_id=current_welcome_channel_id,
            channels=channels,
            roles=roles
        )
        return web.Response(text=html, content_type="text/html")

    async def handle_announce(self, request: web.Request):
        if not self.is_authenticated(request):
            return web.HTTPUnauthorized()

        data = await request.post()
        channel_id = int(data.get("channel_id"))
        title = data.get("title", "Announcement")
        description = data.get("description", "")

        channel = self.bot.get_channel(channel_id)
        if channel:
            embed = make_kawaii_embed(
                title=f"🌸 {title} ✨",
                description=description,
                color=COLOR_PINK
            )
            await channel.send(embed=embed)

        return web.HTTPFound("/")

    async def handle_script_update(self, request: web.Request):
        if not self.is_authenticated(request):
            return web.HTTPUnauthorized()

        data = await request.post()
        channel_id = int(data.get("channel_id"))
        script_name = data.get("script_name")
        version = data.get("version")
        changelog = data.get("changelog")
        download_url = data.get("download_url")

        channel = self.bot.get_channel(channel_id)
        cog = self.bot.get_cog("ScriptUpdates")
        if channel and cog:
            await cog.broadcast_update(
                script_name=script_name,
                version=version,
                changelog=changelog,
                download_url=download_url if download_url else None,
                channel=channel,
                author="Master (via Dashboard)"
            )

        return web.HTTPFound("/")

    async def handle_settings(self, request: web.Request):
        if not self.is_authenticated(request):
            return web.HTTPUnauthorized()

        data = await request.post()
        autorole_id = int(data.get("autorole_id")) if data.get("autorole_id") else None
        welcome_id = int(data.get("welcome_channel_id")) if data.get("welcome_channel_id") else None

        guild = self.bot.guilds[0] if self.bot.guilds else None
        if guild:
            await database.set_autorole(guild.id, autorole_id)
            await database.set_welcome_channel(guild.id, welcome_id)

        return web.HTTPFound("/")

async def start_web_server(bot):
    dashboard = WebDashboard(bot)
    runner = web.AppRunner(dashboard.app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"🌸 Destiny Kawaii Web Dashboard running on http://0.0.0.0:{PORT} ✨")
