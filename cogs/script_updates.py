import time
import discord
from discord import app_commands
from discord.ext import commands
import database
from config import is_owner, denied_embed, make_kawaii_embed, COLOR_PURPLE, COLOR_ROSE, COLOR_MINT

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
        """Builds and broadcasts a clean, aesthetic script update release card."""
        current_time = int(time.time())
        clean_changelog = changelog.strip()

        # Format changelog nicely with diff prefix if lines don't already have one
        formatted_lines = []
        for line in clean_changelog.splitlines():
            line_str = line.strip()
            if not line_str:
                continue
            if line_str.startswith(("+", "-", "*")):
                formatted_lines.append(f"+ {line_str.lstrip('+-* ')}")
            else:
                formatted_lines.append(f"+ {line_str}")
        diff_changelog = "\n".join(formatted_lines) if formatted_lines else clean_changelog

        embed = discord.Embed(
            title=f"🌸 {script_name} ✦ `v{version}`",
            description=(
                f"> ### ✦ CHANGELOG\n"
                f"```diff\n{diff_changelog}\n```\n"
                f"**Developer:** {author}\n"
                f"**Version:** `v{version}`\n"
                f"**Date:** <t:{current_time}:D>"
            ),
            color=COLOR_PURPLE
        )
        embed.set_author(name="DESTINY SCRIPTS ✦ RELEASE", icon_url=self.bot.user.display_avatar.url)
        embed.set_footer(text=f"Destiny ✦ Script Updates")

        view = discord.ui.View()
        if download_url and (download_url.startswith("http://") or download_url.startswith("https://")):
            view.add_item(discord.ui.Button(
                label=f"Download {script_name} v{version}",
                url=download_url,
                emoji="✦"
            ))

        content = ping_role.mention if ping_role else None
        await channel.send(content=content, embed=embed, view=view if len(view.children) > 0 else None)
        await database.save_script_update(script_name, version, clean_changelog, download_url or "")

    @app_commands.command(name="update-script", description="🌸 Announce a clean, aesthetic script update")
    @app_commands.describe(
        script_name="Name of the script",
        version="Version tag (e.g. 2.1.0)",
        changelog="List of changes / improvements",
        download_url="Direct download or website URL",
        channel="Target channel for announcement",
        ping_role="Optional role to mention"
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
            title="✦ Script Update Published",
            description=f"Announced **{script_name} v{version}** in {target_channel.mention}. 🌸",
            color=COLOR_MINT
        )
        await interaction.response.send_message(embed=reply, ephemeral=True)

    @app_commands.command(name="script-history", description="🌸 View recent script release logs")
    async def script_history(self, interaction: discord.Interaction):
        updates = await database.get_recent_script_updates(limit=5)
        if not updates:
            return await interaction.response.send_message(
                "✦ No script updates logged yet.",
                ephemeral=True
            )

        desc = ""
        for u in updates:
            desc += f"✦ **{u['script_name']}** `v{u['version']}`\n"
            desc += f"> {u['changelog'][:90]}...\n\n"

        embed = make_kawaii_embed(
            title="✦ Script Releases History",
            description=desc,
            color=COLOR_ROSE
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(ScriptUpdates(bot))
