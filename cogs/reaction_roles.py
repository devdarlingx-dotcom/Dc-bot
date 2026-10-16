import discord
from discord import app_commands
from discord.ext import commands
import database
from config import is_owner, denied_embed, make_kawaii_embed, COLOR_MINT, COLOR_ROSE

class RoleButton(discord.ui.Button):
    def __init__(self, role_id: int, label: str, emoji: str = "✦"):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label=label,
            emoji=emoji,
            custom_id=f"destiny_rr_{role_id}"
        )
        self.role_id = role_id

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        role = guild.get_role(self.role_id)
        if not role:
            return await interaction.response.send_message(
                "✦ This role no longer exists in the server.",
                ephemeral=True
            )

        member = interaction.user
        if role in member.roles:
            await member.remove_roles(role, reason="Destiny Button Role Removal")
            await interaction.response.send_message(
                f"✦ Removed **{role.name}** from your roles.",
                ephemeral=True
            )
        else:
            await member.add_roles(role, reason="Destiny Button Role Claim")
            await interaction.response.send_message(
                f"✦ Added **{role.name}** to your roles.",
                ephemeral=True
            )

class ReactionRoles(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """Global handler for persistent reaction role buttons."""
        if interaction.type != discord.InteractionType.component:
            return
        custom_id = interaction.data.get("custom_id", "")
        if custom_id.startswith("destiny_rr_"):
            try:
                role_id = int(custom_id.replace("destiny_rr_", ""))
                guild = interaction.guild
                if not guild:
                    return
                role = guild.get_role(role_id)
                if not role:
                    return await interaction.response.send_message(
                        "✦ This role no longer exists in the server.",
                        ephemeral=True
                    )
                member = interaction.user
                if role in member.roles:
                    await member.remove_roles(role, reason="Destiny Role Button Removed")
                    await interaction.response.send_message(
                        f"✦ Removed **{role.name}** from your roles.",
                        ephemeral=True
                    )
                else:
                    await member.add_roles(role, reason="Destiny Role Button Claimed")
                    await interaction.response.send_message(
                        f"✦ Added **{role.name}** to your roles.",
                        ephemeral=True
                    )
            except Exception as e:
                print(f"Error handling button role: {e}")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Traditional Emoji Reaction: assigns role when emoji is clicked."""
        if payload.user_id == self.bot.user.id:
            return
        emoji_str = str(payload.emoji)
        rr = await database.get_reaction_role(payload.message_id, emoji_str)
        if not rr:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        role = guild.get_role(rr["role_id"])
        member = payload.member or guild.get_member(payload.user_id)
        if role and member:
            try:
                await member.add_roles(role, reason="Destiny Emoji Reaction Role")
            except Exception as e:
                print(f"Error adding emoji reaction role: {e}")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        """Traditional Emoji Reaction: removes role when emoji is unclicked."""
        if payload.user_id == self.bot.user.id:
            return
        emoji_str = str(payload.emoji)
        rr = await database.get_reaction_role(payload.message_id, emoji_str)
        if not rr:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        role = guild.get_role(rr["role_id"])
        member = guild.get_member(payload.user_id)
        if role and member:
            try:
                await member.remove_roles(role, reason="Destiny Emoji Reaction Role Removal")
            except Exception as e:
                print(f"Error removing emoji reaction role: {e}")

    rr_group = app_commands.Group(
        name="reactionrole",
        description="🌸 Configure role buttons and emoji bindings"
    )

    @rr_group.command(name="button", description="🌸 Post an aesthetic role button panel in a channel")
    @app_commands.describe(
        channel="Channel to post the role button in",
        role="The role to toggle on click",
        title="Title of the role card",
        description="Description explaining the role",
        button_label="Text on the button",
        button_emoji="Emoji or symbol on the button"
    )
    async def spawn_button(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        role: discord.Role,
        title: str = "✦ Self-Assignable Role",
        description: str = "Click the button below to claim or remove this role.",
        button_label: str = "Toggle Role",
        button_emoji: str = "✦"
    ):
        if not is_owner(interaction.user.id):
            return await interaction.response.send_message(embed=denied_embed(), ephemeral=True)

        embed = discord.Embed(
            title=f"✦ {title.upper()} ✦",
            description=f"{description}\n\n**Role:** {role.mention}",
            color=COLOR_ROSE
        )
        embed.set_footer(text="Destiny ✦ Role Assignment")
        view = discord.ui.View(timeout=None)
        view.add_item(RoleButton(role_id=role.id, label=button_label, emoji=button_emoji))

        msg = await channel.send(embed=embed, view=view)
        await database.add_reaction_role(
            message_id=msg.id,
            channel_id=channel.id,
            role_id=role.id,
            emoji_or_custom_id=f"destiny_rr_{role.id}",
            mode="button",
            title=title
        )

        reply = make_kawaii_embed(
            title="✦ Role Button Created",
            description=f"Created role panel in {channel.mention} for **{role.name}**. 🌸",
            color=COLOR_MINT
        )
        await interaction.response.send_message(embed=reply, ephemeral=True)

    @rr_group.command(name="emoji", description="🌸 Bind an emoji reaction to a role on an existing message")
    @app_commands.describe(
        channel="Channel where the message is",
        message_id="The ID of the message",
        emoji="The emoji cuties will click",
        role="The role to award"
    )
    async def bind_emoji(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        message_id: str,
        emoji: str,
        role: discord.Role
    ):
        if not is_owner(interaction.user.id):
            return await interaction.response.send_message(embed=denied_embed(), ephemeral=True)

        try:
            msg_id_int = int(message_id)
            target_msg = await channel.fetch_message(msg_id_int)
        except Exception:
            return await interaction.response.send_message(
                "✦ Message not found. Verify the ID and channel.",
                ephemeral=True
            )

        try:
            await target_msg.add_reaction(emoji)
        except Exception as e:
            return await interaction.response.send_message(
                f"✦ Could not add reaction '{emoji}'. Verify the emoji is valid: {e}",
                ephemeral=True
            )

        await database.add_reaction_role(
            message_id=msg_id_int,
            channel_id=channel.id,
            role_id=role.id,
            emoji_or_custom_id=emoji,
            mode="emoji",
            title=role.name
        )

        reply = make_kawaii_embed(
            title="✦ Emoji Role Bound",
            description=f"Reacting with {emoji} on [this message]({target_msg.jump_url}) will grant **{role.mention}**. 🌸",
            color=COLOR_MINT
        )
        await interaction.response.send_message(embed=reply, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(ReactionRoles(bot))
