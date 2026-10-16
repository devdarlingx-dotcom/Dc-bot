import discord
from discord import app_commands
from discord.ext import commands
import database
from config import is_owner, denied_embed, make_kawaii_embed, COLOR_MINT, COLOR_PINK, COLOR_WARN

class AutoRole(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Automatically assigns the configured default role to new members."""
        try:
            settings = await database.get_guild_settings(member.guild.id)
            role_id = settings.get("autorole_id")
            if role_id:
                role = member.guild.get_role(role_id)
                if role:
                    await member.add_roles(role, reason="Destiny Auto-Role on join")
        except Exception as e:
            print(f"Error in on_member_join autorole: {e}")

    autorole_group = app_commands.Group(
        name="autorole",
        description="🌸 Configure automatic role assignment on join"
    )

    @autorole_group.command(name="set", description="🌸 Set the default role granted to new members upon joining")
    @app_commands.describe(role="The role to automatically grant")
    async def set_role(self, interaction: discord.Interaction, role: discord.Role):
        if not is_owner(interaction.user.id):
            return await interaction.response.send_message(embed=denied_embed(), ephemeral=True)

        bot_member = interaction.guild.get_member(self.bot.user.id)
        if role >= bot_member.top_role:
            embed = make_kawaii_embed(
                title="✦ Role Hierarchy Error",
                description=(
                    f"The role **{role.name}** is positioned higher than the `Destiny` bot role.\n"
                    "Please move `Destiny` higher in **Server Settings -> Roles**."
                ),
                color=COLOR_WARN
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        await database.set_autorole(interaction.guild_id, role.id)
        embed = make_kawaii_embed(
            title="✦ Auto-Role Enabled",
            description=f"New members will now receive **{role.mention}** upon joining. 🌸",
            color=COLOR_MINT
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @autorole_group.command(name="disable", description="🌸 Turn off auto-role assignment")
    async def disable_role(self, interaction: discord.Interaction):
        if not is_owner(interaction.user.id):
            return await interaction.response.send_message(embed=denied_embed(), ephemeral=True)

        await database.set_autorole(interaction.guild_id, None)
        embed = make_kawaii_embed(
            title="✦ Auto-Role Disabled",
            description="Automatic role assignment has been disabled. 🌸",
            color=COLOR_PINK
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @autorole_group.command(name="status", description="🌸 Check current auto-role configuration")
    async def status_role(self, interaction: discord.Interaction):
        if not is_owner(interaction.user.id):
            return await interaction.response.send_message(embed=denied_embed(), ephemeral=True)

        settings = await database.get_guild_settings(interaction.guild_id)
        role_id = settings.get("autorole_id")
        if role_id:
            role = interaction.guild.get_role(role_id)
            desc = f"✦ Current Auto-Role: **{role.mention if role else f'Unknown Role ({role_id})'}**"
        else:
            desc = "✦ Auto-Role is currently **Disabled**."

        embed = make_kawaii_embed(
            title="✦ Auto-Role Status",
            description=desc,
            color=COLOR_PINK
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(AutoRole(bot))
