import os
import sys
import time
import asyncio
import argparse
import discord
from config import DISCORD_TOKEN

GUILD_ID = 1551121355770961933

async def run_migration(target_role_id: int, remove_role_id: int | None = None, dry_run: bool = False, concurrency: int = 3):
    intents = discord.Intents.default()
    intents.members = True

    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f"🌸 Connected as {client.user} (ID: {client.user.id})")
        guild = client.get_guild(GUILD_ID)
        if not guild:
            print(f"❌ Guild {GUILD_ID} not found!")
            await client.close()
            return

        print(f"🏰 Server: {guild.name} ({guild.id})")
        print(f"📊 Total Members reported: {guild.member_count}")
        
        if len(guild.members) < guild.member_count:
            print("⏳ Chunking guild members...")
            await guild.chunk()

        bot_member = guild.get_member(client.user.id)
        target_role = guild.get_role(target_role_id)
        remove_role = guild.get_role(remove_role_id) if remove_role_id else None

        if not target_role:
            print(f"❌ Target role {target_role_id} not found in guild!")
            await client.close()
            return

        print(f"🎯 Target Role: {target_role.name} ({target_role.id})")
        if remove_role:
            print(f"🗑️ Role to Remove: {remove_role.name} ({remove_role.id})")
        else:
            print("🗑️ Role to Remove: None")

        # Hierarchy check
        if target_role >= bot_member.top_role:
            print(f"❌ Target role {target_role.name} is higher or equal to bot top role {bot_member.top_role.name}!")
            await client.close()
            return
        if remove_role and remove_role >= bot_member.top_role:
            print(f"❌ Remove role {remove_role.name} is higher or equal to bot top role {bot_member.top_role.name}!")
            await client.close()
            return

        # Filter candidates
        all_members = list(guild.members)
        humans_to_process = []
        already_correct = 0
        bots_skipped = 0

        for m in all_members:
            if m.bot:
                bots_skipped += 1
                continue
            if m.id == guild.owner_id:
                continue
            if m.top_role >= bot_member.top_role:
                continue

            current_rids = {r.id for r in m.roles}
            has_target = target_role.id in current_rids
            has_remove = (remove_role.id in current_rids) if remove_role else False

            if has_target and not has_remove:
                already_correct += 1
                continue

            humans_to_process.append(m)

        total_to_update = len(humans_to_process)
        print(f"\n📋 Analysis:")
        print(f"  • Total Cached Members: {len(all_members)}")
        print(f"  • Bots Skipped: {bots_skipped}")
        print(f"  • Humans Already Correct: {already_correct}")
        print(f"  • Humans Needing Update: {total_to_update}")

        if dry_run:
            print("\n🔍 DRY-RUN MODE: No changes will be made.")
            print(f"Sample of 5 candidates that would be modified:")
            for m in humans_to_process[:5]:
                print(f"  - {m.name} ({m.id}) | Current: {[r.name for r in m.roles if r.name != '@everyone']}")
            await client.close()
            return

        if total_to_update == 0:
            print("✨ All human members are already updated! Nothing to do.")
            await client.close()
            return

        print(f"\n🚀 Starting live migration for {total_to_update} members with {concurrency} workers...")
        queue = asyncio.Queue()
        for m in humans_to_process:
            queue.put_nowait(m)

        start_time = time.time()
        success_count = 0
        error_count = 0
        processed_count = 0
        lock = asyncio.Lock()

        async def worker(worker_id: int):
            nonlocal success_count, error_count, processed_count
            while not queue.empty():
                try:
                    member: discord.Member = await queue.get()
                except asyncio.QueueEmpty:
                    break

                try:
                    current_rids = {r.id for r in member.roles if r.id != guild.id}
                    if remove_role:
                        current_rids.discard(remove_role.id)
                    current_rids.add(target_role.id)

                    new_roles = [guild.get_role(rid) for rid in current_rids if guild.get_role(rid) is not None]
                    await member.edit(roles=new_roles, reason=f"Mass role migration by Destiny")
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
                        if processed_count % 25 == 0 or processed_count == total_to_update:
                            elapsed = time.time() - start_time
                            rate = processed_count / elapsed if elapsed > 0 else 0
                            remaining = (total_to_update - processed_count) / rate if rate > 0 else 0
                            pct = (processed_count / total_to_update) * 100
                            print(f"[{processed_count}/{total_to_update}] ({pct:.1f}%) | Success: {success_count} | Err: {error_count} | Rate: {rate:.1f} m/s | ETA: {remaining/60:.1f}m")
                    queue.task_done()
                    await asyncio.sleep(0.05)

        workers = [asyncio.create_task(worker(i)) for i in range(concurrency)]
        await asyncio.gather(*workers)

        total_elapsed = time.time() - start_time
        print("\n" + "=" * 60)
        print("🎉 MASS ROLE MIGRATION COMPLETE!")
        print(f"  • Total Processed: {processed_count}")
        print(f"  • Successfully Updated: {success_count}")
        print(f"  • Errors/Skipped: {error_count}")
        print(f"  • Total Duration: {total_elapsed/60:.2f} minutes")
        print("=" * 60 + "\n")
        await client.close()

    try:
        await client.start(DISCORD_TOKEN)
    except Exception as e:
        print(f"❌ Error starting client: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Destiny Mass Role Migration CLI")
    parser.add_argument("--target-role", type=int, required=True, help="Target Role ID to grant")
    parser.add_argument("--remove-role", type=int, default=None, help="Role ID to remove (optional)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without modifying roles")
    parser.add_argument("--concurrency", type=int, default=3, help="Number of concurrent workers (default: 3)")

    args = parser.parse_args()
    asyncio.run(run_migration(args.target_role, args.remove_role, dry_run=args.dry_run, concurrency=args.concurrency))
