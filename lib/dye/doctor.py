"""dye doctor: is every target wired up?"""
import json
import re
import subprocess
from pathlib import Path

from . import themes, util
from .apps import gnome as gnome_app
from .apps import web

OK, WARN, FAIL = "ok", "warn", "fail"


def _read(p):
    try:
        return Path(p).read_text()
    except OSError:
        return ""


def _service(name):
    r = subprocess.run(["systemctl", "--user", "is-active", name], capture_output=True, text=True)
    return r.stdout.strip()


def _enabled_extensions():
    out = util.gget("org.gnome.shell", "enabled-extensions") or "[]"
    return set(re.findall(r"'([^']+)'", out))


def checks(paths):
    home, cfg = paths.home, paths.config
    state = "~/.local/state/dye/current/theme"
    out = []

    def add(status, label, detail=""):
        out.append((status, label, detail))

    name = themes.current_name(paths)
    t = themes.find(paths, name) if name else None
    add(OK if t else FAIL, "current theme", name or "none set (dye theme set vesper)")
    cur = paths.current_theme
    for f in ("colors.json", "gnome.json", "gnome-shell.css"):
        add(OK if (cur / f).is_file() else FAIL, f"generated {f}", str(cur / f))
    n = len(themes.all_themes(paths))
    add(OK if n else FAIL, "themes available", f"{n} (dye theme list)")

    # GNOME
    ext = _enabled_extensions()
    add(OK if "dye-shell@riz1" in ext else FAIL, "dye-shell extension enabled",
        "gnome-extensions enable dye-shell@riz1 (then log out and in)")
    add(OK if gnome_app.shell_available() else FAIL, "dye-shell answering on D-Bus", "org.riz1.Dye.Ping")
    clash = ext & {"user-theme@gnome-shell-extensions.gcampax.github.com", "rice-shell@riz1", "rice-bar@riz1"}
    add(OK if not clash else WARN, "no conflicting extensions", ", ".join(sorted(clash)) or "")
    add(OK if _service("dye-mode-watch.service") == "active" else FAIL, "dye-mode-watch.service",
        _service("dye-mode-watch.service"))
    colloid = [c for c in ("Colloid-Orange-Dark", "Colloid-Teal-Light", "Colloid-Purple-Dark")
               if gnome_app.icon_installed(c, paths)]
    add(OK if len(colloid) == 3 else WARN, "Colloid colour variants", f"{len(colloid)}/3 sampled installed")
    add(OK if Path("/usr/share/themes/Yaru-dark/gnome-shell/gnome-shell.css").is_file() else FAIL,
        "Yaru shell stylesheet (base for the shell theme)", "")

    # terminal
    ghostty = _read(cfg / "ghostty/config") + _read(cfg / "ghostty/config.ghostty")
    add(OK if "dye/current/theme/ghostty.conf" in ghostty else FAIL,
        "ghostty includes the theme", f"config-file = ?{state}/ghostty.conf")
    zshrc = _read(home / ".zshrc")
    add(OK if "dye/current" in zshrc and "zsh-highlight.zsh" in zshrc else WARN,
        "zsh syntax highlighting follows", f"source {state}/zsh-highlight.zsh (after the plugin)")

    # agents / editors
    claude = _read(home / ".claude/settings.json")
    add(OK if '"custom:dye"' in claude else WARN, "Claude Code theme", "theme = custom:dye")
    add(OK if '"defaultTheme": "dye"' in _read(home / ".t3/userdata/settings.json") else WARN, "T3 Code theme", "")
    vs = _read(cfg / "Code/User/settings.json")
    try:  # the theme's own extension (vscode.json), else dye's generated one
        wanted = json.loads(_read(paths.current_theme / "vscode.json") or "{}").get("name") or "Dye"
    except ValueError:
        wanted = "Dye"
    add(OK if re.search(r'"workbench\.colorTheme"\s*:\s*' + re.escape(json.dumps(wanted)), vs)
        or not util.have("code") else WARN, "VS Code theme", f'workbench.colorTheme = "{wanted}"')

    # browser / launcher
    zen = list(web.zen_profiles(paths))
    add(OK if all((p / "chrome/userChrome.css").is_file() for p in zen) else WARN, "Zen userChrome",
        f"{len(zen)} profile(s); restart Zen to apply")
    vic = _read(cfg / "vicinae/settings.json")
    add(OK if '"dye"' in vic or not util.have("vicinae") else WARN, "vicinae theme", "")
    scripts = paths.data / "vicinae/scripts"
    add(OK if (scripts / "dye-theme-picker.sh").exists() or not util.have("vicinae") else WARN,
        "vicinae script commands", "install.sh links dye/vicinae/*.sh")

    # last switch
    log = _read(paths.log)
    failed = [l for l in log.splitlines() if " failed" in l]
    add(OK if not failed else WARN, "last switch", failed[-1] if failed else "no failures logged")
    return out


def report(paths, as_json=False):
    rows = checks(paths)
    if as_json:
        return json.dumps([{"status": s, "check": l, "detail": d} for s, l, d in rows], indent=1), rows
    mark = {OK: "\x1b[32m✓\x1b[0m", WARN: "\x1b[33m!\x1b[0m", FAIL: "\x1b[31m✗\x1b[0m"}
    lines = [f" {mark[s]} {l}" + (f"  \x1b[2m{d}\x1b[0m" if d and s != OK else "") for s, l, d in rows]
    return "\n".join(lines), rows
