"""The terminal: ghostty. zsh watches theme.generation itself and needs nothing here.

ghostty includes current/theme/ghostty.conf from its main config, so a reload
signal is all a switch needs.
"""
import signal

from .. import util


def ghostty(ctx):
    if not ctx.file("ghostty.conf"):
        return
    # SIGUSR2 makes every ghostty window re-read its config (ghostty >= 1.2).
    util.signal_all("ghostty", signal.SIGUSR2)
