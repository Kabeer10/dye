# Architecture

dye is a stdlib-only Python engine (`lib/dye`), a GNOME Shell extension
(`extension/dye-shell@dye`), a systemd user service and a few shell scripts. One
`dye theme set <name>` stages a theme, renders every app's config from its palette,
swaps a symlink, and retints the apps.

## The pieces

```text
bin/dye                      entry point: puts lib/ on sys.path, calls dye.cli.main
lib/dye/cli.py               argparse tree; every subcommand is a small fn(args)
lib/dye/activate.py          a switch, end to end (below); generations; locking; hooks
lib/dye/themes.py            Theme dataclass, finding themes (stock / omarchy / user)
lib/dye/stage.py             copying a theme into a generation; the untrusted-file filter
lib/dye/palette.py           colors.toml parsing + Omarchy's colour cascade + dye's ui_* roles
lib/dye/render.py            {{ key }} / {{ mix a b 30% }} template renderer (Omarchy-exact)
lib/dye/colormath.py         hex, mix, WCAG contrast, OKLab/OKLCH
lib/dye/shellcss.py          the GNOME Shell stylesheet: Yaru recoloured onto the palette
lib/dye/backgrounds.py       which wallpaper a theme gets; remembered per theme
lib/dye/previews.py          picker thumbnails (cached), terminal ramp, preview.png
lib/dye/library.py           theme install/remove/update (git), import-omarchy, `theme new`
lib/dye/modewatch.py         dye-mode-watch.service: Dark Style toggle → paired theme
lib/dye/settings.py          ~/.config/dye/settings.toml over DEFAULTS
lib/dye/paths.py             every path, from $HOME + XDG (tests sandbox by env alone)
lib/dye/util.py              atomic writes, gsettings/dconf (sandbox-guarded), JSON/JSONC edits
lib/dye/doctor.py            `dye doctor` checks
lib/dye/backup.py            files install.sh backs up (same lookups as the retints)
lib/dye/wire.py              `dye _wire`: the ghostty include and zsh hook install.sh adds
lib/dye/uninstall.py         `dye _uninstall`: undo dye's edits only
lib/dye/apps/                one retint function per app (see apps.md)
templates/*.tpl              per-app config templates, rendered when a theme lacks the file
themes/<name>/               stock themes (see themes.md)
extension/dye-shell@dye/     the shell side (see shell-extension.md)
systemd/                     dye-mode-watch.service
vicinae/                     vicinae script commands (thin wrappers around `dye ...`)
install.sh, uninstall.sh     see install.md
```

## A switch (`activate.set_theme`)

1. **Lock** (`$XDG_RUNTIME_DIR/dye-theme-set.lock`, flock, never follows symlinks), so
   quick switches queue. A mode-watch flag file is raised before the new theme is visible.
2. **Stage** a new generation `~/.local/state/dye/current/generations/<id>/`:
   stock/imported folder first, then `~/.config/dye/themes/<name>` on top (file by file).
   Git-installed themes go through `stage.copy_untrusted` (no scripts, no symlinks, no
   code-running configs; see `stage.DENIED_NAMES` / `COLOUR_ONLY`).
3. **Build** (`activate.build`): `palette.load` → `render_theme` (every `templates/*.tpl`
   whose output the theme doesn't ship; `~/.config/dye/themed/*.tpl` win) →
   `make_dual` (gtk4/Zen CSS get both pair palettes in `prefers-color-scheme` blocks) →
   wallpaper choice → `gnome.json` (accent, icons, colour scheme, stylesheet path) →
   `gnome-shell.css` (`shellcss.build`, or a trusted theme's own + `dye-bar.css`) →
   `colors.json` (the resolved palette).
4. **Publish**: atomically repoint `current/theme` → `generations/<id>`, write
   `theme.name` and `theme.generation`. Apps only ever see a whole theme.
5. **VISIBLE group** in parallel inside a shell cross-fade (`shell`, `ghostty`); wait.
6. **Unlock**, prune old generations (newest 3 kept, pinned ones survive).
7. **OTHER group** (`gnome`, `gtk`, `claude`, `t3code`, `vscode`, `zen`, `vicinae`):
   detached process (`dye _retint <generation>`) unless `--wait`, a TTY, or
   `DYE_THEME_WAIT=1`. A batch whose theme was replaced meanwhile stops.
8. **Hooks** `~/.config/dye/hooks/theme-set*` run with the theme name; failures go to
   `~/.local/state/dye/theme-set.log` and a notification.

`dye theme refresh` rebuilds the current theme; `dye apply <app>...` re-runs retints.

## State on disk

```text
~/.config/dye/settings.toml          user settings (dye settings)
~/.config/dye/themes/<name>/         user themes and git installs (overlay stock by name)
~/.config/dye/themed/*.tpl           user templates (win over templates/)
~/.config/dye/hooks/theme-set*       post-switch hooks
~/.local/share/dye/themes/           Omarchy imports (import-omarchy)
~/.local/state/dye/current/theme     → generations/<id>   (what every app config points at)
~/.local/state/dye/current/theme.name, theme.generation, background
~/.local/state/dye/mode-pairs.json   last dark/light pick (Dark Style toggle pair)
~/.local/state/dye/theme-backgrounds remembered wallpaper per theme
~/.local/state/dye/theme-set.log     last switch's problems
~/.local/state/dye/backup/           install.sh's pre-dye backup (+ restore.sh)
~/.cache/dye/                        previews, shell CSS cache, colloid-src
```

## Trust model

- Stock themes and your own (no `.git`) are **trusted**: every file is staged as is,
  including `gnome-shell.css`, `dye-bar.css`, `gnome.toml`'s `css`.
- A theme folder with `.git` (from `dye theme install`) is **untrusted**: anything that
  runs code or styles a privileged UI is dropped and regenerated from templates; palette
  values must parse as colours (`palette.colour_value`), so nothing else reaches a config.
- Adding a template output means classifying it in `stage.py` (denied or COLOUR_ONLY);
  `tests/test_stage.py::test_every_template_output_is_classified` enforces it.

## Light/dark pairs

`settings.toml [mode]` names the default dark/light themes; each manual pick is remembered
per mode in `mode-pairs.json`. `modewatch.py` watches `color-scheme`; when it no longer
matches the current theme's mode, someone flipped Dark Style, so it switches to the pair.
