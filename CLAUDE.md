# dye

Omarchy-style desktop themes for GNOME. One `dye theme set <name>` restyles GNOME Shell,
GTK, the wallpaper, ghostty, zsh, VS Code, Zen, Claude Code, T3 Code and vicinae. Themes
use Omarchy's format. README.md is the user-facing overview.

## Where to look (read these before the code)

| topic | doc |
| --- | --- |
| modules, what a switch does step by step, state on disk, trust model | `docs/architecture.md` |
| each app's retint: what it reads and writes, and how to add an app | `docs/apps.md` |
| theme format: colors.toml keys, `ui_*` roles, gnome.toml, templates | `docs/themes.md` |
| the GNOME Shell extension and its D-Bus interface | `docs/shell-extension.md` |
| install.sh / uninstall.sh / backup / doctor | `docs/install.md` |
| adding or porting a theme | skill `add-theme` (`.claude/skills/add-theme/`) |

Each module in `lib/dye/` opens with a docstring that explains its part. Read that
before reading the code.

## Commands

```sh
python3 -m unittest discover -s tests             # all tests (~6 s), run from the repo root
python3 -m unittest tests.test_palette            # one file
DYE_UPDATE_GOLDEN=1 python3 -m unittest tests.test_templates   # accept template output changes, then review the diff
bin/dye doctor                                    # is every app wired up (real machine)
bin/dye theme set <name> --wait                   # a real switch: changes the user's desktop
./uninstall.sh --dry-run                          # what an uninstall would change
```

## Rules

- **Stdlib-only Python 3.11+** (`tomllib`). Pillow is optional (previews only). Don't add
  dependencies.
- **Tests never touch the real desktop.** Run `bin/dye` under `helpers.sandbox_env(home)`
  (HOME/XDG in a temp dir, `DYE_SANDBOX=1`, `GSETTINGS_BACKEND=memory`, no session bus).
  gsettings/dconf/gdbus go through `util.gset` / `util.dset` / `util._bus_guard`, which
  refuse in the sandbox. `dconf` itself ignores GSETTINGS_BACKEND, so any new dconf call
  needs the same guard or an `if util.SANDBOX` skip.
- **Ask before** `dye theme set`, `install.sh` or `uninstall.sh` on the real machine. They
  change the user's live desktop and configs.
- **Omarchy parity**: `palette.py` (the colour cascade) and `render.py` (the template
  renderer) are line-for-line ports so that themes render byte-identically to Omarchy.
  Don't "improve" them. dye's own additions are the `ui_*` keys and the `dye_*` template
  values.
- **Trust**: a theme folder with `.git` is untrusted. Every template output must be
  classified in `stage.py` (`DENIED_NAMES` or `COLOUR_ONLY`), and a test enforces it.
  Palette values must parse as colours.
- **Editing other apps' configs**: use `util.atomic_write` (writes through symlinks),
  `util.install_file`, `util.json_set` (strict JSON) and `util.jsonc_set`/`jsonc_unset`
  (VS Code/vicinae, which keeps comments). A file that won't parse is left alone and
  reported, never rewritten.
- **A new in-place edit of another app's file touches four places**: the retint, then
  `backup.targets` (install.sh backs it up), `uninstall.py` (the undo), and `doctor.py`.
- **Naming**: the extension UUID is `dye-shell@dye`, the D-Bus name `org.dye.Dye` at
  `/org/dye/Dye`, the gsettings schema `org.gnome.shell.extensions.dye-shell`, and every
  generated per-app theme is named `dye` (`custom:dye`, `dye.json`, `dye.toml`, the VS Code
  "Dye"). Keep new names in that pattern.
- **Style**: British spelling in prose and comments (colour, recolour). Comments say
  *why*, in short plain sentences, at the density of the surrounding code. Shell scripts
  are bash with `set -euo pipefail` and `step "..."` headings.

## Gotchas

- GNOME Shell (Wayland) only loads extension JS at login. Changes to
  `extension/dye-shell@dye/*.js` need a log out and back in. Until then `dye doctor` shows
  "dye-shell answering on D-Bus ✗", and switches fall back to gsettings.
- A switch's second app group (`OTHER`) runs detached unless `--wait`, a TTY, or
  `DYE_THEME_WAIT=1`. Its errors land in `~/.local/state/dye/theme-set.log`, not stdout.
- `current/theme` is a symlink to an immutable generation. Never write into it. Rebuild
  with `dye theme refresh`.
- `install.sh` is idempotent: the backup and the first theme only happen once.
  `tests/test_install.py` and `tests/test_uninstall.py` cut install.sh between its
  `# ---- N.` markers, so keep those headings when editing it.
- The interactive shell here is zsh: unquoted `$var` doesn't word-split. Use `xargs` or
  arrays in one-liners.
