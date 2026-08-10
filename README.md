<p align="center">
  <img src="https://img.shields.io/badge/Platform-Windows%2010%2F11-0078D4?style=flat-square&logo=windows&logoColor=white"/>
  <img src="https://img.shields.io/badge/Games-Black%20Ops%20II%20%7C%20Plutonium-e87a20?style=flat-square"/>
  <img src="https://img.shields.io/badge/Built%20With-Python%20%7C%20PyQt6-3776AB?style=flat-square&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Version-2.0-green?style=flat-square"/>
  <img src="https://img.shields.io/badge/Status-Ready%20for%20Deploy-success?style=flat-square"/>
</p>

---

A desktop application for managing and deploying custom mods for **Call of Duty: Black Ops II** on the **Plutonium** platform. No more dragging folders around or losing track of which mod is active , manually copy scripts and images over and over. now : Point, click, deploy, launch.

---

## Features

**Mod Management**
- Automatically scans your `MyMods` folder and detects mods with MP and/or ZM scripts
- Deploys the selected mod's scripts and images to your Plutonium T6 installation
- Reset restores stock/vanilla files instantly
- Keeps track of the currently active mod per mode

**Preview & Info Panel**
- Select any mod and see its `Preview.png` rendered in the right panel
- Read the mod's `readme.txt` description below the preview
- No more guessing which mod is which

**Favorites System**
- Right-click any mod to add/remove it from favorites
- Favorites appear first in the list with a star indicator
- Toggle "★ FAVS" to show only your favorite mods

**Multiplayer & Zombies Separation**
- Dedicated **MP** and **ZM** tabs in the mods panel
- Each mode maintains its own list, active mod, and favorites

**5 Built-in Themes**

| Theme | Mood | Accent |
|-------|------|--------|
| **BLACK OPS II** | Dark charcoal, military HUD | Orange |
| **MODERN WARFARE** | Tactical green, grey | Olive green |
| **COLD WAR** | Dark, cold | Crimson red |
| **CLASSIFIED** | Pure black, CRT glitch | Blood red |
| **LIGHT OPS** | Light briefing room | Warm orange |

**COD-Inspired Typography**
- Impact for headings, Segoe UI for body — the same weight and feel as the game menus
- Monospace Consolas for paths and technical readouts

**Portable Executable**
- Single `.exe` file, zero dependencies
- Configuration saves alongside the executable
- No installers, no registry entries, no bloat

---

## Installation

### Option 1: Portable EXE (Recommended)

1. Download `BO2ModManager.exe` from the [Releases](https://github.com/codeBySherwan/bo2-mod-manager/releases) page
2. Drop it anywhere — USB drive, desktop, game folder — it just works
3. Run it

### Option 2: From Source

```batch
git clone https://github.com/codeBySherwan/bo2-mod-manager.git
cd bo2-mod-manager
pip install PyQt6
python run.py
```

(Or `python -m bo2_mod_manager` — equivalent.)

Requires Python 3.10+ and PyQt6. QtWebEngine is optional; without it the auto-fetch falls back to manual entry.

---

## Quick Start

1. Launch the app
2. Click **BROWSE** next to **MYMODS** and select your `MyMods` folder
3. Click **BROWSE** or **DET** next to **T6** to point to your Plutonium `storage/t6` folder
4. Click **BROWSE** next to **EXE** and select the game launcher (e.g. `plutonium-launcher-win32.exe`)
5. Switch between **MP** and **ZM** tabs to browse available mods
6. Click a mod to preview it, then hit **DEPLOY MOD**
7. Click **LAUNCH BLACK OPS II** and play

Typical paths:
```
MyMods:  %localappdata%\Plutonium\storage\t6\MyMods
T6:      %localappdata%\Plutonium\storage\t6
Exe:     %localappdata%\Plutonium\bin\plutonium-launcher-win32.exe
```

---

## Screenshots

<p align="center">
  <img width="1122" height="987" alt="image" src="https://github.com/user-attachments/assets/a545d904-da23-455b-b207-6d73f56b1d79" />
  <img width="1124" height="1008" alt="image" src="https://github.com/user-attachments/assets/846c495e-a05f-4005-93cf-707a15eda056" />



</p>

---

## How It Works

1. **Scan** — The app reads your `MyMods` directory and checks each folder for `scripts/mp` or `scripts/zm` subdirectories
2. **Preview** — When you click a mod, it loads `Preview.png` and reads `readme.txt` from that mod's folder
3. **Deploy** — Copies the mod's scripts to `t6/scripts/mp` (or `zm`) and merges its images into `t6/images`. Any previously deployed mod for that mode is wiped clean beforehand
4. **Launch** — Fires the game executable in its own directory so Plutonium picks it up correctly 

---

## Configuration

Settings are stored in `bo2mm_config.ini` alongside the executable:

```ini
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

---

## Theming

The stylesheet is built from a single template with colour tokens. Each theme is a dictionary of ~20 tokens (background, panel, card, accent, text, border, success, danger — each with variants). Adding a new theme is as simple as dropping in a new token set and adding it to `THEME_ORDER`.

---

## Building from Source

```batch
pip install pyinstaller
pyinstaller --onefile --noconsole --name "BO2ModManager" --icon icon.ico `
    --collect-all PyQt6.QtWebEngineCore --collect-all PyQt6.QtWebEngineWidgets run.py
```

`--collect-all` for the two WebEngine modules is required so the embedded
browser keeps working inside the packed exe. Output lands in
`dist/BO2ModManager.exe` — a fully self-contained portable binary.

---

## License

This project is provided for educational and modding purposes. Call of Duty: Black Ops II is a registered trademark of Activision Publishing, Inc. Plutonium is a third-party modding platform. This tool is not affiliated with or endorsed by Activision or the Plutonium team.

---

<p align="center">
  <sub>Made for the community. Inspired by the golden era of FPS modding.</sub><br>
  <sub>Good luck, soldier.</sub>
</p>
