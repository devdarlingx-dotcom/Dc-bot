import time
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
import database
from config import is_owner, denied_embed, make_kawaii_embed, COLOR_MINT, COLOR_PINK, COLOR_ROSE, COLOR_WARN

def make_progress_bar(current: int, total: int, length: int = 12) -> str:
    """Renders a clean aesthetic unicode progress bar."""
    if total <= 0:
        return f"[{'▱' * length}] 0%"
    pct = min(1.0, max(0.0, current / total))
    filled = int(round(pct * length))
    bar = "▰" * filled + "▱" * (length - filled)
    return f"[{bar}] {int(pct * 100)}%"

class AutoRole(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.migration_task: asyncio.Task | None = None
        self.migration_cancel: bool = False
        self.migration_info: dict = {}

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

    # =========================================================================
    # CORE MASS ROLE ENGINE (FAST, CONCURRENT, NON-BLOCKING, RATELIMIT-SAFE)
    # =========================================================================

    async def _execute_migration(
        self,
        guild: discord.Guild,
        initiator: discord.User | discord.Member,
        target_role: discord.Role,
        remove_role: discord.Role | None,
        only_if_has_role: discord.Role | None,
        progress_msg: discord.Message | discord.WebhookMessage,
        concurrency: int = 3
    ):
        """Asynchronously migrates human members to target_role with real-time UI feedback."""
        start_time = time.time()
        self.migration_cancel = False

        try:
            # 1. Ensure members are loaded
            if len(guild.members) < guild.member_count:
                try:
                    await guild.chunk()
                except Exception as e:
                    print(f"Warning during guild.chunk(): {e}")

            bot_member = guild.get_member(self.bot.user.id)

            # 2. Filter candidates (strictly skip bots, owner, higher hierarchy)
            all_members = list(guild.members)
            candidates: list[discord.Member] = []
            skipped_bots = 0
            already_correct = 0

            for m in all_members:
                if m.bot:
                    skipped_bots += 1
                    continue
                if m.id == guild.owner_id:
                    continue
                if bot_member and m.top_role >= bot_member.top_role:
                    continue
                if only_if_has_role and only_if_has_role not in m.roles:
                    continue

                current_rids = {r.id for r in m.roles}
                has_target = target_role.id in current_rids
                has_remove = (remove_role.id in current_rids) if remove_role else False

                if has_target and not has_remove:
                    already_correct += 1
                    continue

                candidates.append(m)

            total_candidates = len(candidates)
            if total_candidates == 0:
                embed = discord.Embed(
                    title="✦ MASS ROLE OPERATION ✦",
                    description=(
                        f"✨ All human members already have **{target_role.mention}**"
                        + (f" and none hold **{remove_role.mention}**." if remove_role else ".")
                        + "\n\nNo member updates were required."
                    ),
                    color=COLOR_MINT
                )
                embed.set_footer(text="Destiny ✦ Role Operations")
                return await progress_msg.edit(content=None, embed=embed)

            # 3. Setup work queue and workers
            queue = asyncio.Queue()
            for m in candidates:
                queue.put_nowait(m)

            success_count = 0
            error_count = 0
            processed_count = 0
            lock = asyncio.Lock()
            last_edit_time = 0.0

            self.migration_info = {
                "running": True,
                "total": total_candidates,
                "processed": 0,
                "success": 0,
                "errors": 0,
                "start_time": start_time,
                "target_role": target_role.name,
                "remove_role": remove_role.name if remove_role else None
            }

            async def worker(worker_id: int):
                nonlocal success_count, error_count, processed_count, last_edit_time
                while not queue.empty() and not self.migration_cancel:
                    try:
                        member: discord.Member = queue.get_nowait()
                    except asyncio.QueueEmpty:
                        break

                    try:
                        # Construct new roles atomically in 1 single HTTP request
                        current_rids = {r.id for r in member.roles if r.id != guild.id}
                        if remove_role:
                            current_rids.discard(remove_role.id)
                        current_rids.add(target_role.id)

                        new_roles = [guild.get_role(rid) for rid in current_rids if guild.get_role(rid) is not None]
                        await member.edit(roles=new_roles, reason=f"Destiny Mass Role by Master {initiator}")

                        async with lock:
                            success_count += 1
                    except discord.Forbidden:
                        async with lock:
                            error_count += 1
                    except discord.HTTPException as e:
                        async with lock:
                            error_count += 1
                            if e.status != 429:
                                print(f"[Worker {worker_id}] HTTP error on {member.id}: {e}")
                    except Exception as e:
                        async with lock:
                            error_count += 1
                            print(f"[Worker {worker_id}] Unexpected error on {member.id}: {e}")
                    finally:
                        async with lock:
                            processed_count += 1
                            self.migration_info["processed"] = processed_count
                            self.migration_info["success"] = success_count
                            self.migration_info["errors"] = error_count

                            now = time.time()
                            # Throttle Discord message edits to at most once every 3.5 seconds
                            if (now - last_edit_time >= 3.5) or (processed_count == total_candidates):
                                last_edit_time = now
                                elapsed = now - start_time
                                rate = processed_count / elapsed if elapsed > 0 else 0
                                remaining = (total_candidates - processed_count) / rate if rate > 0 else 0
                                bar = make_progress_bar(processed_count, total_candidates)

                                embed = discord.Embed(
                                    title="✦ MASS ROLE OPERATION IN PROGRESS ✦",
                                    description=(
                                        f"**Target Role:** {target_role.mention}\n"
                                        + (f"**Removing Role:** {remove_role.mention}\n" if remove_role else "")
                                        + f"**Progress:** `{bar}`\n"
                                        f"**Processed:** `{processed_count} / {total_candidates}` humans\n"
                                        f"**Updated:** `{success_count}` | **Errors/Skipped:** `{error_count}`\n"
                                        f"**Elapsed:** `{int(elapsed)}s` | **ETA:** `~{int(remaining)}s`\n\n"
                                        f"🌸 *Updating active member roles on Discord...*"
                                    ),
                                    color=COLOR_ROSE
                                )
                                embed.set_footer(text="Destiny ✦ Fast Role Worker • Use /role-mass-cancel to halt")
                                try:
                                    await progress_msg.edit(content=None, embed=embed)
                                except Exception:
                                    pass

                        queue.task_done()
                        await asyncio.sleep(0.04)

            workers = [asyncio.create_task(worker(i)) for i in range(concurrency)]
            await asyncio.gather(*workers)

            total_elapsed = time.time() - start_time
            is_cancelled = self.migration_cancel

            final_title = "✦ MASS ROLE OPERATION CANCELLED ✦" if is_cancelled else "✦ MASS ROLE OPERATION COMPLETE ✦"
            final_color = COLOR_WARN if is_cancelled else COLOR_MINT
            final_status = "Operation stopped early by Master." if is_cancelled else "All human members have been successfully updated! ✨"

            embed = discord.Embed(
                title=final_title,
                description=(
                    f"**Status:** {final_status}\n\n"
                    f"**Target Role:** {target_role.mention}\n"
                    + (f"**Removed Role:** {remove_role.mention}\n" if remove_role else "")
                    + f"**Total Humans Targeted:** `{total_candidates}`\n"
                    f"**Successfully Updated:** `{success_count}`\n"
                    f"**Skipped Bots:** `{skipped_bots}`\n"
                    f"**Errors/Skipped:** `{error_count}`\n"
                    f"**Duration:** `{int(total_elapsed // 60)}m {int(total_elapsed % 60)}s`"
                ),
                color=final_color
            )
            embed.set_footer(text="Destiny ✦ Role Operations")
            await progress_msg.edit(content=f"🌸 {initiator.mention}", embed=embed)

        except Exception as e:
            print(f"❌ Mass role migration exception: {e}")
            try:
                err_embed = make_kawaii_embed(
                    title="✦ Migration Interrupted",
                    description=f"An unexpected error occurred during execution: `{e}`",
                    color=COLOR_WARN
                )
                await progress_msg.edit(content=None, embed=err_embed)
            except Exception:
                pass
        finally:
            self.migration_task = None
            self.migration_cancel = False
            self.migration_info = {"running": False}

    # =========================================================================
    # SLASH COMMANDS
    # =========================================================================

    @app_commands.command(
        name="role-all-humans",
        description="🌸 Rapidly assign a chosen role to all human members (skipping bots)"
    )
    @app_commands.describe(
        target_role="The role to give to all human members",
        remove_role="Optional: Role to strip away from everyone (e.g. Members)",
        only_if_has_role="Optional: Only modify members who currently have this role"
    )
    async def role_all_humans(
        self,
        interaction: discord.Interaction,
        target_role: discord.Role,
        remove_role: discord.Role | None = None,
        only_if_has_role: discord.Role | None = None
    ):
        if not is_owner(interaction.user.id):
            return await interaction.response.send_message(embed=denied_embed(), ephemeral=True)

        if self.migration_task and not self.migration_task.done():
            embed = make_kawaii_embed(
                title="✦ Operation In Progress",
                description="Another mass role migration is already running! Use `/role-mass-cancel` to stop it or `/role-mass-status` to inspect it.",
                color=COLOR_WARN
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        bot_member = interaction.guild.get_member(self.bot.user.id)
        if target_role >= bot_member.top_role:
            embed = make_kawaii_embed(
                title="✦ Role Hierarchy Error",
                description=f"The target role **{target_role.name}** is higher than or equal to `Destiny`.\nPlease move `Destiny` higher in **Server Settings -> Roles**.",
                color=COLOR_WARN
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        if remove_role and remove_role >= bot_member.top_role:
            embed = make_kawaii_embed(
                title="✦ Role Hierarchy Error",
                description=f"The role to remove **{remove_role.name}** is higher than or equal to `Destiny`.\nPlease move `Destiny` higher in **Server Settings -> Roles**.",
                color=COLOR_WARN
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        await interaction.response.defer(thinking=False)

        init_embed = discord.Embed(
            title="✦ INITIALIZING MASS ROLE OPERATION ✦",
            description=(
                f"**Target Role:** {target_role.mention}\n"
                + (f"**Removing Role:** {remove_role.mention}\n" if remove_role else "")
                + (f"**Filter (Only with):** {only_if_has_role.mention}\n" if only_if_has_role else "")
                + "\n🌸 *Scanning human members and launching fast concurrent workers...*"
            ),
            color=COLOR_ROSE
        )
        init_embed.set_footer(text="Destiny ✦ Role Operations")
        progress_msg = await interaction.followup.send(embed=init_embed)

        self.migration_task = asyncio.create_task(
            self._execute_migration(
                guild=interaction.guild,
                initiator=interaction.user,
                target_role=target_role,
                remove_role=remove_role,
                only_if_has_role=only_if_has_role,
                progress_msg=progress_msg,
                concurrency=3
            )
        )

    @app_commands.command(name="role-mass-cancel", description="🌸 Stop the currently running mass role operation")
    async def role_mass_cancel(self, interaction: discord.Interaction):
        if not is_owner(interaction.user.id):
            return await interaction.response.send_message(embed=denied_embed(), ephemeral=True)

        if not self.migration_task or self.migration_task.done():
            embed = make_kawaii_embed(
                title="✦ No Active Operation",
                description="There is currently no mass role migration running.",
                color=COLOR_PINK
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        self.migration_cancel = True
        embed = make_kawaii_embed(
            title="✦ Cancellation Requested",
            description="Stopping mass role operation... Any worker currently processing will complete cleanly and report final stats. 🌸",
            color=COLOR_WARN
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="role-mass-status", description="🌸 Check status of active mass role operation")
    async def role_mass_status(self, interaction: discord.Interaction):
        if not is_owner(interaction.user.id):
            return await interaction.response.send_message(embed=denied_embed(), ephemeral=True)

        if not self.migration_info.get("running"):
            embed = make_kawaii_embed(
                title="✦ Mass Role Status",
                description="No mass role operation is currently active. 🌸",
                color=COLOR_PINK
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        total = self.migration_info.get("total", 0)
        proc = self.migration_info.get("processed", 0)
        succ = self.migration_info.get("success", 0)
        err = self.migration_info.get("errors", 0)
        bar = make_progress_bar(proc, total)

        embed = discord.Embed(
            title="✦ MASS ROLE STATUS ✦",
            description=(
                f"**Target Role:** `{self.migration_info.get('target_role')}`\n"
                f"**Removing Role:** `{self.migration_info.get('remove_role') or 'None'}`\n"
                f"**Progress:** `{bar}`\n"
                f"**Processed:** `{proc} / {total}`\n"
                f"**Success:** `{succ}` | **Errors:** `{err}`"
            ),
            color=COLOR_ROSE
        )
        embed.set_footer(text="Destiny ✦ Role Operations")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # =========================================================================
    # PREFIX COMMANDS (!roleall, !roletransfer, !rolecancel, !rolestatus)
    # =========================================================================

    @commands.command(name="roleall", aliases=["massrole", "roleallhumans"])
    async def prefix_role_all(
        self,
        ctx: commands.Context,
        target_role: discord.Role,
        remove_role: discord.Role | None = None
    ):
        """Prefix command: !roleall @TargetRole [@RemoveRole]"""
        if not is_owner(ctx.author.id):
            return await ctx.send(embed=denied_embed())

        if self.migration_task and not self.migration_task.done():
            return await ctx.send("✦ A mass role operation is already running! Use `!rolecancel` to stop it.")

        bot_member = ctx.guild.get_member(self.bot.user.id)
        if target_role >= bot_member.top_role:
            return await ctx.send(f"✦ Error: Role **{target_role.name}** is higher or equal to `Destiny` role.")
        if remove_role and remove_role >= bot_member.top_role:
            return await ctx.send(f"✦ Error: Role **{remove_role.name}** is higher or equal to `Destiny` role.")

        msg = await ctx.send(f"🌸 Initializing mass role assignment for all humans to **{target_role.name}**...")

        self.migration_task = asyncio.create_task(
            self._execute_migration(
                guild=ctx.guild,
                initiator=ctx.author,
                target_role=target_role,
                remove_role=remove_role,
                only_if_has_role=None,
                progress_msg=msg,
                concurrency=3
            )
        )

    @commands.command(name="roletransfer", aliases=["transfer"])
    async def prefix_role_transfer(
        self,
        ctx: commands.Context,
        from_role: discord.Role,
        to_role: discord.Role
    ):
        """Prefix command: !roletransfer @FromRole @ToRole"""
        if not is_owner(ctx.author.id):
            return await ctx.send(embed=denied_embed())

        if self.migration_task and not self.migration_task.done():
            return await ctx.send("✦ A mass role operation is already running! Use `!rolecancel` to stop it.")

        bot_member = ctx.guild.get_member(self.bot.user.id)
        if to_role >= bot_member.top_role or from_role >= bot_member.top_role:
            return await ctx.send(f"✦ Error: Roles must be below `Destiny` role in Server Settings.")

        msg = await ctx.send(f"🌸 Transferring members holding **{from_role.name}** to **{to_role.name}**...")

        self.migration_task = asyncio.create_task(
            self._execute_migration(
                guild=ctx.guild,
                initiator=ctx.author,
                target_role=to_role,
                remove_role=from_role,
                only_if_has_role=from_role,
                progress_msg=msg,
                concurrency=3
            )
        )

    @commands.command(name="rolecancel")
    async def prefix_role_cancel(self, ctx: commands.Context):
        """Prefix command: !rolecancel"""
        if not is_owner(ctx.author.id):
            return await ctx.send(embed=denied_embed())

        if not self.migration_task or self.migration_task.done():
            return await ctx.send("✦ No mass role migration is currently active.")

        self.migration_cancel = True
        await ctx.send("🌸 Stopping mass role operation cleanly...")

    @commands.command(name="rolestatus")
    async def prefix_role_status(self, ctx: commands.Context):
        """Prefix command: !rolestatus"""
        if not is_owner(ctx.author.id):
            return await ctx.send(embed=denied_embed())

        if not self.migration_info.get("running"):
            return await ctx.send("✦ No mass role operation is currently active.")

        total = self.migration_info.get("total", 0)
        proc = self.migration_info.get("processed", 0)
        succ = self.migration_info.get("success", 0)
        bar = make_progress_bar(proc, total)
        await ctx.send(f"🌸 **Mass Role Status:** `{bar}` ({proc}/{total}) | Success: `{succ}`")

async def setup(bot: commands.Bot):
    await bot.add_cog(AutoRole(bot))
