import discord
from discord import app_commands
from discord.ext import commands
import database
from config import is_owner, denied_embed, make_kawaii_embed, COLOR_PINK, COLOR_ROSE, COLOR_MINT, random_happy

class Welcome(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def send_welcome_embed(self, member: discord.Member, channel: discord.TextChannel):
        """Constructs and sends the kawaii welcome card."""
        embed = discord.Embed(
            title=f"🌸 Welcome to {member.guild.name}! 🌸",
            description=(
                f"(੭ˊᵕˋ)੭ Yay! A sweet new cutie has arrived!\n"
                f"Welcome {member.mention} to our cozy haven! 💕\n\n"
                f"✨ **You are Cutie #:** `{member.guild.member_count}`\n"
                f"🎀 **Account Born:** <t:{int(member.created_at.timestamp())}:R>\n\n"
                f"*Please make yourself at home, grab some tea, and have fun!* 🍰"
            ),
            color=COLOR_ROSE
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Destiny Welcomer • {random_happy()} ✨")
        await channel.send(content=f"🌸 Welcome {member.mention}! ✨", embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Dispatches welcome card when someone joins."""
        try:
            settings = await database.get_guild_settings(member.guild.id)
            channel_id = settings.get("welcome_channel_id")
            channel = None

            if channel_id:
                channel = member.guild.get_channel(channel_id)
            else:
                # Auto-detect channel named welcome if not explicitly configured
                for c in member.guild.text_channels:
                    if "welcome" in c.name.lower():
                        channel = c
                        break

            if channel:
                await self.send_welcome_embed(member, channel)
        except Exception as e:
            print(f"Error in on_member_join welcome: {e}")

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
            title=f"🌸 Welcome Channel Configured! {random_happy()}",
            description=f"Welcome messages will now be posted in {channel.mention}! ✨",
            color=COLOR_MINT
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @welcome_group.command(name="test", description="🌸 Test how the welcome card looks right now")
    async def test_welcome(self, interaction: discord.Interaction):
        if not is_owner(interaction.user.id):
            return await interaction.response.send_message(embed=denied_embed(), ephemeral=True)

        embed = discord.Embed(
            title=f"🌸 [TEST] Welcome to {interaction.guild.name}! 🌸",
            description=(
                f"(੭ˊᵕˋ)੭ Yay! A sweet new cutie has arrived!\n"
                f"Welcome {interaction.user.mention} to our cozy haven! 💕\n\n"
                f"✨ **You are Cutie #:** `{interaction.guild.member_count}`\n"
                f"🎀 **Account Born:** <t:{int(interaction.user.created_at.timestamp())}:R>\n\n"
                f"*Please make yourself at home, grab some tea, and have fun!* 🍰"
            ),
            color=COLOR_ROSE
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text=f"Destiny Welcomer (Preview) • {random_happy()} ✨")
        await interaction.response.send_message(content=f"🌸 Welcome {interaction.user.mention}! ✨", embed=embed, ephemeral=True)

    @welcome_group.command(name="disable", description="🌸 Disable automatic welcome messages")
    async def disable_welcome(self, interaction: discord.Interaction):
        if not is_owner(interaction.user.id):
            return await interaction.response.send_message(embed=denied_embed(), ephemeral=True)

        await database.set_welcome_channel(interaction.guild_id, None)
        embed = make_kawaii_embed(
            title="🌸 Welcome Messages Disabled",
            description="Welcome messages have been disabled! 🎀",
            color=COLOR_PINK
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Welcome(bot))
