import time
import discord
from discord import app_commands
from discord.ext import commands
import database
from config import is_owner, denied_embed, make_kawaii_embed, COLOR_PINK, COLOR_MINT, COLOR_ROSE, COLOR_PURPLE

# --- Modals ---
class BroadcastModal(discord.ui.Modal, title="✦ Broadcast Announcement ✦"):
    channel_id = discord.ui.TextInput(
        label="Channel ID or Mention",
        placeholder="e.g. 1560475069824634880 or #announcements",
        required=True
    )
    title_input = discord.ui.TextInput(
        label="Announcement Title",
        placeholder="Important Update",
        required=True
    )
    content_input = discord.ui.TextInput(
        label="Announcement Message",
        style=discord.TextStyle.paragraph,
        placeholder="Type your announcement content here...",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        clean_id = self.channel_id.value.replace("<#", "").replace(">", "").strip()
        channel = guild.get_channel(int(clean_id)) if clean_id.isdigit() else None
        if not channel:
            return await interaction.response.send_message("✦ Channel not found. Verify the ID.", ephemeral=True)

        embed = discord.Embed(
            title=f"✦ {self.title_input.value.upper()} ✦",
            description=self.content_input.value,
            color=COLOR_PINK
        )
        if guild.icon:
            embed.set_author(name=guild.name, icon_url=guild.icon.url)
        embed.set_footer(text="Destiny ✦ Server Announcement")

        await channel.send(embed=embed)
        await interaction.response.send_message(
            f"✦ Announcement published to {channel.mention}. 🌸",
            ephemeral=True
        )

class ScriptUpdateModal(discord.ui.Modal, title="✦ Announce Script Update ✦"):
    channel_id = discord.ui.TextInput(
        label="Target Channel ID (Optional)",
        placeholder="Leave empty for updates channel or paste ID",
        required=False
    )
    script_name = discord.ui.TextInput(
        label="Script Name",
        placeholder="e.g. Destiny Hub",
        required=True
    )
    version = discord.ui.TextInput(
        label="Version",
        placeholder="e.g. 2.1.0",
        required=True
    )
    changelog = discord.ui.TextInput(
        label="Changelog / What's New",
        style=discord.TextStyle.paragraph,
        placeholder="- Added new features\n- Fixed bugs\n- Performance improvements",
        required=True
    )
    download_url = discord.ui.TextInput(
        label="Download / Script URL",
        placeholder="https://example.com/script.lua",
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        target_channel = None
        if self.channel_id.value.strip():
            clean_id = self.channel_id.value.replace("<#", "").replace(">", "").strip()
            if clean_id.isdigit():
                target_channel = guild.get_channel(int(clean_id))

        if not target_channel:
            settings = await database.get_guild_settings(guild.id)
            if settings.get("updates_channel_id"):
                target_channel = guild.get_channel(settings["updates_channel_id"])
            if not target_channel:
                import unicodedata
                for c in guild.text_channels:
                    norm = unicodedata.normalize("NFKD", c.name).lower()
                    if "update" in norm:
                        target_channel = c
                        break

        if not target_channel:
            target_channel = interaction.channel

        cog = interaction.client.get_cog("ScriptUpdates")
        if cog:
            await cog.broadcast_update(
                script_name=self.script_name.value,
                version=self.version.value,
                changelog=self.changelog.value,
                download_url=self.download_url.value or None,
                channel=target_channel,
                author=interaction.user.mention
            )
            await interaction.response.send_message(
                f"✦ Script update published to {target_channel.mention}. 🌸",
                ephemeral=True
            )
        else:
            await interaction.response.send_message("✦ ScriptUpdates module is not loaded.", ephemeral=True)

class QuickGiveawayModal(discord.ui.Modal, title="✦ Quick Giveaway Creator ✦"):
    channel_id = discord.ui.TextInput(
        label="Channel ID (Optional)",
        placeholder="Leave empty for current channel",
        required=False
    )
    prize = discord.ui.TextInput(
        label="Prize Name",
        placeholder="e.g. Discord Nitro / VIP Access",
        required=True
    )
    duration = discord.ui.TextInput(
        label="Duration (e.g. 10m, 1h, 1d)",
        placeholder="10m",
        required=True
    )
    winners = discord.ui.TextInput(
        label="Number of Winners",
        placeholder="1",
        default="1",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        from cogs.giveaways import parse_duration, GiveawayButton
        guild = interaction.guild
        target_channel = interaction.channel
        if self.channel_id.value.strip():
            clean_id = self.channel_id.value.replace("<#", "").replace(">", "").strip()
            if clean_id.isdigit():
                c = guild.get_channel(int(clean_id))
                if c:
                    target_channel = c

        seconds = parse_duration(self.duration.value)
        if not seconds:
            return await interaction.response.send_message("✦ Invalid duration format. Use 10m, 1h, etc.", ephemeral=True)

        try:
            winners_int = int(self.winners.value)
        except ValueError:
            winners_int = 1

        end_timestamp = time.time() + seconds
        embed = discord.Embed(
            title="✦ GIVEAWAY ✦",
            description=(
                f"### 🎁 {self.prize.value}\n\n"
                f"**Winners:** `{winners_int}`\n"
                f"**Hosted by:** {interaction.user.mention}\n"
                f"**Ends:** <t:{int(end_timestamp)}:R> (<t:{int(end_timestamp)}:f>)\n\n"
                f"> Click the button below to participate."
            ),
            color=COLOR_ROSE
        )
        embed.set_footer(text="Destiny ✦ Active Giveaway")

        view = discord.ui.View(timeout=None)
        view.add_item(discord.ui.Button(style=discord.ButtonStyle.primary, label="Entering...", emoji="✦"))
        msg = await target_channel.send(embed=embed, view=view)

        real_view = discord.ui.View(timeout=None)
        real_view.add_item(GiveawayButton(message_id=msg.id, entries=0))
        await msg.edit(view=real_view)

        await database.create_giveaway(
            message_id=msg.id,
            channel_id=target_channel.id,
            guild_id=guild.id,
            prize=self.prize.value,
            end_time=end_timestamp,
            winners_count=winners_int
        )

        await interaction.response.send_message(
            f"✦ Giveaway live in {target_channel.mention}. 🌸",
            ephemeral=True
        )

# --- Role & Channel Select Views ---
class AutoRoleSelect(discord.ui.RoleSelect):
    def __init__(self):
        super().__init__(placeholder="Select the default auto-role for new members 🌸", min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        role = self.values[0]
        await database.set_autorole(interaction.guild_id, role.id)
        await interaction.response.send_message(
            f"✦ Default auto-role set to **{role.name}**. 🌸",
            ephemeral=True
        )

class WelcomeChannelSelect(discord.ui.ChannelSelect):
    def __init__(self):
        super().__init__(
            placeholder="Select the channel for welcome cards 🎀",
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=1
        )

    async def callback(self, interaction: discord.Interaction):
        channel = self.values[0]
        await database.set_welcome_channel(interaction.guild_id, channel.id)
        await interaction.response.send_message(
            f"✦ Welcome cards will be sent to {channel.mention}. 🌸",
            ephemeral=True
        )

# --- Main Master Panel View ---
class MasterPanelView(discord.ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Auto-Role", style=discord.ButtonStyle.primary, emoji="🌸", row=0)
    async def btn_autorole(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = discord.ui.View(timeout=60)
        view.add_item(AutoRoleSelect())
        await interaction.response.send_message("🌸 Select the new member auto-role:", view=view, ephemeral=True)

    @discord.ui.button(label="Welcome Channel", style=discord.ButtonStyle.primary, emoji="🎀", row=0)
    async def btn_welcome(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = discord.ui.View(timeout=60)
        view.add_item(WelcomeChannelSelect())
        await interaction.response.send_message("🎀 Select the welcome card destination:", view=view, ephemeral=True)

    @discord.ui.button(label="Broadcast", style=discord.ButtonStyle.success, emoji="📢", row=0)
    async def btn_broadcast(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(BroadcastModal())

    @discord.ui.button(label="Script Update", style=discord.ButtonStyle.success, emoji="🚀", row=1)
    async def btn_script_update(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ScriptUpdateModal())

    @discord.ui.button(label="Giveaway", style=discord.ButtonStyle.secondary, emoji="🎁", row=1)
    async def btn_giveaway(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(QuickGiveawayModal())

    @discord.ui.button(label="Refresh Panel", style=discord.ButtonStyle.secondary, emoji="🔄", row=1)
    async def btn_refresh(self, interaction: discord.Interaction, button: discord.ui.Button):
        panel_cog = self.bot.get_cog("ControlPanel")
        if panel_cog:
            embed = await panel_cog.generate_panel_embed(interaction.guild)
            await interaction.response.edit_message(embed=embed, view=self)

class ControlPanel(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def generate_panel_embed(self, guild: discord.Guild) -> discord.Embed:
        settings = await database.get_guild_settings(guild.id)
        autorole = guild.get_role(settings["autorole_id"]) if settings.get("autorole_id") else None
        welcome_ch = guild.get_channel(settings["welcome_channel_id"]) if settings.get("welcome_channel_id") else None

        embed = discord.Embed(
            title="✦ DESTINY MASTER CONTROL ✦",
            description=(
                f"Welcome back, Master <@{guild.owner_id}>. 🌸\n"
                "Select any module below to manage server operations.\n\n"
                f"**Server:** `{guild.name}` (`{guild.id}`)\n"
                f"**Members:** `{guild.member_count}`\n"
                f"**Bot Latency:** `{round(self.bot.latency * 1000)}ms`\n\n"
                f"**Auto-Role:** {autorole.mention if autorole else '`Disabled`'}\n"
                f"**Welcome Channel:** {welcome_ch.mention if welcome_ch else '`Auto / None`'}\n"
                f"**System Status:** `Online & Operational` ✦"
            ),
            color=COLOR_PURPLE
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text="Destiny ✦ Master System")
        return embed

    @app_commands.command(name="panel", description="🌸 Open the master interactive Destiny control center")
    async def open_panel(self, interaction: discord.Interaction):
        if not is_owner(interaction.user.id):
            return await interaction.response.send_message(embed=denied_embed(), ephemeral=True)

        embed = await self.generate_panel_embed(interaction.guild)
        view = MasterPanelView(self.bot)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @commands.command(name="panel")
    async def prefix_panel(self, ctx: commands.Context):
        """Prefix fallback: !panel"""
        if not is_owner(ctx.author.id):
            return await ctx.send(embed=denied_embed())

        embed = await self.generate_panel_embed(ctx.guild)
        view = MasterPanelView(self.bot)
        await ctx.send(embed=embed, view=view)

    @commands.command(name="ping")
    async def prefix_ping(self, ctx: commands.Context):
        """Prefix fallback: !ping"""
        latency = round(self.bot.latency * 1000)
        await ctx.send(f"✦ Pong! Latency: `{latency}ms` 🌸")

async def setup(bot: commands.Bot):
    await bot.add_cog(ControlPanel(bot))
