#!/usr/bin/env bash
# Takes dye off this machine: install.sh in reverse.
#
#  1. stops dye's light/dark watcher (before anything changes Dark Style)
#  2. undoes dye's edits to other apps (dye _uninstall): the theme keys it set go back
#     to their pre-dye values, files it added go, the ghostty and zsh includes come
#     out; GNOME's colours, icons and wallpaper go back and dye-shell is switched off.
#     Changes you made since installing are kept.
#  3. removes what install.sh linked: the command, the extension, the vicinae scripts
#  4. deletes dye's state and cache. The pre-dye backup stays (backup/restore.sh puts
#     every file back whole, as it was before dye).
#
#   --dry-run  list what would change, change nothing
#   --purge    also delete your own themes and settings (~/.config/dye,
#              ~/.local/share/dye) and the pre-dye backup
#   -y         don't ask first
#
# The Colloid icons stay: they're ordinary icon themes, and other things may use them.
set -euo pipefail
ROOT=$(dirname "$(realpath "$0")")
BIN=$HOME/.local/bin
DATA=${XDG_DATA_HOME:-$HOME/.local/share}
CONFIG=${XDG_CONFIG_HOME:-$HOME/.config}
STATE=${XDG_STATE_HOME:-$HOME/.local/state}
CACHE=${XDG_CACHE_HOME:-$HOME/.cache}
UUID=dye-shell@dye

dry= purge= yes=
for a in "$@"; do
    case $a in
        --dry-run) dry=1 ;;
        --purge) purge=1 ;;
        -y|--yes) yes=1 ;;
        *) echo "usage: uninstall.sh [--dry-run] [--purge] [-y]" >&2; exit 2 ;;
    esac
done

step() { printf '\033[1m==> %s\033[0m\n' "$*"; }
# Runs a command, or under --dry-run only says what it would do.
do_() { if [[ -n $dry ]]; then echo "    would: $*"; else "$@"; fi; }
# A link install.sh made: only removed if it still points into this checkout.
unlink_ours() {
    [[ -L $1 && $(readlink -- "$1") == "$ROOT"/* ]] || return 0
    do_ rm -f -- "$1"
}

if [[ -z $dry && -z $yes ]]; then
    echo "This takes dye off: GNOME, Claude Code, T3 Code, VS Code, vicinae, ghostty, zsh,"
    echo "GTK and Zen go back to how they were before dye.${purge:+ --purge: your own themes and the backup go too.}"
    read -rp "Uninstall dye? [y/N] " answer
    [[ $answer == [yY]* ]] || exit 1
fi

# ---- 1. the light/dark watcher ----------------------------------------------------------
# First: putting color-scheme back would otherwise make it switch themes again.
step "Stopping dye mode-watch"
do_ systemctl --user disable --now dye-mode-watch.service 2>/dev/null || true
unlink_ours "$CONFIG/systemd/user/dye-mode-watch.service"
do_ systemctl --user daemon-reload

# ---- 2. dye's edits ---------------------------------------------------------------------
step "Undoing dye's edits to other apps"
status=0
"$ROOT/bin/dye" _uninstall ${dry:+--dry-run} || status=$?

# ---- 3. the links -----------------------------------------------------------------------
step "Removing the command, the extension and the vicinae scripts"
unlink_ours "$BIN/dye"
unlink_ours "$DATA/gnome-shell/extensions/$UUID"
for f in "$DATA"/vicinae/scripts/*.sh; do
    unlink_ours "$f"
done

# ---- 4. state and cache -----------------------------------------------------------------
step "Deleting dye's state and cache"
if [[ -d $STATE/dye ]]; then
    while IFS= read -r -d '' f; do
        do_ rm -rf -- "$f"
    done < <(find "$STATE/dye" -mindepth 1 -maxdepth 1 ! -name backup -print0)
fi
[[ -e $CACHE/dye ]] && do_ rm -rf -- "$CACHE/dye"
if [[ -n $purge ]]; then
    for d in "$CONFIG/dye" "$DATA/dye" "$STATE/dye"; do
        [[ -e $d ]] && do_ rm -rf -- "$d"
    done
fi

echo
if [[ -n $dry ]]; then
    echo "Nothing changed (--dry-run)."
    exit $status
fi
(( status == 0 )) || echo "Some edits couldn't be undone (the ! lines above); fix those by hand."
if [[ -z $purge && -d $STATE/dye/backup ]]; then
    echo "The pre-dye backup stays in $STATE/dye/backup (delete it when you're happy)."
fi
[[ -d $CONFIG/dye ]] && [[ -z $purge ]] && echo "Your own themes and settings stay in $CONFIG/dye."
echo "Log out and back in to drop dye-shell from GNOME Shell completely; this checkout ($ROOT) can be deleted."
exit $status
