# BO2 Mod Manager

![Version 2.0](https://img.shields.io/badge/Version-2.0-green?style=flat-square)
![Windows 10/11](https://img.shields.io/badge/Platform-Windows%2010%2F11-0078D4?style=flat-square)
![Built With](https://img.shields.io/badge/Built%20With-Python%20%7C%20PyQt6-3776AB?style=flat-square)

A desktop application for managing and deploying custom mods for **Call of Duty: Black Ops II** on the **Plutonium** platform. No more dragging folders around or losing track of which mod is active, manually copying scripts and images over and over. Point, click, deploy, launch.

## Screenshots

![1](https://media.moddb.com/images/members/5/4960/4959168/profile/Screenshot_2026-08-10_213029.png)
![2](https://media.moddb.com/images/members/5/4960/4959168/profile/Screenshot_2026-08-10_213208.png)
![3](https://media.moddb.com/images/members/5/4960/4959168/profile/Screenshot_2026-08-10_213327.png)
![4](https://media.moddb.com/images/members/5/4960/4959168/profile/Screenshot_2026-08-10_213547.png)

## What's New in v2.0

- ⬇ **FETCH FROM WEB** — paste a Plutonium forum mod link and the app opens a real browser window, clears the Cloudflare check, and auto-downloads the mod's preview image and description into its folder as `Preview.png` + `readme.txt`.
- ■ **Offline LAN Launcher** — one-click **MULTIPLAYER** / **ZOMBIES** launch buttons that fire Plutonium's bootstrapper with `-lan`, no internet required.
- ★ **Favorites system** — right-click to favorite, ★ FAVS filter, favorites float to the top.
- 📷 **Preview & Info panel** — live `Preview.png` + `readme.txt` right in the window.
- 🎨 **5 eye-friendly themes** with a live swatch picker — switched instantly, saved automatically.
- ⚠ **Debug log** — every action is logged to `bo2mm_debug.log` beside the app for easy troubleshooting.

## Features

### Mod Management

- ✔ Automatically scans your `MyMods` folder and detects mods with MP and/or ZM scripts
- ✔ Deploys the selected mod's scripts and images to your Plutonium T6 installation
- ✔ Reset restores stock/vanilla files instantly
- ✔ Keeps track of the currently active mod per mode

### Preview & Info Panel

- ✔ Select any mod and see its `Preview.png` rendered in the right panel
- ✔ Read the mod's `readme.txt` description below the preview
- ✔ No more guessing which mod is which

### Favorites System

- ✔ Right-click any mod to add/remove it from favorites
- ✔ Favorites appear first in the list with a star indicator
- ✔ Toggle "★ FAVS" to show only your favorite mods

### Multiplayer & Zombies Separation

- ✔ Dedicated **MP** and **ZM** tabs in the mods panel
- ✔ Each mode maintains its own list, active mod, and favorites

### Fetch From Web — Auto-Download Preview & Description (NEW in v2.0)

- ✔ Select a mod and hit **⬇ FETCH FROM WEB** — paste a Plutonium forum mod link (e.g. `https://forum.plutonium.pw/topic/...`)
- ✔ A real embedded browser window (WebView2 via pywebview — no bundled Chromium, so the app stays small) opens the page in a separate process, so the UI never freezes
- ✔ If a Cloudflare challenge appears, the app waits (up to a few minutes, with a live countdown) for it to clear, then extracts the post automatically
- ✔ Extracts the post's title, preview image, and description — you can edit the text before saving
- ✔ Saves them straight into the mod folder as `Preview.png` + `readme.txt`, and the preview panel refreshes instantly
- ✔ **MANUAL** mode is always there as a fallback — enter title/description/image by hand

### Embedded Offline LAN Launcher (NEW in v2.0)

- ✔ One-click **■ MULTIPLAYER** and **■ ZOMBIES** launch buttons
- ✔ Launches Plutonium's bootstrapper with `-lan` — pure offline LAN play, no internet required
- ✔ Validates your install before launching: launcher EXE, Black Ops II folder (`zone/all/base.ipak`), and your in-game name

### 5 Built-in Themes

| Theme | Mood | Accent |
|-------|------|--------|
| **BLACK OPS II** | Dark charcoal, military HUD | Orange |
| **MODERN WARFARE** | Tactical green, grey | Olive green |
| **COLD WAR** | Dark, cold | Crimson red |
| **CLASSIFIED** | Pure black, CRT glitch | Blood red |
| **LIGHT OPS** | Light briefing room | Warm orange |

✔ In v2.0 the theme switcher is a live **swatch picker** — click a color swatch and the whole UI re-skins instantly. Your choice is saved to the config and restored next launch.

### COD-Inspired Typography

- ✔ Impact for headings, Segoe UI for body — the same weight and feel as the game menus
- ✔ Monospace Consolas for paths and technical readouts

### Portable Executable

- ✔ Single `.exe` file, zero dependencies
- ✔ Configuration saves alongside the executable (`bo2mm_config.ini`)
- ✔ Full debug log (`bo2mm_debug.log`) lives in the same folder — easy to grab when reporting a bug
- ✔ No installers, no registry entries, no bloat

## Installation

### Option 1: Portable EXE (Recommended)

1. Download `BO2ModManager.zip` (Contains the exe file + the source code if you want to check)
2. Drop it anywhere — USB drive, desktop, game folder — it just works
3. Run it

## Quick Start

1. Launch the app
2. Click **BROWSE** next to **MYMODS** and select your `MyMods` folder
3. Click **BROWSE** or **DET** next to **T6** to point to your Plutonium `storage/t6` folder (DET auto-detects it)
4. Click **BROWSE** next to **BO2** and select your Black Ops II install folder (checked for `zone/all/base.ipak`)
5. Click **BROWSE** or **DET** next to **EXE** and select the launcher — `plutonium-launcher-win32.exe`
6. Enter your in-game name (required for launching)
7. Switch between **MP** and **ZM** tabs to browse available mods
8. Click a mod to preview it, then hit **▶ DEPLOY MOD**
9. Click **■ MULTIPLAYER** or **■ ZOMBIES** to launch offline and play

**Typical paths**

```
MyMods: %localappdata%\Plutonium\storage\t6\MyMods
T6: %localappdata%\Plutonium\storage\t6
BO2: C:\Games\Steam\steamapps\common\Call of Duty Black Ops II
Exe: %localappdata%\Plutonium\bin\plutonium-launcher-win32.exe
```

## How It Works

- **Scan** — the app reads your `MyMods` directory and checks each folder for `scripts/mp` or `scripts/zm` subdirectories
- **Preview** — when you click a mod, it loads `Preview.png` and, for the description, it reads `readme.txt` from that mod's folder
- **Deploy** — copies the mod's scripts to `t6/scripts/mp` (wiping any previously deployed mod for that mode beforehand) and merges its `images/` folder into `t6/images` if the mod contains images
- **Launch** — fires the Plutonium bootstrapper with `-lan` in its own directory so Plutonium picks the mod up correctly, offline

## Configuration

Settings are stored in `bo2mm_config.ini` alongside the executable:

```
[Paths]
mymods_dir = C:/Users/.../Plutonium/storage/t6/MyMods
t6_root = C:/Users/.../Plutonium/storage/t6
game_exe = C:/Users/.../Plutonium/bin/plutonium-launcher-win32.exe
active_mp = MyCoolMod
active_zm = AnotherMod

[UI]
theme = black_ops

[Favorites]
mp = ModAlpha,ModBravo
zm = ModCharlie
```

You can edit it manually, but the app manages everything through the UI.

## Changelog

Full history is also maintained in `CHANGELOG.md` alongside this project.

### v2.0.0 — 2025 (LATEST)

**Added**

- **Fetch From Web** — paste a Plutonium forum mod link and the app opens a real embedded browser window (WebView2 via pywebview, no bundled Chromium), waits out the Cloudflare check with a live countdown, then auto-extracts the post's title, preview image and description and saves them as `Preview.png` + `readme.txt` in the mod folder. Editable before saving; **MANUAL** entry always available as a fallback.
- **Embedded Offline LAN Launcher** — one-click **■ MULTIPLAYER** / **■ ZOMBIES** buttons fire Plutonium's bootstrapper with `-lan` for fully offline play, with install validation (launcher EXE, BO2 folder `zone/all/base.ipak`, in-game name).
- **Live theme swatch picker** — 5 themes (BLACK OPS II, MODERN WARFARE, COLD WAR, CLASSIFIED, LIGHT OPS) re-skin the UI instantly; your choice persists across sessions.
- **Favorites system** — right-click a mod to add/remove it, favorites float to the top with a star, and the **★ FAVS** toggle filters the list.
- **Preview & Info panel** — renders the mod's `Preview.png` and its `readme.txt` description directly in the main window.
- **Debug log** — every action is logged to `bo2mm_debug.log` beside the app for easy troubleshooting.

**Changed**

- Fetch engine moved from a bundled Chromium to **pywebview + the OS WebView2 runtime** — smaller app, no QtWebEngine flag juggling.
- Fetch dialog now opens non-modally (`open()` instead of a modal `exec()` loop), fixing a teardown crash seen on some Windows machines.
- Deployment flow polished — scripts are wiped then copied per mode, images merge into `t6/images`, and the active mod is saved and highlighted with a status-bar confirmation.

**Fixed**

- Cloudflare wait is now driven by real page events plus periodic checks instead of a fixed timer — it no longer gives up while the page is still loading.
- Re-fetching a link no longer picks up stale state from the previous page.
- Various stability fixes in the embedded browser subprocess.

### v1.0.0 — 2025

**Added**

- Automatically scans your `MyMods` folder and detects mods with MP and/or ZM scripts.
- Deploys the selected mod's scripts and images to your Plutonium T6 installation.
- Reset restores stock/vanilla files instantly.
- Keeps track of the currently active mod per mode.
- Portable single-`.exe` layout with configuration saved alongside the executable.

## License

> This project is provided for educational and modding purposes. Call of Duty: Black Ops II is a registered trademark of Activision Publishing, Inc. Plutonium is a third-party modding platform. This tool is not affiliated with or endorsed by Activision or the Plutonium team.

*Made for the community. Inspired by the golden era of FPS modding.*
*Good luck, soldier.*
