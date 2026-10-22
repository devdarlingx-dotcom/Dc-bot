import sys
import time
import asyncio
import discord
import database
from config import DISCORD_TOKEN

GUILD_ID = 1551121355770961933
ROLE_MEMBERS_ID = 1560798646889615551

async def main():
    intents = discord.Intents.default()
    intents.members = True

    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print("=" * 60)
        print(f"🌸 Destiny Connected as {client.user} (ID: {client.user.id})")
        guild = client.get_guild(GUILD_ID)
        if not guild:
            print(f"❌ Guild {GUILD_ID} not found!")
            await client.close()
            return

        print(f"🏰 Server: {guild.name}")
        role_members = guild.get_role(ROLE_MEMBERS_ID)
        if not role_members:
            print(f"❌ Role {ROLE_MEMBERS_ID} not found!")
            await client.close()
            return

        print(f"🎯 Target Role: {role_members.name} ({role_members.id})")
        bot_member = guild.get_member(client.user.id)

        # 1. REMOVE 'Members' from ALL BOTS
        print("\n🤖 [STEP 1] Removing 'Members' from all bots...")
        bots_cleaned = 0
        bots_failed = 0
        for m in guild.members:
            if m.bot and role_members in m.roles:
                try:
                    await m.remove_roles(role_members, reason="Destiny: Bots must not have Members role")
                    print(f"  ✅ Removed Members from bot: {m.name} ({m.id})")
                    bots_cleaned += 1
                    await asyncio.sleep(0.3)
                except Exception as e:
                    print(f"  ❌ Failed on bot {m.name}: {e}")
                    bots_failed += 1

        print(f"✨ Step 1 Complete: {bots_cleaned} bots cleaned, {bots_failed} failed.")

        # 2. ADD 'Members' to ALL HUMANS WHO LACK IT
        print("\n👥 [STEP 2] Adding 'Members' to all human members without it...")
        humans_to_add = [m for m in guild.members if not m.bot and role_members not in m.roles and m.id != guild.owner_id]
        print(f"Found {len(humans_to_add)} humans needing the '{role_members.name}' role.")

        humans_added = 0
        humans_failed = 0
        for i, m in enumerate(humans_to_add, 1):
            try:
                await m.add_roles(role_members, reason="Destiny: Assigning default Members role to human")
                print(f"  [{i}/{len(humans_to_add)}] ✅ Added Members to: {m.name} ({m.id})")
                humans_added += 1
                await asyncio.sleep(0.3)
            except Exception as e:
                print(f"  [{i}/{len(humans_to_add)}] ❌ Failed on {m.name}: {e}")
                humans_failed += 1

        print(f"✨ Step 2 Complete: {humans_added} humans granted '{role_members.name}', {humans_failed} failed.")

        # 3. SET AUTOROLE IN DATABASE FOR FUTURE JOINS
        print("\n⚙️ [STEP 3] Updating database autorole configuration...")
        await database.set_autorole(guild.id, role_members.id)
        print(f"✅ Database autorole_id configured to: {role_members.id} ({role_members.name})")

        # 4. FINAL VERIFICATION
        print("\n📊 [STEP 4] Final Server Role Audit:")
        bots_with_members = sum(1 for m in guild.members if m.bot and role_members in m.roles)
        humans_without_members = sum(1 for m in guild.members if not m.bot and role_members not in m.roles and m.id != guild.owner_id)
        humans_with_members = sum(1 for m in guild.members if not m.bot and role_members in m.roles)

        print(f"  • Total Bots with Members: {bots_with_members} (Expected: 0)")
        print(f"  • Total Humans WITH Members: {humans_with_members}")
        print(f"  • Total Humans WITHOUT Members: {humans_without_members} (Expected: 0)")
        print("=" * 60)
        print("🎉 OPERATION COMPLETE! ALL MEMBERS AND BOTS ARE SYNCHRONIZED! 🌸✨\n")
        await client.close()

    try:
        await client.start(DISCORD_TOKEN)
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
