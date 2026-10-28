#!/usr/bin/env bash
# Sets dye up on this machine. Safe to re-run.
#
#  1. backs up the configs dye manages (first run only)
#  2. links the dye command into ~/.local/bin
#  3. installs the dye-shell GNOME Shell extension (it loads at the next login)
#  4. installs dye's light/dark watcher
#  5. applies the first theme (first run only)
#  6. ghostty's theme include and the zsh hook (if missing), vicinae script commands,
#     Colloid icons in every accent
#
# DYE_FIRST_THEME=<name> picks the first theme; otherwise Vesper or Flexoki Light,
# following GNOME's current light/dark style.
set -euo pipefail
ROOT=$(dirname "$(realpath "$0")")
BIN=$HOME/.local/bin
DATA=${XDG_DATA_HOME:-$HOME/.local/share}
CONFIG=${XDG_CONFIG_HOME:-$HOME/.config}
STATE=${XDG_STATE_HOME:-$HOME/.local/state}
UUID=dye-shell@dye

step() { printf '\033[1m==> %s\033[0m\n' "$*"; }

python3 -c 'import tomllib' 2>/dev/null || { echo "dye needs Python 3.11+"; exit 1; }
python3 -c 'import PIL' 2>/dev/null ||
    echo "note: without python3-pil there are no picker thumbnails or previews (sudo apt install python3-pil)"

# ---- 1. backup ------------------------------------------------------------------------
# Every existing file a retint edits in place (`dye _backup-targets`: the lookups the
# retints themselves use), saved by its real path, so a config symlinked into a
# dotfiles repo is saved as the file it points at. restore.sh puts them back and
# re-creates the symlinks. Private: settings files can hold tokens.
backup=$STATE/dye/backup
mkdir -p "$backup"
chmod 700 "$backup"
if [[ ! -e $backup/pre-dye.tar.gz ]]; then
    step "Backing up the configs dye manages"
    (
        umask 077
        declare -A seen=()
        files=()
        : > "$backup/pre-dye.links"
        while IFS= read -r -d '' f; do
            real=$(realpath -e -- "$f") || continue
            [[ -n ${seen[$real]:-} ]] || { seen[$real]=1; files+=("$real"); }
            [[ -L $f ]] && printf '%s\t%s\n' "$f" "$(readlink -- "$f")" >> "$backup/pre-dye.links"
        done < <("$ROOT/bin/dye" _backup-targets)
        dconf dump /org/gnome/ > "$backup/pre-dye.dconf"
        printf '%s\0' "${files[@]}" | tar -czPf "$backup/pre-dye.tar.gz" --null -T -
        cat > "$backup/restore.sh" <<'RESTORE'
#!/usr/bin/env bash
# Puts back the configs dye edits, as they were before its first switch (saved by
# dye/install.sh). GNOME's own settings: see the last line.
set -euo pipefail
cd "$(dirname "$(realpath "$0")")"
tar -xzPf pre-dye.tar.gz                 # every file at its real path
while IFS=$'\t' read -r link target; do   # and the symlinks that pointed at them
    [[ -n $link ]] && ln -sfn -- "$target" "$link"
done < pre-dye.links
echo "Configs restored. GNOME settings too: dconf load /org/gnome/ < $PWD/pre-dye.dconf"
RESTORE
        echo "    $backup (restore.sh puts it all back)"
    )
fi
chmod 600 "$backup"/pre-dye.* 2>/dev/null || true
if [[ -e $backup/restore.sh ]]; then chmod 700 "$backup/restore.sh"; fi

# ---- 2. the command -------------------------------------------------------------------
step "Linking the dye command"
mkdir -p "$BIN"
ln -sfn "$ROOT/bin/dye" "$BIN/dye"

# ---- 3. the shell extension -------------------------------------------------------------
step "Installing the dye-shell extension"
mkdir -p "$DATA/gnome-shell/extensions"
ln -sfn "$ROOT/extension/$UUID" "$DATA/gnome-shell/extensions/$UUID"
glib-compile-schemas "$ROOT/extension/$UUID/schemas"
# Enabled now, loaded at the next login. dye-shell then switches off user-theme
# itself (they'd fight over the stylesheet); doing it here would reset the shell's
# look mid-session.
python3 - "$UUID" <<'EOF'
import ast, subprocess, sys
uuid = sys.argv[1]
get = lambda: ast.literal_eval(subprocess.run(["gsettings", "get", "org.gnome.shell", "enabled-extensions"],
                                              capture_output=True, text=True, check=True).stdout.replace("@as ", ""))
enabled = get()
new = list(enabled)
if uuid not in new:
    new.append(uuid)
if new != enabled:
    subprocess.run(["gsettings", "set", "org.gnome.shell", "enabled-extensions", str(new)], check=True)
EOF

# ---- 4. the light/dark watcher ----------------------------------------------------------
step "Installing dye mode-watch (follows the Dark Style toggle)"
mkdir -p "$CONFIG/systemd/user"
ln -sfn "$ROOT/systemd/dye-mode-watch.service" "$CONFIG/systemd/user/dye-mode-watch.service"
systemctl --user daemon-reload

# ---- 5. the first theme -----------------------------------------------------------------
if [[ ! -e $STATE/dye/current/theme.name ]]; then
    first=${DYE_FIRST_THEME:-}
    if [[ -z $first ]]; then
        [[ $(gsettings get org.gnome.desktop.interface color-scheme) == "'prefer-dark'" ]] &&
            first=vesper || first=flexoki-light
    fi
    step "Applying the first theme: $first"
    DYE_THEME_WAIT=1 "$BIN/dye" theme set "$first" || echo "    (some apps reported problems; see dye doctor)"
fi
systemctl --user enable --now dye-mode-watch.service

# ---- 6. the rest ------------------------------------------------------------------------
# ghostty and zsh load the theme from current/theme; each needs a line in its config.
step "Wiring ghostty and zsh to the theme"
"$BIN/dye" _wire

if command -v vicinae >/dev/null; then
    step "Linking the vicinae script commands"
    mkdir -p "$DATA/vicinae/scripts"
    for f in "$ROOT"/vicinae/*.sh; do
        ln -sfn "$f" "$DATA/vicinae/scripts/$(basename "$f")"
    done
fi

if [[ ! -d $DATA/icons/Colloid-Teal-Dark ]]; then
    step "Installing the Colloid icons in every accent colour"
    src=${XDG_CACHE_HOME:-$HOME/.cache}/dye/colloid-src
    [[ -d $src/.git ]] || git clone -q --depth 1 https://github.com/vinceliuice/Colloid-icon-theme "$src"
    (cd "$src" && ./install.sh -t all >/dev/null)
fi

step "Checking"
"$BIN/dye" doctor || true
echo
echo "Log out and back in once: GNOME Shell loads the dye-shell extension at login."
echo "Then: Super+Ctrl+Shift+Space for themes, Super+Ctrl+Space for backgrounds."
