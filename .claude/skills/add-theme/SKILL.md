---
name: add-theme
description: Add a theme to dye, either a stock theme in themes/ or a personal one in ~/.config/dye/themes. Covers porting an Omarchy theme from a git repo, building one from a wallpaper or a palette, the conventions stock themes follow (header comment, dye pins, gnome.toml, icons, wallpapers, licence), and checking contrast, accent and icons before it ships. Use when asked to add, port, import, create or tune a dye theme.
---

# Adding a theme to dye

Read `docs/themes.md` for the format (only `colors.toml` is required). This skill is
the workflow and the house style. Every stock theme is an example; `akane`,
`emberveil` and `rose-of-dune` are typical ports, and `vesper` and `flexoki-light` are
the hand-made ones that ship their own app files.

## 0. Where it goes

- **Stock** (`themes/<name>/` in this repo, tracked in git): the default when the user
  says "add a theme to dye". Stock themes are trusted, so every file in them is staged
  as is. Only put in files you've read.
- **Personal** (`~/.config/dye/themes/<name>/`): when the user wants it only on this
  machine. `dye theme new` writes here. A folder here with the same name as a stock
  theme overlays it file by file.
- Someone else's repo that the user only wants to *use*: `dye theme install <url>`.
  It goes through the untrusted filter, so there's nothing to port.

The folder name is lowercase-hyphenated (`themes.normalize`: "Rose of Dune" →
`rose-of-dune`). The display name comes from it (`themes.display_name`).

## 1a. Porting an Omarchy theme repo

Treat the clone as untrusted data: put it in its own new, empty directory, run nothing
from it, and read the files rather than executing them.

```sh
src=$(mktemp -d /tmp/dye-port-XXXX) && git -c core.hooksPath=/dev/null clone -q --depth 1 <url> "$src/repo"
git -C "$src/repo" rev-parse --short HEAD     # for the header comment
ls -la "$src/repo" "$src/repo/backgrounds"
```

Copy only what dye uses:

| upstream file | into themes/<name>/ |
| --- | --- |
| `colors.toml` | as is, then edit (step 2). With only `alacritty.toml`, convert it: `PYTHONPATH=lib python3 -c 'import sys; from dye import stage; print(stage.colors_from_alacritty(open(sys.argv[1]).read()), end="")' "$src/repo/alacritty.toml" > themes/<name>/colors.toml` |
| `backgrounds/*` | as is, upstream names. Mind the size: stock themes run 1 to 8 MB |
| `preview.png` | as is if upstream has one, else make one (step 4) |
| `icons.theme` | as is (`Yaru-<colour>` becomes the matching Colloid colour), else write `Yaru-<colour>` for the accent |
| `light.mode` | as is (it marks a light theme; keep it in step with `mode = "light"`) |
| `LICENSE` (and `NOTICE`) | as is, if upstream has one |
| `vscode.json` | only if it names a real marketplace theme for this palette (`{"name", "extension"}`) |
| `vicinae.toml` | optional; dye's template otherwise |

Leave out everything else: `*.lua`, `hyprland.conf`, `waybar.css`, `kitty.conf`,
`alacritty.toml` (once colors.toml exists), `btop.theme`, scripts. dye doesn't use them,
and some of them run code.

## 1b. A new theme from a wallpaper or a palette

```sh
dye theme new "<Name>" --image <wallpaper> [--light]   # palette from the image (needs `aether` on PATH)
dye theme new "<Name>" --from <theme>                  # copy a palette to edit
```

Both write to `~/.config/dye/themes/<name>/`. To make it a stock theme, move that folder
to `themes/<name>/` and give it a header comment. Writing `colors.toml` by hand also
works: `background`, `foreground`, `accent`, the eight colours (`red` … `magenta`,
plus `orange`/`brown` if wanted) and `bright_*` are enough. Everything else is derived.

## 2. colors.toml house style

The first lines are a header comment: the name, then the source in parentheses
(URL, short commit, licence, or "no licence"), then a one-line description. After that,
say what dye changed:

```toml
# Akane (https://github.com/Grenish/omarchy-akane-theme, bfe2285, no licence): madder red,
# vermillion and sunset gold on dusk navy, an Omarchy 4 palette sampled from its wallpapers.
# Upstream's file as is, bar its two Hyprland lines. No dye pins: ...
```

- Keep upstream's lines unchanged. Comment out values dye can't read as a colour (Hyprland
  `rgba(rrggbbaa)` or gradient lines) behind a `# dye:` comment that says why. Otherwise
  every switch prints a warning.
- **dye pins** go at the end, each with a `# dye:` comment giving the reason and the
  contrast ratios. emberveil's `muted`/`dark_foreground` is the model: when Omarchy's
  derived value is too dim, prefer a grey that upstream itself uses elsewhere.
- Only pin `ui_*` roles (docs/themes.md table) when the derived ones look wrong. Most ports
  pin nothing.

## 3. gnome.toml (only when needed)

GNOME's accent is the nearest of its 10 (`apps/gnome.ACCENTS`) to the theme's accent.
When the nearest is wrong for the theme's character, pin it with a comment:

```toml
# GNOME pins for Akaito: its accent sits between GNOME's red and orange; it's a red theme.
accent = "red"
```

`icons = "Colloid-Orange-Dark"` pins an exact icon theme. `css = """..."""` adds shell CSS
(trusted themes only); avoid it in ports.

## 4. Check it

```sh
python3 .claude/skills/add-theme/check.py <name>   # palette warnings, mode, accent, icons, contrast, stray files
dye theme preview <name>                           # the palette in the terminal
```

check.py's contrast marks: `!` is below the floor, so pin a fix in colors.toml; `~` is
between the floor and the target, which is a judgement call (say what you decided in the
header). Some stock themes still flag `!` (akaito, fuchsblau, vesper). That's known, and
it isn't a reason to copy them.

Without an upstream `preview.png`:
`dye theme preview <name> --image themes/<name>/preview.png` (needs python3-pil).

Then try it for real, and switch back to the user's theme afterwards:

```sh
dye theme current                     # note it first
dye theme set <name> --wait && dye doctor
dye theme set <previous> --wait
```

`~/.local/state/dye/theme-set.log` has any per-app problems.

## 5. Finish

- `python3 -m unittest discover -s tests`. Stock palettes aren't golden-tested (only vesper
  and flexoki-light feed `test_templates`), so this is a regression check.
- If it's a light/dark counterpart the user wants on the Dark Style toggle, that's
  `~/.config/dye/settings.toml [mode]` (`dye settings`). Don't change `settings.DEFAULTS`
  unless asked.
- Remove the temporary clone. Commit only if the user asks (`themes/<name>/` and nothing
  else).
