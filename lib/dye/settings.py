"""~/.config/dye/settings.toml, merged over the defaults below."""
import copy
import sys
import tomllib

DEFAULTS = {
    "mode": {
        # The themes GNOME's Dark Style toggle switches between, until you pick
        # others (each pick is remembered for its mode in the state folder).
        "dark": "vesper",
        "light": "flexoki-light",
        # Flip to the paired theme when Dark Style changes in Quick Settings.
        "follow_toggle": True,
    },
    "icons": {
        # "colloid": an Omarchy theme's Yaru-<colour> icons become the matching
        # Colloid colour when it's installed. "theme": use icons.theme as is.
        "style": "colloid",
    },
    "shell": {
        # Cross-fade the whole screen while the theme changes underneath.
        "transition": True,
    },
    "apps": {
        # Set an app to false and dye leaves it alone.
        "ghostty": True, "claude": True, "t3code": True, "vscode": True, "zen": True,
        "vicinae": True, "gtk": True, "gnome": True, "shell": True,
    },
}


def _merge(base, over):
    for key, value in over.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _merge(base[key], value)
        else:
            base[key] = value
    return base


def load(paths):
    settings = copy.deepcopy(DEFAULTS)
    if paths.settings.is_file():
        try:
            _merge(settings, tomllib.loads(paths.settings.read_text()))
        except tomllib.TOMLDecodeError as e:
            print(f"dye: ignoring {paths.settings}: {e}", file=sys.stderr)
    return settings


def app_enabled(settings, app):
    return bool(settings.get("apps", {}).get(app, True))


TEMPLATE = """\
# dye settings. Everything here is optional; these are the defaults.

[mode]
# The themes GNOME's Dark Style toggle switches between. Each theme you pick
# becomes the remembered one for its mode, so these only matter at first.
dark = "vesper"
light = "flexoki-light"
follow_toggle = true

[icons]
# "colloid" maps an Omarchy theme's Yaru-<colour> icons to the Colloid colour.
# "theme" uses the theme's icons.theme as is.
style = "colloid"

[shell]
transition = true

[apps]
# Set an app to false to leave it alone: ghostty, claude, t3code, vscode, zen,
# vicinae, gtk, gnome (icons, GTK3 theme, tiling-assistant), shell.
vscode = true
"""
