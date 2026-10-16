import re
import time
import random
import discord
from discord import app_commands
from discord.ext import commands, tasks
import database
from config import is_owner, denied_embed, make_kawaii_embed, COLOR_PINK, COLOR_ROSE, COLOR_SUCCESS, COLOR_WARN, random_happy

def parse_duration(duration_str: str) -> float | None:
    """Parses strings like 30s, 10m, 2h, 1d into seconds."""
    match = re.match(r"^(\d+)([smhd])$", duration_str.strip().lower())
    if not match:
        return None
    val, unit = match.groups()
    val = int(val)
    multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    return float(val * multipliers[unit])

class GiveawayButton(discord.ui.Button):
    def __init__(self, message_id: int, entries: int = 0):
        super().__init__(
            style=discord.ButtonStyle.primary,
            label=f"🎉 Enter Giveaway ({entries})",
            custom_id=f"destiny_gw_{message_id}",
            emoji="✨"
        )

class Giveaways(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.giveaway_checker.start()

    def cog_unload(self):
        self.giveaway_checker.cancel()

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """Handles persistent join button clicks on giveaways."""
        if interaction.type != discord.InteractionType.component:
            return
        custom_id = interaction.data.get("custom_id", "")
        if custom_id.startswith("destiny_gw_"):
            try:
                message_id = int(custom_id.replace("destiny_gw_", ""))
                entered, count = await database.toggle_giveaway_participant(message_id, interaction.user.id)
                
                # Update button count on the original message
                try:
                    view = discord.ui.View(timeout=None)
                    view.add_item(discord.ui.Button(
                        style=discord.ButtonStyle.primary,
                        label=f"🎉 Enter Giveaway ({count})",
                        custom_id=f"destiny_gw_{message_id}",
                        emoji="✨"
                    ))
                    await interaction.message.edit(view=view)
                except Exception:
                    pass

                if entered:
                    await interaction.response.send_message(
                        f"✨ Yay! You are now entered into the giveaway! Good luck, cutie! (੭ˊᵕˋ)੭ 🌸",
                        ephemeral=True
                    )
                else:
                    await interaction.response.send_message(
                        f"🎀 You have withdrawn your entry from the giveaway. (｡•́︿•̀｡)",
                        ephemeral=True
                    )
            except Exception as e:
                print(f"Error handling giveaway button: {e}")

    @tasks.loop(seconds=10)
    async def giveaway_checker(self):
        """Background worker that continuously tracks giveaway end times."""
        try:
            active_gws = await database.get_active_giveaways()
            now = time.time()
            for gw in active_gws:
                if gw["end_time"] <= now:
                    await self.finish_giveaway(gw)
        except Exception as e:
            print(f"Error in giveaway checker loop: {e}")

    @giveaway_checker.before_loop
    async def before_checker(self):
        await self.bot.wait_until_ready()

    async def finish_giveaway(self, gw: dict):
        """Ends a giveaway, picks winners, and updates the embed."""
        message_id = gw["message_id"]
        channel_id = gw["channel_id"]
        prize = gw["prize"]
        winners_count = gw["winners_count"]
        participants = gw["participants"]

        await database.end_giveaway(message_id)

        channel = self.bot.get_channel(channel_id)
        if not channel:
            return

        try:
            msg = await channel.fetch_message(message_id)
        except Exception:
            return

        if not participants:
            embed = make_kawaii_embed(
                title=f"🌸 Giveaway Ended: {prize} (｡•́︿•̀｡)",
                description="Unfortunately, no one entered this giveaway! Better luck next time! 🎀",
                color=COLOR_WARN
            )
            disabled_view = discord.ui.View(timeout=None)
            disabled_view.add_item(discord.ui.Button(
                style=discord.ButtonStyle.secondary,
                label="Giveaway Ended",
                disabled=True
            ))
            await msg.edit(embed=embed, view=disabled_view)
            return

        # Pick random winners
        num_winners = min(len(participants), winners_count)
        winners = random.sample(participants, num_winners)
        mentions = " ".join([f"<@{w}>" for w in winners])

        embed = make_kawaii_embed(
            title=f"🌸✨ Giveaway Ended: {prize} ✨🌸",
            description=(
                f"**Winner(s):** {mentions}\n"
                f"**Hosted by:** Master Destiny 🌸\n"
                f"**Total Entries:** {len(participants)} cuties 💕"
            ),
            color=COLOR_SUCCESS
        )
        disabled_view = discord.ui.View(timeout=None)
        disabled_view.add_item(discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label=f"Ended ({len(participants)} Entries)",
            disabled=True,
            emoji="🎁"
        ))
        await msg.edit(embed=embed, view=disabled_view)

        # Celebratory win message
        await channel.send(
            f"🎉 (ﾉ◕ヮ◕)ﾉ*:･ﾟ✧ Congratulations {mentions}! You won **{prize}**! 🍰✨"
        )

    gw_group = app_commands.Group(
        name="giveaway",
        description="🌸 Manage cute giveaways and roll prizes"
    )

    @gw_group.command(name="start", description="🌸 Start a kawaii giveaway with interactive buttons")
    @app_commands.describe(
        duration="Duration (e.g. 30s, 10m, 2h, 1d)",
        prize="What lucky cuties can win",
        winners="Number of winners (default: 1)",
        channel="Channel to post giveaway in (defaults to current)"
    )
    async def start_giveaway(
        self,
        interaction: discord.Interaction,
        duration: str,
        prize: str,
        winners: int = 1,
        channel: discord.TextChannel = None
    ):
        if not is_owner(interaction.user.id):
            return await interaction.response.send_message(embed=denied_embed(), ephemeral=True)

        target_channel = channel or interaction.channel
        seconds = parse_duration(duration)
        if not seconds:
            return await interaction.response.send_message(
                "🌸 Invalid duration! Use formats like `30s`, `10m`, `2h`, or `1d`! (｡•́︿•̀｡)",
                ephemeral=True
            )

        if winners < 1:
            return await interaction.response.send_message(
                "🌸 Winners must be at least 1! (,,>﹏<,,)",
                ephemeral=True
            )

        end_timestamp = time.time() + seconds
        discord_time = int(end_timestamp)

        embed = make_kawaii_embed(
            title=f"🌸 GIVEAWAY: {prize} 🎁✨",
            description=(
                f"Click the button below to enter!\n\n"
                f"🎁 **Prize:** `{prize}`\n"
                f"🏆 **Winners:** `{winners}`\n"
                f"⏰ **Ends:** <t:{discord_time}:R> (<t:{discord_time}:f>)\n"
                f"🌸 **Hosted by:** {interaction.user.mention}"
            ),
            color=COLOR_ROSE
        )

        # Send initial message with empty view
        view = discord.ui.View(timeout=None)
        # Use dummy button first, we update with message id right after
        view.add_item(discord.ui.Button(style=discord.ButtonStyle.primary, label="Entering...", emoji="✨"))
        msg = await target_channel.send(embed=embed, view=view)

        # Update with real custom_id
        real_view = discord.ui.View(timeout=None)
        real_view.add_item(GiveawayButton(message_id=msg.id, entries=0))
        await msg.edit(view=real_view)

        await database.create_giveaway(
            message_id=msg.id,
            channel_id=target_channel.id,
            guild_id=interaction.guild_id,
            prize=prize,
            end_time=end_timestamp,
            winners_count=winners
        )

        reply = make_kawaii_embed(
            title=f"🌸 Giveaway Launched! {random_happy()}",
            description=f"Your giveaway for **{prize}** is now live in {target_channel.mention}! ✨",
            color=COLOR_PINK
        )
        await interaction.response.send_message(embed=reply, ephemeral=True)

    @gw_group.command(name="reroll", description="🌸 Reroll a winner for an ended giveaway")
    @app_commands.describe(message_id="The message ID of the giveaway")
    async def reroll(self, interaction: discord.Interaction, message_id: str):
        if not is_owner(interaction.user.id):
            return await interaction.response.send_message(embed=denied_embed(), ephemeral=True)

        try:
            msg_id_int = int(message_id)
            gw = await database.get_giveaway(msg_id_int)
        except Exception:
            gw = None

        if not gw:
            return await interaction.response.send_message(
                "🌸 Could not find a giveaway with that message ID! (｡•́︿•̀｡)",
                ephemeral=True
            )

        participants = gw.get("participants", [])
        if not participants:
            return await interaction.response.send_message(
                "🌸 No cuties entered this giveaway to reroll from! (◞‸◟；)",
                ephemeral=True
            )

        new_winner_id = random.choice(participants)
        channel = self.bot.get_channel(gw["channel_id"])
        if channel:
            await channel.send(
                f"🎉 (ﾉ◕ヮ◕)ﾉ*:･ﾟ✧ **REROLL!** The new winner for **{gw['prize']}** is <@{new_winner_id}>! Congratulations! 🍰✨"
            )

        reply = make_kawaii_embed(
            title=f"🌸 Reroll Complete! {random_happy()}",
            description=f"Selected new winner <@{new_winner_id}> for **{gw['prize']}**! 🎀",
            color=COLOR_SUCCESS
        )
        await interaction.response.send_message(embed=reply, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Giveaways(bot))
