import discord
from discord import app_commands
from discord.ext import commands
from config import is_owner, denied_embed, make_kawaii_embed, COLOR_PINK, COLOR_MINT, random_happy

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
            title=f"🌸 Message Sent! {random_happy()}",
            description=f"Your message was successfully sent to {channel.mention}! ✨",
            color=COLOR_MINT
        )
        await interaction.response.send_message(embed=reply, ephemeral=True)

    @app_commands.command(name="announce", description="🌸 Broadcast a beautiful kawaii embed announcement")
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

        embed = make_kawaii_embed(
            title=f"🌸 {title} ✨",
            description=description,
            color=COLOR_PINK,
            image=image_url
        )
        embed.set_author(name="Server Announcement", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)

        content = ping_role.mention if ping_role else None
        await channel.send(content=content, embed=embed)

        reply = make_kawaii_embed(
            title=f"🌸 Announcement Posted! {random_happy()}",
            description=f"Your announcement was published to {channel.mention}! 🎀",
            color=COLOR_MINT
        )
        await interaction.response.send_message(embed=reply, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Announcements(bot))
