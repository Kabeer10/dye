"""Vicinae."""
import re
import subprocess

from .. import util


def vicinae(ctx):
    theme = ctx.file("vicinae.toml")
    if not theme or not util.have("vicinae"):
        return
    settings = ctx.paths.config / "vicinae" / "settings.json"
    if not settings.is_file():
        return  # vicinae isn't set up for this user
    changed = util.install_file(theme, ctx.paths.data / "vicinae" / "themes" / "dye.toml")
    text = settings.read_text()
    # One theme id for both schemes: its contents follow the dye theme.
    new = re.sub(r'("(?:light|dark)"\s*:\s*\{[^{}]*?"name"\s*:\s*)"[^"]*"', r'\1"dye"', text)
    if new != text:
        util.atomic_write(settings, new)
        changed = True
    # Vicinae parses theme files once at startup, so a new palette needs a server restart.
    if changed and not util.SANDBOX:
        subprocess.run(["systemctl", "--user", "try-restart", "vicinae.service"],
                       capture_output=True, timeout=15)

