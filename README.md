# dye

One command recolours the whole desktop, Omarchy style. Pick a theme from a carousel
(<kbd>Super</kbd>+<kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>Space</kbd>). GNOME Shell,
GTK, the wallpaper, the terminal, the editor, the browser, coding agents and the launcher
all switch together under one cross-fade. Themes use [Omarchy's format](docs/themes.md),
so every Omarchy theme works as is: the stock ones (`dye theme import-omarchy`) and the
community ones (`dye theme install <git url>`).

```sh
./install.sh            # once; then log out and back in
dye theme set tokyo-night
```

## Using it

| | |
| --- | --- |
| <kbd>Super</kbd>+<kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>Space</kbd> | theme carousel: ←/→, type to filter, Enter apply, Del remove, Esc close |
| <kbd>Super</kbd>+<kbd>Ctrl</kbd>+<kbd>Space</kbd> | background carousel for the current theme |
| Quick Settings → Dark Style | switches to the current theme's light/dark pair |
| vicinae | "Pick Theme", "Next Theme", "Set Theme", "Next Background", "Install Theme", "Dye Doctor", … |

```text
dye theme list | current | set <name> | next | prev | picker | refresh
dye theme install <git url> | remove <name> | update | import-omarchy [--all|--list]
dye theme new <name> [--from <theme>] [--image <wallpaper> [--light]] [--edit]
dye theme preview [<name>] [--json | --image FILE]
dye bg next | prev | set <file> | picker | open | list
dye mode toggle | dark | light | status
dye apply <app>...      re-apply one app (e.g. dye apply ghostty vscode)
dye doctor              is every app wired up?
dye settings            create ~/.config/dye/settings.toml (commented defaults), print its path
```

`dye theme set` returns as soon as what's on screen has switched (the shell,
wallpaper, ghostty; about 0.1 s). The rest (VS Code, Zen, Claude Code, T3 Code,
GTK, vicinae) finishes in the background. `--wait` (or a terminal) waits for all of
it. Problems go to `~/.local/state/dye/theme-set.log` and a notification.

`dye theme new` with `--image` gets its palette from the wallpaper via
[Aether](https://github.com/bjarneo/aether) (`aether` on your PATH); without Aether,
or with `--from`, it copies an existing theme's palette for you to edit.

## What follows the theme

| App | How |
| --- | --- |
| GNOME Shell | the `dye-shell` extension loads the theme's shell stylesheet (a recoloured Yaru plus the bar) and sets the colour scheme, accent and wallpaper in one go |
| GTK 4 / libadwaita | `~/.config/gtk-4.0/gtk.css`, both of the pair's palettes in `prefers-color-scheme` blocks, so open apps follow Dark Style live |
| GTK 3, icons | `~/.config/gtk-3.0/gtk.css`; Colloid icons in the theme's accent colour |
| ghostty | `config-file = ?~/.local/state/dye/current/theme/ghostty.conf` in its config, reloaded with SIGUSR2 |
| zsh | zsh-syntax-highlighting colours, re-sourced before the next prompt (see below) |
| VS Code | the theme's `vscode.json` extension, or a generated "Dye" theme |
| Claude Code, T3 Code | generated themes, set in each one's settings (every `~/.claude*` account) |
| Zen | `userChrome.css`/`userContent.css` in every profile, native or flatpak |
| vicinae | a generated theme file |
| tiling-assistant | the focus hint in the accent colour |

zsh needs this in `~/.zshrc`, after oh-my-zsh loads `zsh-syntax-highlighting`:

```zsh
# dye: syntax-highlighting colours follow the theme
_dye_zsh() {
  local f=~/.local/state/dye/current/theme.generation g
  [[ -r $f ]] && g=$(<$f) || return 0
  [[ $g == ${_dye_gen-} ]] && return 0
  _dye_gen=$g
  source ~/.local/state/dye/current/theme/zsh-highlight.zsh 2>/dev/null
}
autoload -Uz add-zsh-hook && add-zsh-hook precmd _dye_zsh
```

Other apps (kitty, tmux, btop, Neovim, Cursor, Obsidian, Codex, Vencord, Chromium,
lazygit, gitui, yazi, the desktop widgets, other window-border extensions) were
dropped because they aren't installed here; rice, the project dye came from, has them.
Omarchy themes still carry files for them, which dye stages and ignores.

`~/.config/dye/settings.toml` (`dye settings` creates it) turns apps off and picks the
light/dark pair and the icon style.

## Layout

```text
bin/dye             the command          lib/dye/         the engine (stdlib Python)
extension/          dye-shell@riz1       templates/       *.tpl for themes that lack a file
themes/             stock themes         systemd/         dye-mode-watch.service
vicinae/            script commands      tests/           python3 -m unittest discover -s tests
```

At run time: your themes in `~/.config/dye/themes`, Omarchy imports in
`~/.local/share/dye/themes`, the applied theme in `~/.local/state/dye/current`, your
own templates in `~/.config/dye/themed/*.tpl` (they win over the stock ones), and
hooks in `~/.config/dye/hooks/theme-set*` (run with the theme name after every switch).

## Safety

Themes installed with git are treated as untrusted. Nothing in them that runs code
(scripts, `*.lua`, executables, app configs that can run commands), no shell CSS
(`gnome-shell.css`, `dye-bar.css`, `gnome.toml`'s `css`) and no symlink is ever
staged; dye generates those files from the palette instead and tells you what it
left out. Palette values from any theme must be colours, so nothing else can reach
the configs they're written into. Git runs without hooks, prompts or `ext::`
transports, and URLs that git would read as options are refused.

Each switch builds a new folder in `~/.local/state/dye/current/generations` and then
points the `current/theme` symlink at it, so apps only ever see a whole theme.
Switches queue behind a lock, and edits to other apps' settings keep everything else
in the file; a settings file dye can't parse is left alone and named in the log.

Before the first switch, `install.sh` backs up every config dye edits (found the
way the retints find them) and a `dconf dump` of `/org/gnome/` to
`~/.local/state/dye/backup`, readable only by you. `restore.sh` there puts the files
back, re-creating any that were symlinks into a dotfiles repo.

## Credits

The theme format, palette rules, template syntax and several templates come from
[Omarchy](https://github.com/basecamp/omarchy) (MIT, see `templates/LICENSE.omarchy`).

## Coming from rice

dye is rice renamed. `install.sh` retires rice when it finds it: it stops
`rice-mode-watch.service`, unlinks rice's vicinae commands and points ghostty's
include at `~/.local/state/dye/`. At the next login dye-shell switches `rice-shell@riz1`
off. `~/.local/bin/rice` and rice's backup (`~/.local/state/rice/backup`, your configs
from before rice) stay where they are.
