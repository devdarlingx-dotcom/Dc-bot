# 🌸 Destiny - Kawaii Discord Bot ✨

> A pastel-aesthetic, full-featured Discord Bot with an interactive Discord `/panel`, built-in Kawaii Web Dashboard, Moderation, Giveaways, Script Update Broadcaster, Auto-Role, and Reaction Roles.  
> Strictly locked and controlled **only** by Master (`1560466119880347730`)! 🌸💕

---

## 🎀 Features Overview

- 🌸 **Master Lockdown**: Every moderation command, panel, and configuration check strictly verifies `interaction.user.id == 1560466119880347730`. Anyone else is greeted with a cute kawaii denied card: `(¬_¬) Gomen ne! Only my master can give me orders! 🌸`.
- 🌸 **Default Auto-Role**: Automatically awards a default role (e.g., `member` or `unverified`) to new cuties as soon as they join.
- 🎀 **Reaction Roles**: Supports **both** modern Discord interactive buttons (click to toggle role on/off) and classic emoji reactions!
- 📢 **Channel Broadcaster**: Send plain messages or gorgeous kawaii pastel embeds to any channel (`/say`, `/announce`).
- 🛡️ **Polite Kawaii Moderation**: `/ban`, `/kick`, `/timeout`, `/unmute`, `/purge` with gentle DM notices, reason tracking, and cute embeds.
- 🎁 **Interactive Giveaways**: Launch giveaways with custom duration (`10m`, `2h`, `1d`), interactive `🎉 Enter Giveaway` buttons, live participant counts, auto winner picking, and `/giveaway reroll`.
- 🚀 **Script Update Broadcaster**: Publish releases for your scripts with version tags, changelog codeblocks, download buttons, and optional role pings (`/update-script`).
- 🌸 **Cute Welcome Cards**: Greets new members in the welcome channel with their avatar, member count badge, and cheerful kaomojis.
- 🎛️ **Dual Control Panels**:
  1. **In-Discord Interactive `/panel`**: Tap buttons to open Modals and Select menus right inside Discord!
  2. **Kawaii Web Dashboard**: A pastel glassmorphism web panel (running on port `5000` or Railway dynamic `$PORT`) to control the bot from any browser!

---

## 🚀 24/7 Railway Deployment Guide

This repository is ready to be hosted 24/7 on [Railway](https://railway.app) in 2 minutes:

### Step 1: Connect Your GitHub Repository
1. Log in to [Railway.app](https://railway.app).
2. Click **+ New Project**.
3. Select **Deploy from GitHub repo**.
4. Choose this private repository: `darlingdev022/bot`.

### Step 2: Set Environment Variables
Go to your project in Railway, click on the **Service** -> **Variables** tab, and add:

| Variable | Recommended Value | Note |
|---|---|---|
| `DISCORD_TOKEN` | `MTU2MDQ5...` | Your Discord Bot Token |
| `OWNER_ID` | `1560466119880347730` | Your Discord User ID |
| `DASHBOARD_SECRET` | `destiny_kawaii_key_2026` | Secret password to unlock web dashboard |
| `PORT` | `5000` | Railway handles web routing |
| `DATABASE_PATH` | `data/destiny.db` | Path for SQLite storage |

### Step 3: Enable Public Web Dashboard (Optional)
1. In Railway, click **Settings** -> **Networking** -> **Generate Domain**.
2. Visit the generated URL in your browser!
3. Enter your `DASHBOARD_SECRET` to access the full visual control center! ✨

---

## 🌸 Discord Slash Commands Reference

### 🎛️ Master Control Center
| Command | Description |
|---|---|
| `/panel` | Opens the master interactive control center with buttons and modals |

### 🌸 Auto-Role
| Command | Description |
|---|---|
| `/autorole set <role>` | Sets the role given to new cuties upon joining |
| `/autorole disable` | Disables auto-role |
| `/autorole status` | Checks the active auto-role setup |

### 🎀 Reaction & Button Roles
| Command | Description |
|---|---|
| `/reactionrole button <role> <label> [emoji] [description]` | Spawns a modern interactive role toggle button |
| `/reactionrole emoji <message_id> <emoji> <role>` | Links an emoji reaction on any existing message to a role |

### 📢 Announcements
| Command | Description |
|---|---|
| `/say <channel> <message>` | Sends a plain message to any channel |
| `/announce <channel> <title> <description> [ping_role] [image_url]` | Broadcasts a rich pastel announcement embed |

### 🚀 Script Updates
| Command | Description |
|---|---|
| `/update-script <script_name> <version> <changelog> [download_url] [channel] [ping_role]` | Posts a script changelog card with download buttons |
| `/script-history` | Displays recently published script updates |

### 🎁 Giveaways
| Command | Description |
|---|---|
| `/giveaway start <duration> <prize> [winners] [channel]` | Launches a giveaway with join buttons and countdown |
| `/giveaway reroll <message_id>` | Rolls new winners for an ended giveaway |

### 🛡️ Moderation
| Command | Description |
|---|---|
| `/ban <member> [reason] [delete_days]` | Bans a member with DM notice and log |
| `/kick <member> [reason]` | Kicks a member with polite DM |
| `/timeout <member> <duration_minutes> [reason]` | Silences a member for specified minutes |
| `/unmute <member>` | Unmutes / clears timeout for a member |
| `/purge <amount>` | Deletes messages in bulk (1-100) |

### 🌸 Welcome Messages
| Command | Description |
|---|---|
| `/welcome set-channel <channel>` | Sets the welcome channel for new member cards |
| `/welcome test` | Sends a preview welcome card to test appearance |
| `/welcome disable` | Disables welcome messages |

---

## 🎀 Discord Developer Portal Note

Make sure privileged intents are turned **ON** in the Discord Developer Portal for the bot to read member joins and message reactions:
- **Server Members Intent**: `ON` (Needed for Auto-Role & Welcome Cards)
- **Message Content Intent**: `ON`
- **Presence Intent**: `ON`

---

*Made with love for Master `1560466119880347730` • (｡♥‿♥｡) 🌸*
