import datetime
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from config import is_owner, denied_embed, make_kawaii_embed, COLOR_ERROR, COLOR_SUCCESS, COLOR_WARN, COLOR_MINT

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

    # --- Category & Channel Permission Synchronization ---
    @app_commands.command(
        name="sync-category",
        description="🌸 Copy and synchronize permissions from one category to another"
    )
    @app_commands.describe(
        from_category="Category to copy permissions from",
        to_category="Category to receive permissions",
        sync_channels="Whether to also synchronize all channels inside the target category (default: True)"
    )
    async def sync_category(
        self,
        interaction: discord.Interaction,
        from_category: discord.CategoryChannel,
        to_category: discord.CategoryChannel,
        sync_channels: bool = True
    ):
        if not is_owner(interaction.user.id):
            return await interaction.response.send_message(embed=denied_embed(), ephemeral=True)

        if not interaction.guild.me.guild_permissions.manage_channels or not interaction.guild.me.guild_permissions.manage_roles:
            embed = make_kawaii_embed(
                title="✦ Missing Permissions",
                description="Destiny requires **Manage Channels** and **Manage Roles** permissions to sync category permissions.",
                color=COLOR_ERROR
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        await interaction.response.defer(ephemeral=False)

        try:
            # 1. Copy overwrites from from_category to to_category
            source_overwrites = from_category.overwrites
            await to_category.edit(
                overwrites=source_overwrites,
                reason=f"Synced category permissions from {from_category.name} by Master {interaction.user}"
            )

            # 2. Optionally sync child channels inside to_category
            channels_synced = 0
            channels_failed = 0
            child_channels = to_category.channels

            if sync_channels and child_channels:
                for c in child_channels:
                    try:
                        await c.edit(
                            sync_permissions=True,
                            reason=f"Synced permissions with category {to_category.name} by Master {interaction.user}"
                        )
                        channels_synced += 1
                        await asyncio.sleep(0.25)
                    except Exception as e:
                        print(f"Error syncing channel {c.name}: {e}")
                        channels_failed += 1

            embed = discord.Embed(
                title="✦ CATEGORY PERMISSIONS SYNCHRONIZED ✦",
                description=(
                    f"**Source Category:** {from_category.name} (`{from_category.id}`)\n"
                    f"**Target Category:** {to_category.name} (`{to_category.id}`)\n"
                    f"**Overwrites Copied:** `{len(source_overwrites)}` role/member rules\n"
                    f"**Child Channels Synced:** `{channels_synced}/{len(child_channels)}`"
                    + (f"\n**Failed Channels:** `{channels_failed}`" if channels_failed > 0 else "")
                    + "\n\n🌸 *All permissions and overwrites have been replicated.*"
                ),
                color=COLOR_MINT
            )
            embed.set_footer(text="Destiny ✦ Channel & Category Operations")
            await interaction.followup.send(embed=embed)

        except Exception as e:
            err_embed = make_kawaii_embed(
                title="✦ Sync Failed",
                description=f"An error occurred while synchronizing category permissions:\n`{e}`",
                color=COLOR_ERROR
            )
            await interaction.followup.send(embed=err_embed)

    @app_commands.command(
        name="sync-category-channels",
        description="🌸 Force all channels in a category to sync permissions with that category"
    )
    @app_commands.describe(category="Category whose channels should be synchronized")
    async def sync_category_channels(
        self,
        interaction: discord.Interaction,
        category: discord.CategoryChannel
    ):
        if not is_owner(interaction.user.id):
            return await interaction.response.send_message(embed=denied_embed(), ephemeral=True)

        if not category.channels:
            return await interaction.response.send_message(
                f"✦ Category **{category.name}** has no channels inside it.",
                ephemeral=True
            )

        await interaction.response.defer(ephemeral=False)

        synced = 0
        failed = 0
        for c in category.channels:
            try:
                await c.edit(sync_permissions=True, reason=f"Forced sync with {category.name} by {interaction.user}")
                synced += 1
                await asyncio.sleep(0.25)
            except Exception as e:
                print(f"Error syncing channel {c.name}: {e}")
                failed += 1

        embed = discord.Embed(
            title="✦ CATEGORY CHANNELS SYNCHRONIZED ✦",
            description=(
                f"**Category:** {category.name} (`{category.id}`)\n"
                f"**Channels Synced:** `{synced}/{len(category.channels)}`\n"
                + (f"**Failed:** `{failed}`\n" if failed > 0 else "")
                + "\n🌸 *All child channels are now directly synced with category permissions.*"
            ),
            color=COLOR_MINT
        )
        embed.set_footer(text="Destiny ✦ Channel Operations")
        await interaction.followup.send(embed=embed)

    @app_commands.command(
        name="sync-channel",
        description="🌸 Copy permissions from one channel to another"
    )
    @app_commands.describe(
        from_channel="Channel to copy permissions from",
        to_channel="Channel to apply permissions to"
    )
    async def sync_channel(
        self,
        interaction: discord.Interaction,
        from_channel: discord.abc.GuildChannel,
        to_channel: discord.abc.GuildChannel
    ):
        if not is_owner(interaction.user.id):
            return await interaction.response.send_message(embed=denied_embed(), ephemeral=True)

        await interaction.response.defer(ephemeral=False)

        try:
            source_overwrites = from_channel.overwrites
            await to_channel.edit(
                overwrites=source_overwrites,
                reason=f"Synced permissions from {from_channel.name} by Master {interaction.user}"
            )
            embed = discord.Embed(
                title="✦ CHANNEL PERMISSIONS COPIED ✦",
                description=(
                    f"**From Channel:** {from_channel.name} (`{from_channel.id}`)\n"
                    f"**To Channel:** {to_channel.name} (`{to_channel.id}`)\n"
                    f"**Overwrites Copied:** `{len(source_overwrites)}` rules\n\n"
                    "🌸 *Target channel now matches source permissions exactly.*"
                ),
                color=COLOR_MINT
            )
            embed.set_footer(text="Destiny ✦ Channel Operations")
            await interaction.followup.send(embed=embed)
        except Exception as e:
            err = make_kawaii_embed(
                title="✦ Sync Failed",
                description=f"Failed to copy channel permissions: `{e}`",
                color=COLOR_ERROR
            )
            await interaction.followup.send(embed=err)

    # --- Prefix Commands for Category / Channel Permissions ---
    @commands.command(name="synccategory", aliases=["synccat", "syncpermscat"])
    async def prefix_sync_category(
        self,
        ctx: commands.Context,
        from_category: discord.CategoryChannel,
        to_category: discord.CategoryChannel,
        sync_channels: bool = True
    ):
        """Prefix command: !synccat <from_category> <to_category> [sync_channels=True]"""
        if not is_owner(ctx.author.id):
            return await ctx.send(embed=denied_embed())

        msg = await ctx.send(f"🌸 Copying permissions from **{from_category.name}** to **{to_category.name}**...")
        try:
            await to_category.edit(
                overwrites=from_category.overwrites,
                reason=f"Synced category permissions from {from_category.name} by {ctx.author}"
            )
            synced = 0
            if sync_channels and to_category.channels:
                for c in to_category.channels:
                    try:
                        await c.edit(sync_permissions=True, reason=f"Synced permissions with {to_category.name}")
                        synced += 1
                        await asyncio.sleep(0.2)
                    except Exception:
                        pass

            embed = discord.Embed(
                title="✦ CATEGORY PERMISSIONS SYNCHRONIZED ✦",
                description=(
                    f"**From:** {from_category.name}\n"
                    f"**To:** {to_category.name}\n"
                    f"**Rules Copied:** `{len(from_category.overwrites)}`\n"
                    f"**Channels Synced:** `{synced}/{len(to_category.channels)}`"
                ),
                color=COLOR_MINT
            )
            embed.set_footer(text="Destiny ✦ Category Operations")
            await msg.edit(content=None, embed=embed)
        except Exception as e:
            await msg.edit(content=f"✦ Error syncing category: `{e}`")

    @commands.command(name="syncchannels", aliases=["syncchans"])
    async def prefix_sync_channels(self, ctx: commands.Context, category: discord.CategoryChannel):
        """Prefix command: !syncchannels <category>"""
        if not is_owner(ctx.author.id):
            return await ctx.send(embed=denied_embed())

        msg = await ctx.send(f"🌸 Syncing all channels in **{category.name}** with category permissions...")
        synced = 0
        for c in category.channels:
            try:
                await c.edit(sync_permissions=True, reason=f"Synced permissions by {ctx.author}")
                synced += 1
                await asyncio.sleep(0.2)
            except Exception:
                pass

        await msg.edit(content=f"🌸 Successfully synced `{synced}/{len(category.channels)}` channels in **{category.name}**! ✨")

async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
