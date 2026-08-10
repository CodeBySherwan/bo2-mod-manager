"""Launcher for running from source:  python run.py

Equivalent to `python -m bo2_mod_manager`. Also used as the PyInstaller entry
point when building the portable .exe."""

from bo2_mod_manager.app import main

if __name__ == "__main__":
    main()
