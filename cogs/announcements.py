import discord
from discord import app_commands
from discord.ext import commands
from config import is_owner, denied_embed, make_kawaii_embed, COLOR_PINK, COLOR_MINT

class Announcements(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="say", description="🌸 Send a plain message to any channel as Destiny")
    @app_commands.describe(
        channel="Channel to send the message in",
        message="The message text"
    )
    async def say(self, interaction: discord.Interaction, channel: discord.TextChannel, message: str):
        if not is_owner(interaction.user.id):
            return await interaction.response.send_message(embed=denied_embed(), ephemeral=True)

        await channel.send(message)
        reply = make_kawaii_embed(
            title="✦ Message Delivered",
            description=f"Message sent to {channel.mention}. 🌸",
            color=COLOR_MINT
        )
        await interaction.response.send_message(embed=reply, ephemeral=True)

    @app_commands.command(name="announce", description="🌸 Broadcast a clean, aesthetic announcement")
    @app_commands.describe(
        channel="Target announcement channel",
        title="Title of the announcement",
        description="Main announcement content",
        ping_role="Optional role to mention (e.g. @everyone or a specific role)",
        image_url="Optional banner image URL to display"
    )
    async def announce(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        title: str,
        description: str,
        ping_role: discord.Role = None,
        image_url: str = None
    ):
        if not is_owner(interaction.user.id):
            return await interaction.response.send_message(embed=denied_embed(), ephemeral=True)

        embed = discord.Embed(
            title=f"✦ {title.upper()} ✦",
            description=description,
            color=COLOR_PINK
        )
        if interaction.guild.icon:
            embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon.url)
        else:
            embed.set_author(name=interaction.guild.name)

        if image_url:
            embed.set_image(url=image_url)

        embed.set_footer(text="Destiny ✦ Server Announcement")

        content = ping_role.mention if ping_role else None
        await channel.send(content=content, embed=embed)

        reply = make_kawaii_embed(
            title="✦ Announcement Published",
            description=f"Broadcasted to {channel.mention}. 🌸",
            color=COLOR_MINT
        )
        await interaction.response.send_message(embed=reply, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Announcements(bot))
