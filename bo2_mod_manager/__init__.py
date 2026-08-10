"""BO2 Mod Manager - a desktop manager for Black Ops II (Plutonium) mods."""

from .constants import VERSION as __version__


def main():
    from .app import main as _main
    _main()
