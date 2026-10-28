"""Claude Code and T3 Code.

Each gets one theme file whose name never changes (dye) and whose contents do.
Both watch their theme folders and retint running sessions.
"""
import os
from pathlib import Path

from .. import util


def claude_dirs(paths):
    """Every Claude Code config folder: ~/.claude, extra accounts in ~/.claude-*,
    and $CLAUDE_CONFIG_DIR."""
    dirs = [paths.home / ".claude", *sorted(paths.home.glob(".claude-*"))]
    if os.environ.get("CLAUDE_CONFIG_DIR") and not util.SANDBOX:
        dirs.append(Path(os.environ["CLAUDE_CONFIG_DIR"]))
    seen, out = set(), []
    for d in dirs:
        if d.is_dir() and ((d / "settings.json").exists() or (d / ".claude.json").exists()):
            key = d.resolve()
            if key not in seen:
                seen.add(key)
                out.append(d)
    return out


def claude(ctx):
    """Claude watches its themes folder, so running sessions retint live."""
    src = ctx.file("claude.json")
    if not src:
        return
    problems = []
    for home in claude_dirs(ctx.paths):
        util.install_file(src, home / "themes" / "dye.json")
        settings = home / "settings.json"
        if settings.is_file():
            text = settings.read_text()
            try:
                new = util.json_set(text, "theme", "custom:dye")
            except util.ConfigEditError as e:
                problems.append(f"{settings}: {e}")
                continue
            if new != text:
                util.atomic_write(settings, new)
    if problems:
        raise RuntimeError("; ".join(problems))


def t3_userdata(paths):
    return Path(os.environ.get("T3CODE_HOME") or paths.home / ".t3") / "userdata"


def t3code(ctx):
    src = ctx.file("t3code.json")
    userdata = t3_userdata(ctx.paths)
    if not src or not userdata.is_dir():
        return
    if "{{" in src.read_text():
        raise RuntimeError("t3code.json has unresolved colours; kept the previous theme")
    util.install_file(src, userdata / "themes" / "dye.json")
    # `t3 theme set dye` writes the same key: connected clients switch to it.
    settings = userdata / "settings.json"
    text = settings.read_text() if settings.is_file() else ""
    new = util.json_set(text, "defaultTheme", "dye")
    if new != text:
        util.atomic_write(settings, new)
