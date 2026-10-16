import discord
from discord import app_commands
from discord.ext import commands
import database
from config import is_owner, denied_embed, make_kawaii_embed, COLOR_PINK, COLOR_MINT, COLOR_PURPLE, random_happy

class ScriptUpdates(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def broadcast_update(
        self,
        script_name: str,
        version: str,
        changelog: str,
        download_url: str = None,
        channel: discord.TextChannel = None,
        ping_role: discord.Role = None,
        author: str = "Master"
    ):
        """Helper used by both slash command and web dashboard."""
        embed = discord.Embed(
            title=f"🌸✨ NEW SCRIPT UPDATE: {script_name} ✨🌸",
            description=(
                f"A new sparkling update has been released for **{script_name}**! (੭ˊᵕˋ)੭ 💕\n\n"
                f"🏷️ **Version:** `v{version}`\n"
                f"👤 **Author:** {author}\n\n"
                f"📝 **What's New / Changelog:**\n```markdown\n{changelog}\n```"
            ),
            color=COLOR_PURPLE
        )
        if download_url:
            embed.add_field(
                name="📦 Get The Script",
                value=f"[🌸 Click here to Download / View Script]({download_url})",
                inline=False
            )
        embed.set_footer(text=f"Destiny Script Notifier • {random_happy()} ✨")

        view = discord.ui.View()
        if download_url and (download_url.startswith("http://") or download_url.startswith("https://")):
            view.add_item(discord.ui.Button(
                label=f"Download {script_name} v{version}",
                url=download_url,
                emoji="🚀"
            ))

        content = ping_role.mention if ping_role else None
        await channel.send(content=content, embed=embed, view=view if len(view.children) > 0 else None)
        await database.save_script_update(script_name, version, changelog, download_url or "")

    @app_commands.command(name="update-script", description="🌸 Announce a new script update or release")
    @app_commands.describe(
        script_name="Name of your awesome script",
        version="Version string (e.g. 1.2.0 or 2.0)",
        changelog="What changed or was improved in this update",
        download_url="Optional link or download page for the script",
        channel="Channel to post the update in (defaults to current)",
        ping_role="Optional role to mention for notifications"
    )
    async def update_script_cmd(
        self,
        interaction: discord.Interaction,
        script_name: str,
        version: str,
        changelog: str,
        download_url: str = None,
        channel: discord.TextChannel = None,
        ping_role: discord.Role = None
    ):
        if not is_owner(interaction.user.id):
            return await interaction.response.send_message(embed=denied_embed(), ephemeral=True)

        target_channel = channel or interaction.channel
        await self.broadcast_update(
            script_name=script_name,
            version=version,
            changelog=changelog,
            download_url=download_url,
            channel=target_channel,
            ping_role=ping_role,
            author=interaction.user.mention
        )

        reply = make_kawaii_embed(
            title=f"🌸 Script Update Published! {random_happy()}",
            description=f"Successfully announced **{script_name} v{version}** in {target_channel.mention}! 🚀✨",
            color=COLOR_MINT
        )
        await interaction.response.send_message(embed=reply, ephemeral=True)

    @app_commands.command(name="script-history", description="🌸 View recent script updates log")
    async def script_history(self, interaction: discord.Interaction):
        updates = await database.get_recent_script_updates(limit=5)
        if not updates:
            return await interaction.response.send_message(
                "🌸 No script updates recorded yet! (｡•́︿•̀｡)",
                ephemeral=True
            )

        desc = ""
        for u in updates:
            desc += f"🌸 **{u['script_name']}** `v{u['version']}`\n"
            desc += f"> *{u['changelog'][:80]}...*\n\n"

        embed = make_kawaii_embed(
            title="🌸 Recent Script Updates History",
            description=desc,
            color=COLOR_PINK
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(ScriptUpdates(bot))
