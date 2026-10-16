import datetime
import discord
from discord import app_commands
from discord.ext import commands
from config import is_owner, denied_embed, make_kawaii_embed, COLOR_ERROR, COLOR_SUCCESS, COLOR_WARN, random_sad, random_happy

class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ban", description="🌸 Ban a user with kawaii care")
    @app_commands.describe(
        member="The member to ban",
        reason="Reason for the ban",
        delete_message_days="Days of message history to delete (0 to 7)"
    )
    async def ban(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "Disrupting the kawaii peace",
        delete_message_days: int = 0
    ):
        if not is_owner(interaction.user.id):
            return await interaction.response.send_message(embed=denied_embed(), ephemeral=True)

        if member.id == interaction.user.id:
            return await interaction.response.send_message("🌸 You cannot ban yourself, silly master! (,,>﹏<,,)", ephemeral=True)

        # Attempt polite DM before banning
        try:
            dm_embed = make_kawaii_embed(
                title=f"🌸 You have been banned from {interaction.guild.name} {random_sad()}",
                description=f"**Reason:** {reason}\n\n*Please reflect on the server rules. Take care!*",
                color=COLOR_ERROR
            )
            await member.send(embed=dm_embed)
        except Exception:
            pass  # DMs might be closed

        try:
            await member.ban(reason=f"{reason} (by {interaction.user})", delete_message_days=delete_message_days)
            embed = make_kawaii_embed(
                title=f"🌸 Member Banned! {random_sad()}",
                description=f"**User:** {member.mention} (`{member.id}`)\n**Reason:** {reason}\n**Moderator:** {interaction.user.mention}",
                color=COLOR_ERROR
            )
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"🌸 Failed to ban member: {e} (｡•́︿•̀｡)", ephemeral=True)

    @app_commands.command(name="kick", description="🌸 Kick a member from the server")
    @app_commands.describe(
        member="The member to kick",
        reason="Reason for kicking"
    )
    async def kick(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "Disrupting the kawaii vibes"
    ):
        if not is_owner(interaction.user.id):
            return await interaction.response.send_message(embed=denied_embed(), ephemeral=True)

        if member.id == interaction.user.id:
            return await interaction.response.send_message("🌸 You cannot kick yourself, master! (,,>﹏<,,)", ephemeral=True)

        try:
            dm_embed = make_kawaii_embed(
                title=f"🌸 You were kicked from {interaction.guild.name} {random_sad()}",
                description=f"**Reason:** {reason}\n\n*You may rejoin if you respect server guidelines!*",
                color=COLOR_WARN
            )
            await member.send(embed=dm_embed)
        except Exception:
            pass

        try:
            await member.kick(reason=f"{reason} (by {interaction.user})")
            embed = make_kawaii_embed(
                title=f"🌸 Member Kicked! {random_sad()}",
                description=f"**User:** {member.mention} (`{member.id}`)\n**Reason:** {reason}\n**Moderator:** {interaction.user.mention}",
                color=COLOR_WARN
            )
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"🌸 Failed to kick member: {e} (｡•́︿•̀｡)", ephemeral=True)

    @app_commands.command(name="timeout", description="🌸 Silence/timeout a member for a specified duration")
    @app_commands.describe(
        member="The member to mute/timeout",
        duration_minutes="Duration in minutes (e.g. 5, 60, 1440)",
        reason="Reason for timeout"
    )
    async def timeout(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        duration_minutes: int,
        reason: str = "Time to calm down and have some tea 🍵"
    ):
        if not is_owner(interaction.user.id):
            return await interaction.response.send_message(embed=denied_embed(), ephemeral=True)

        if duration_minutes <= 0:
            return await interaction.response.send_message("🌸 Duration must be greater than 0 minutes! (｡•́︿•̀｡)", ephemeral=True)

        until = discord.utils.utcnow() + datetime.timedelta(minutes=duration_minutes)

        try:
            await member.timeout(until, reason=f"{reason} (by {interaction.user})")
            embed = make_kawaii_embed(
                title=f"🌸 Member Silenced! (つω`｡)",
                description=(
                    f"**User:** {member.mention} (`{member.id}`)\n"
                    f"**Duration:** {duration_minutes} minute(s)\n"
                    f"**Reason:** {reason}\n"
                    f"**Until:** <t:{int(until.timestamp())}:R>"
                ),
                color=COLOR_WARN
            )
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"🌸 Failed to timeout member: {e} (｡•́︿•̀｡)", ephemeral=True)

    @app_commands.command(name="unmute", description="🌸 Remove timeout / unmute a member")
    @app_commands.describe(
        member="The member to unmute",
        reason="Reason for unmuting"
    )
    async def unmute(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "Timeout cleared with love 🌸"
    ):
        if not is_owner(interaction.user.id):
            return await interaction.response.send_message(embed=denied_embed(), ephemeral=True)

        try:
            await member.timeout(None, reason=f"{reason} (by {interaction.user})")
            embed = make_kawaii_embed(
                title=f"🌸 Member Unmuted! {random_happy()}",
                description=f"**User:** {member.mention}\n**Status:** Voice & Chat permissions restored! ✨",
                color=COLOR_SUCCESS
            )
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"🌸 Failed to unmute member: {e} (｡•́︿•̀｡)", ephemeral=True)

    @app_commands.command(name="purge", description="🌸 Clean up a number of messages from this channel")
    @app_commands.describe(amount="Number of messages to delete (1 - 100)")
    async def purge(self, interaction: discord.Interaction, amount: int):
        if not is_owner(interaction.user.id):
            return await interaction.response.send_message(embed=denied_embed(), ephemeral=True)

        if amount < 1 or amount > 100:
            return await interaction.response.send_message("🌸 Please specify an amount between 1 and 100! (｡•́︿•̀｡)", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=amount)
        embed = make_kawaii_embed(
            title=f"🌸 Channel Tidied Up! {random_happy()}",
            description=f"Deleted **{len(deleted)}** messages! The room is sparkling clean again! ✨🧹",
            color=COLOR_SUCCESS
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
