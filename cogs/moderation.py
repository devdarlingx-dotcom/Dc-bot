import datetime
import discord
from discord import app_commands
from discord.ext import commands
from config import is_owner, denied_embed, make_kawaii_embed, COLOR_ERROR, COLOR_SUCCESS, COLOR_WARN

class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ban", description="🌸 Ban a user from the server")
    @app_commands.describe(
        member="Member to ban",
        reason="Reason for the ban",
        delete_message_days="Days of messages to delete (0 to 7)"
    )
    async def ban(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "Violation of server guidelines",
        delete_message_days: int = 0
    ):
        if not is_owner(interaction.user.id):
            return await interaction.response.send_message(embed=denied_embed(), ephemeral=True)

        if member.id == interaction.user.id:
            return await interaction.response.send_message("✦ You cannot ban yourself.", ephemeral=True)

        try:
            dm_embed = discord.Embed(
                title=f"✦ BANNED FROM {interaction.guild.name.upper()} ✦",
                description=f"**Reason:** {reason}",
                color=COLOR_ERROR
            )
            dm_embed.set_footer(text="Destiny ✦ Moderation Notice")
            await member.send(embed=dm_embed)
        except Exception:
            pass

        try:
            await member.ban(reason=f"{reason} (by {interaction.user})", delete_message_days=delete_message_days)
            embed = discord.Embed(
                title="✦ MEMBER BANNED ✦",
                description=(
                    f"**User:** {member.mention} (`{member.id}`)\n"
                    f"**Reason:** {reason}\n"
                    f"**Moderator:** {interaction.user.mention}"
                ),
                color=COLOR_ERROR
            )
            embed.set_footer(text="Destiny ✦ Moderation Log")
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"✦ Failed to ban member: {e}", ephemeral=True)

    @app_commands.command(name="kick", description="🌸 Kick a member from the server")
    @app_commands.describe(
        member="Member to kick",
        reason="Reason for kicking"
    )
    async def kick(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "Violation of server guidelines"
    ):
        if not is_owner(interaction.user.id):
            return await interaction.response.send_message(embed=denied_embed(), ephemeral=True)

        if member.id == interaction.user.id:
            return await interaction.response.send_message("✦ You cannot kick yourself.", ephemeral=True)

        try:
            dm_embed = discord.Embed(
                title=f"✦ KICKED FROM {interaction.guild.name.upper()} ✦",
                description=f"**Reason:** {reason}",
                color=COLOR_WARN
            )
            dm_embed.set_footer(text="Destiny ✦ Moderation Notice")
            await member.send(embed=dm_embed)
        except Exception:
            pass

        try:
            await member.kick(reason=f"{reason} (by {interaction.user})")
            embed = discord.Embed(
                title="✦ MEMBER KICKED ✦",
                description=(
                    f"**User:** {member.mention} (`{member.id}`)\n"
                    f"**Reason:** {reason}\n"
                    f"**Moderator:** {interaction.user.mention}"
                ),
                color=COLOR_WARN
            )
            embed.set_footer(text="Destiny ✦ Moderation Log")
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"✦ Failed to kick member: {e}", ephemeral=True)

    @app_commands.command(name="timeout", description="🌸 Silence a member for a duration")
    @app_commands.describe(
        member="Member to timeout",
        duration_minutes="Duration in minutes",
        reason="Reason for timeout"
    )
    async def timeout(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        duration_minutes: int,
        reason: str = "Temporary timeout"
    ):
        if not is_owner(interaction.user.id):
            return await interaction.response.send_message(embed=denied_embed(), ephemeral=True)

        if duration_minutes <= 0:
            return await interaction.response.send_message("✦ Duration must be at least 1 minute.", ephemeral=True)

        until = discord.utils.utcnow() + datetime.timedelta(minutes=duration_minutes)

        try:
            await member.timeout(until, reason=f"{reason} (by {interaction.user})")
            embed = discord.Embed(
                title="✦ MEMBER TIMED OUT ✦",
                description=(
                    f"**User:** {member.mention} (`{member.id}`)\n"
                    f"**Duration:** `{duration_minutes}m`\n"
                    f"**Until:** <t:{int(until.timestamp())}:R>\n"
                    f"**Reason:** {reason}\n"
                    f"**Moderator:** {interaction.user.mention}"
                ),
                color=COLOR_WARN
            )
            embed.set_footer(text="Destiny ✦ Moderation Log")
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"✦ Failed to timeout member: {e}", ephemeral=True)

    @app_commands.command(name="unmute", description="🌸 Remove timeout / unmute a member")
    @app_commands.describe(
        member="Member to unmute",
        reason="Reason for unmuting"
    )
    async def unmute(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "Timeout cleared"
    ):
        if not is_owner(interaction.user.id):
            return await interaction.response.send_message(embed=denied_embed(), ephemeral=True)

        try:
            await member.timeout(None, reason=f"{reason} (by {interaction.user})")
            embed = discord.Embed(
                title="✦ TIMEOUT REMOVED ✦",
                description=(
                    f"**User:** {member.mention}\n"
                    f"**Status:** Normal permissions restored.\n"
                    f"**Moderator:** {interaction.user.mention}"
                ),
                color=COLOR_SUCCESS
            )
            embed.set_footer(text="Destiny ✦ Moderation Log")
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"✦ Failed to unmute member: {e}", ephemeral=True)

    @app_commands.command(name="purge", description="🌸 Clean up a number of messages")
    @app_commands.describe(amount="Number of messages to delete (1 - 100)")
    async def purge(self, interaction: discord.Interaction, amount: int):
        if not is_owner(interaction.user.id):
            return await interaction.response.send_message(embed=denied_embed(), ephemeral=True)

        if amount < 1 or amount > 100:
            return await interaction.response.send_message("✦ Amount must be between 1 and 100.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=amount)
        reply = make_kawaii_embed(
            title="✦ Messages Cleared",
            description=f"Deleted **{len(deleted)}** messages from {interaction.channel.mention}. 🌸",
            color=COLOR_SUCCESS
        )
        await interaction.followup.send(embed=reply, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
