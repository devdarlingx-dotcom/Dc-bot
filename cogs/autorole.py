import asyncio
import discord
from discord import app_commands
from discord.ext import commands
import database
from config import is_owner, denied_embed, make_kawaii_embed, COLOR_MINT, COLOR_PINK, COLOR_ROSE, COLOR_WARN

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

    # --- Mass Role Transfer Feature ---
    @app_commands.command(name="role-transfer", description="🌸 Transfer all members from one role to another at once")
    @app_commands.describe(
        from_role="Role members currently have",
        to_role="New role to give everyone",
        remove_old_role="Whether to remove the old role after granting the new one"
    )
    async def role_transfer(
        self,
        interaction: discord.Interaction,
        from_role: discord.Role,
        to_role: discord.Role,
        remove_old_role: bool = True
    ):
        if not is_owner(interaction.user.id):
            return await interaction.response.send_message(embed=denied_embed(), ephemeral=True)

        bot_member = interaction.guild.get_member(self.bot.user.id)
        if to_role >= bot_member.top_role or from_role >= bot_member.top_role:
            embed = make_kawaii_embed(
                title="✦ Role Hierarchy Error",
                description=(
                    "One of the specified roles is higher than or equal to the `Destiny` bot role.\n"
                    "Please ensure `Destiny` is above both roles in **Server Settings -> Roles**."
                ),
                color=COLOR_WARN
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        await interaction.response.defer(thinking=True)

        # Collect target members
        guild = interaction.guild
        members_to_process = []

        # If cache is partial, fetch all members
        if len(guild.members) < guild.member_count:
            try:
                async for m in guild.fetch_members(limit=None):
                    if from_role in m.roles:
                        members_to_process.append(m)
            except Exception:
                members_to_process = [m for m in guild.members if from_role in m.roles]
        else:
            members_to_process = [m for m in guild.members if from_role in m.roles]

        total = len(members_to_process)
        if total == 0:
            return await interaction.followup.send(
                f"✦ No members found currently holding the role {from_role.mention}."
            )

        progress_msg = await interaction.followup.send(
            f"✦ Starting mass role transfer for **{total}** members... 🌸"
        )

        success_count = 0
        error_count = 0

        for i, member in enumerate(members_to_process, 1):
            try:
                # Add new role if they don't have it
                if to_role not in member.roles:
                    await member.add_roles(to_role, reason=f"Mass role transfer by Master {interaction.user}")

                # Remove old role if requested
                if remove_old_role and from_role in member.roles:
                    await member.remove_roles(from_role, reason=f"Mass role transfer by Master {interaction.user}")

                success_count += 1

                # Update progress periodically to avoid rate limits
                if i % 10 == 0 or i == total:
                    try:
                        await progress_msg.edit(content=f"✦ Transferring roles... `{i}/{total}` completed.")
                    except Exception:
                        pass

                # Short delay to respect Discord API rate limits
                await asyncio.sleep(0.35)

            except Exception as e:
                print(f"Error transferring role for {member}: {e}")
                error_count += 1

        embed = discord.Embed(
            title="✦ MASS ROLE TRANSFER COMPLETE ✦",
            description=(
                f"**From:** {from_role.mention}\n"
                f"**To:** {to_role.mention}\n"
                f"**Members Migrated:** `{success_count}/{total}`\n"
                f"**Removed Previous Role:** `{'Yes' if remove_old_role else 'No'}`\n"
                f"**Errors/Skipped:** `{error_count}`"
            ),
            color=COLOR_MINT
        )
        embed.set_footer(text="Destiny ✦ Role Operations")
        await progress_msg.edit(content=None, embed=embed)

    @commands.command(name="transfer", aliases=["roletransfer", "migrateroles"])
    async def prefix_role_transfer(
        self,
        ctx: commands.Context,
        from_role: discord.Role,
        to_role: discord.Role,
        remove_old_role: bool = True
    ):
        """Prefix command: !transfer @from_role @to_role [remove_old_role=True]"""
        if not is_owner(ctx.author.id):
            return await ctx.send(embed=denied_embed())

        bot_member = ctx.guild.get_member(self.bot.user.id)
        if to_role >= bot_member.top_role or from_role >= bot_member.top_role:
            return await ctx.send("✦ Error: Bot role must be higher than both roles in Server Settings.")

        members_to_process = [m for m in ctx.guild.members if from_role in m.roles]
        if not members_to_process:
            try:
                async for m in ctx.guild.fetch_members(limit=None):
                    if from_role in m.roles:
                        members_to_process.append(m)
            except Exception:
                pass

        total = len(members_to_process)
        if total == 0:
            return await ctx.send(f"✦ No members found with role {from_role.mention}.")

        msg = await ctx.send(f"✦ Starting transfer for **{total}** members... 🌸")
        success_count = 0

        for i, member in enumerate(members_to_process, 1):
            try:
                if to_role not in member.roles:
                    await member.add_roles(to_role, reason=f"Mass transfer by {ctx.author}")
                if remove_old_role and from_role in member.roles:
                    await member.remove_roles(from_role, reason=f"Mass transfer by {ctx.author}")
                success_count += 1
                if i % 10 == 0 or i == total:
                    await msg.edit(content=f"✦ Transferring roles... `{i}/{total}` completed.")
                await asyncio.sleep(0.35)
            except Exception:
                pass

        embed = discord.Embed(
            title="✦ MASS ROLE TRANSFER COMPLETE ✦",
            description=(
                f"**From:** {from_role.mention}\n"
                f"**To:** {to_role.mention}\n"
                f"**Members Migrated:** `{success_count}/{total}`"
            ),
            color=COLOR_MINT
        )
        embed.set_footer(text="Destiny ✦ Role Operations")
        await msg.edit(content=None, embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(AutoRole(bot))
