import os
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

# Aesthetic Pastel Palette
COLOR_PINK = 0xFFB6C1
COLOR_ROSE = 0xF4A7B9
COLOR_PURPLE = 0xD8B4E2
COLOR_LAVENDER = 0xE6E6FA
COLOR_MINT = 0xB5EAD7
COLOR_PEACH = 0xFFD1DC
COLOR_ERROR = 0xFF9AA2
COLOR_WARN = 0xFFDAC1
COLOR_SUCCESS = 0xB5EAD7

def is_owner(user_id: int) -> bool:
    """Strictly checks if user matches the bot owner ID."""
    return user_id == OWNER_ID

def denied_embed() -> discord.Embed:
    """Clean aesthetic embed shown when an unauthorized user attempts an action."""
    embed = discord.Embed(
        title="✦ Access Restricted",
        description=f"Only Master <@{OWNER_ID}> can use this control. 🌸",
        color=COLOR_ERROR
    )
    embed.set_footer(text="Destiny ✦ Master Only")
    return embed

def make_kawaii_embed(
    title: str,
    description: str,
    color: int = COLOR_PINK,
    thumbnail: str = None,
    image: str = None,
    footer: str = None
) -> discord.Embed:
    """Generates clean, aesthetic pastel embeds with consistent styling."""
    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    if image:
        embed.set_image(url=image)
        
    embed.set_footer(text=footer if footer else "Destiny ✦ Aesthetic System")
    return embed
