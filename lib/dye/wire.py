"""dye _wire: the lines ghostty and zsh need so that they load dye's theme (install.sh).

dye doesn't rewrite these two apps' configs on a switch. Instead each config loads a
file under current/theme once: ghostty through a `config-file` include, zsh through
a precmd hook that re-sources the highlight colours when the generation changes.
install.sh adds them once, only for an app that's in use, and never twice (the test
is doctor's). uninstall.py takes both back out; they start with "# dye" so it can
drop the comment too.
"""
import shutil
import signal

from . import util

GHOSTTY = "# dye: colours follow the theme\nconfig-file = ?~/.local/state/dye/current/theme/ghostty.conf\n"
ZSH = """# dye: syntax-highlighting colours follow the theme
_dye_zsh() {
  local f=~/.local/state/dye/current/theme.generation g
  [[ -r $f ]] && g=$(<$f) || return 0
  [[ $g == ${_dye_gen-} ]] && return 0
  _dye_gen=$g
  source ~/.local/state/dye/current/theme/zsh-highlight.zsh 2>/dev/null
}
autoload -Uz add-zsh-hook && add-zsh-hook precmd _dye_zsh
"""


def ghostty_wired(text):
    return "dye/current/theme/ghostty.conf" in text


def zsh_wired(text):
    return "dye/current" in text and "zsh-highlight.zsh" in text


def ghostty_configs(paths):
    """Both names ghostty reads: config.ghostty (1.2 on), then the older config."""
    d = paths.config / "ghostty"
    return [d / "config.ghostty", d / "config"]


def _read(f):
    try:
        return f.read_text()
    except OSError:
        return ""


def _append(f, block):
    text = _read(f)
    if text and not text.endswith("\n"):
        text += "\n"
    util.atomic_write(f, text + ("\n" if text.strip() else "") + block)


def ghostty(paths):
    """Include the theme in ghostty's config. With no config yet, start config.ghostty,
    but only if ghostty is installed."""
    files = ghostty_configs(paths)
    if any(ghostty_wired(_read(f)) for f in files):
        return None
    f = next((f for f in files if f.is_file()), None)
    if f is None and not shutil.which("ghostty"):
        return None
    f = f or files[0]
    _append(f, GHOSTTY)
    util.signal_all("ghostty", signal.SIGUSR2)  # open windows pick it up now
    return f


def zsh(paths):
    """Add the hook to ~/.zshrc. At the end is fine: precmd runs after the whole file,
    so the highlighting plugin has loaded by then."""
    f = paths.home / ".zshrc"
    if not f.is_file() or zsh_wired(_read(f)):
        return None
    _append(f, ZSH)
    return f


def run(paths):
    for what, step in (("ghostty's theme include", ghostty), ("the zsh highlighting hook", zsh)):
        f = step(paths)
        if f:
            print(f"    added {what} to {f}")
    return 0
