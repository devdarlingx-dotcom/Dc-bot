import unicodedata
import discord
from discord import app_commands
from discord.ext import commands
import database
from config import is_owner, denied_embed, make_kawaii_embed, COLOR_PINK, COLOR_ROSE, COLOR_MINT, COLOR_WARN

def normalize_channel_name(name: str) -> str:
    """Normalizes Unicode aesthetic/mathematical script fonts to standard ASCII."""
    return unicodedata.normalize("NFKD", name).lower()

class Welcome(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def resolve_welcome_channel(self, guild: discord.Guild) -> discord.TextChannel | None:
        """Finds the configured or auto-detected welcome channel."""
        try:
            settings = await database.get_guild_settings(guild.id)
            channel_id = settings.get("welcome_channel_id")
            
            # 1. Try saved channel ID
            if channel_id:
                channel = guild.get_channel(channel_id)
                if not channel:
                    try:
                        channel = await self.bot.fetch_channel(channel_id)
                    except Exception:
                        channel = None
                if isinstance(channel, discord.TextChannel):
                    return channel

            # 2. Auto-detect by searching normalized channel names
            for c in guild.text_channels:
                norm = normalize_channel_name(c.name)
                if "welcome" in norm or "bienvenid" in norm or "llegada" in norm:
                    await database.set_welcome_channel(guild.id, c.id)
                    return c

            # 3. Known fallback for user's specific server
            fallback_channel = guild.get_channel(1560482248598355968)
            if fallback_channel:
                await database.set_welcome_channel(guild.id, fallback_channel.id)
                return fallback_channel

        except Exception as e:
            print(f"❌ Error resolving welcome channel: {e}")

        return None

    async def send_welcome_embed(self, member: discord.Member, channel: discord.TextChannel):
        """Constructs and sends a clean, aesthetic kawaii welcome card."""
        try:
            avatar_url = member.display_avatar.url if member.display_avatar else None
            embed = discord.Embed(
                title=f"✦ WELCOME TO {member.guild.name.upper()} ✦",
                description=(
                    f"Welcome {member.mention} to our community. 🌸\n\n"
                    f"**Member:** `#{member.guild.member_count}`\n"
                    f"**Account Created:** <t:{int(member.created_at.timestamp())}:R>\n\n"
                    f"> Please check out our guidelines and enjoy your stay."
                ),
                color=COLOR_ROSE
            )
            if avatar_url:
                embed.set_thumbnail(url=avatar_url)
            embed.set_footer(text=f"Destiny ✦ Member #{member.guild.member_count}")
            
            await channel.send(content=f"🌸 Welcome {member.mention}", embed=embed)
        except Exception as e:
            print(f"❌ [WELCOME] Failed to send welcome card: {e}")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Dispatches welcome card when someone joins."""
        channel = await self.resolve_welcome_channel(member.guild)
        if channel:
            await self.send_welcome_embed(member, channel)

    welcome_group = app_commands.Group(
        name="welcome",
        description="🌸 Manage server welcome messages"
    )

    @welcome_group.command(name="set-channel", description="🌸 Set the channel where welcome cards are delivered")
    @app_commands.describe(channel="Channel for welcome cards")
    async def set_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not is_owner(interaction.user.id):
            return await interaction.response.send_message(embed=denied_embed(), ephemeral=True)

        await database.set_welcome_channel(interaction.guild_id, channel.id)
        embed = make_kawaii_embed(
            title="✦ Welcome Channel Configured",
            description=f"Welcome cards will now be sent to {channel.mention}. 🌸",
            color=COLOR_MINT
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @welcome_group.command(name="test", description="🌸 Test welcome card (sends preview to welcome channel)")
    @app_commands.describe(send_to_channel="If true, posts directly into the welcome channel")
    async def test_welcome(self, interaction: discord.Interaction, send_to_channel: bool = True):
        if not is_owner(interaction.user.id):
            return await interaction.response.send_message(embed=denied_embed(), ephemeral=True)

        channel = await self.resolve_welcome_channel(interaction.guild)
        if not channel:
            channel = interaction.channel

        if send_to_channel and channel:
            await self.send_welcome_embed(interaction.user, channel)
            reply = make_kawaii_embed(
                title="✦ Welcome Card Preview Sent",
                description=f"Sent a test card to {channel.mention}. 🌸",
                color=COLOR_MINT
            )
            await interaction.response.send_message(embed=reply, ephemeral=True)
        else:
            avatar_url = interaction.user.display_avatar.url if interaction.user.display_avatar else None
            embed = discord.Embed(
                title=f"✦ WELCOME TO {interaction.guild.name.upper()} ✦",
                description=(
                    f"Welcome {interaction.user.mention} to our community. 🌸\n\n"
                    f"**Member:** `#{interaction.guild.member_count}`\n"
                    f"**Account Created:** <t:{int(interaction.user.created_at.timestamp())}:R>\n\n"
                    f"> Please check out our guidelines and enjoy your stay."
                ),
                color=COLOR_ROSE
            )
            if avatar_url:
                embed.set_thumbnail(url=avatar_url)
            embed.set_footer(text=f"Destiny ✦ Preview")
            await interaction.response.send_message(content=f"🌸 Welcome {interaction.user.mention}", embed=embed, ephemeral=True)

    @welcome_group.command(name="status", description="🌸 View current welcome channel setup")
    async def status_welcome(self, interaction: discord.Interaction):
        if not is_owner(interaction.user.id):
            return await interaction.response.send_message(embed=denied_embed(), ephemeral=True)

        channel = await self.resolve_welcome_channel(interaction.guild)
        if channel:
            desc = f"✦ Active welcome channel: {channel.mention} (`{channel.id}`)"
            color = COLOR_MINT
        else:
            desc = "✦ No welcome channel configured. Use `/welcome set-channel` to bind one."
            color = COLOR_WARN

        embed = make_kawaii_embed(
            title="✦ Welcome Status",
            description=desc,
            color=color
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @welcome_group.command(name="disable", description="🌸 Disable automatic welcome messages")
    async def disable_welcome(self, interaction: discord.Interaction):
        if not is_owner(interaction.user.id):
            return await interaction.response.send_message(embed=denied_embed(), ephemeral=True)

        await database.set_welcome_channel(interaction.guild_id, None)
        embed = make_kawaii_embed(
            title="✦ Welcome Disabled",
            description="Automatic welcome cards have been disabled. 🌸",
            color=COLOR_PINK
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Welcome(bot))
