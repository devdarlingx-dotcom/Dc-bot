import os
import random
from dotenv import load_dotenv
import discord

# Load environment variables
load_dotenv()

# Bot Credentials & Configuration
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
OWNER_ID = int(os.getenv("OWNER_ID", "1560466119880347730"))
PORT = int(os.getenv("PORT", "5000"))
DASHBOARD_SECRET = os.getenv("DASHBOARD_SECRET", "destiny_kawaii_key_2026")
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/destiny.db")

# Kawaii Pastel Palette
COLOR_PINK = 0xFFB6C1
COLOR_LAVENDER = 0xE6E6FA
COLOR_PURPLE = 0xDDA0DD
COLOR_MINT = 0xB5EAD7
COLOR_ROSE = 0xFF69B4
COLOR_PEACH = 0xFFDAB9
COLOR_BABY_BLUE = 0xAEE3F5
COLOR_SUCCESS = 0xBAEDC7
COLOR_ERROR = 0xFFABAB
COLOR_WARN = 0xFFDFBA

# Kaomojis & Emojis
KAWAII_HAPPY = [
    "(◕‿◕✿)",
    "(｡♥‿♥｡)",
    "(੭ˊᵕˋ)੭",
    "(*^▽^*)",
    "(✿◠‿◠)",
    "(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧",
    "(づ｡◕‿‿◕｡)づ",
    "(◕ᴗ◕✿)"
]

KAWAII_SAD = [
    "(｡•́︿•̀｡)",
    "(◞‸◟；)",
    "(つω`｡)",
    "(,,>﹏<,,)"
]

KAWAII_DENIED = [
    "(¬_¬)",
    "(>_<)",
    "(｡•́︿•̀｡)"
]

def random_happy() -> str:
    return random.choice(KAWAII_HAPPY)

def random_sad() -> str:
    return random.choice(KAWAII_SAD)

def is_owner(user_id: int) -> bool:
    """Strictly checks if user matches the bot owner ID."""
    return user_id == OWNER_ID

def denied_embed() -> discord.Embed:
    """Cute embed shown when someone other than the owner tries an admin action."""
    embed = discord.Embed(
        title="🌸 Access Denied! " + random.choice(KAWAII_DENIED),
        description=(
            f"(¬_¬) Gomen ne! Only my lovely master <@{OWNER_ID}> is authorized "
            "to control me! 🌸✨\n\n"
            "*Please contact the owner if you think this is a mistake.*"
        ),
        color=COLOR_ERROR
    )
    embed.set_footer(text="Destiny Kawaii Guard • Protected 🎀")
    return embed

def make_kawaii_embed(
    title: str,
    description: str,
    color: int = COLOR_PINK,
    thumbnail: str = None,
    image: str = None,
    footer: str = None
) -> discord.Embed:
    """Helper to generate consistent kawaii pastel embeds."""
    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    if image:
        embed.set_image(url=image)
        
    footer_text = footer if footer else f"Destiny Kawaii Bot • {random_happy()} ✨"
    embed.set_footer(text=footer_text)
    return embed
