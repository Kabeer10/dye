# Apps (retints)

Each app is one function `fn(ctx)` in `lib/dye/apps/`, registered in
`apps/__init__.py` in either `VISIBLE` (on screen, waited for) or `OTHER` (background).
`ctx` is `apps.Context`: `paths`, `settings`, `name`, `display`, `colors` (resolved
palette), `mode`, `dir` (= `current/theme`), `generation`, `background`, `gnome`
(gnome.json). `ctx.file("x")` returns the generation's file or `None`. A retint raises
on failure; the engine logs and notifies. Every app can be turned off in
`settings.toml [apps]`.

| name | module.fn | group | reads from generation | writes |
| --- | --- | --- | --- | --- |
| shell | `gnome.shell` | VISIBLE | gnome.json, gnome-shell.css | D-Bus `ApplyTheme` to dye-shell; without it, gsettings colour scheme/accent/wallpaper |
| ghostty | `terminal.ghostty` | VISIBLE | ghostty.conf | nothing: SIGUSR2 to ghostty (config includes `current/theme/ghostty.conf`) |
| gnome | `gnome.extras` | OTHER | gnome.json | gsettings `icon-theme`, `gtk-theme`; dconf tiling-assistant `focus-hint-color` |
| gtk | `gnome.gtk` | OTHER | gtk4.css, gtk3.css | `~/.config/gtk-4.0/gtk.css` (+ `gtk-dark.css` → gtk.css), `~/.config/gtk-3.0/gtk.css` |
| claude | `agents.claude` | OTHER | claude.json | `<each ~/.claude*>/themes/dye.json`; `settings.json` `"theme": "custom:dye"` |
| t3code | `agents.t3code` | OTHER | t3code.json | `~/.t3/userdata/themes/dye.json`; `settings.json` `"defaultTheme": "dye"` |
| vscode | `editors.vscode` | OTHER | vscode.json or vscode-theme.json | marketplace install, or local extension `~/.vscode/extensions/dye-theme` + `extensions.json`; `workbench.colorTheme` (+ preferred{Dark,Light}) |
| zen | `web.zen` | OTHER | userChrome.css, userContent.css | `<profile>/chrome/*.css`; `user.js` stylesheet pref |
| vicinae | `desktop.vicinae` | OTHER | vicinae.toml | `~/.local/share/vicinae/themes/dye.toml`; settings theme name → `dye`; restarts vicinae |

zsh has no retint: a `~/.zshrc` hook re-sources `current/theme/zsh-highlight.zsh` when
`theme.generation` changes. install.sh adds it, and ghostty's include, with `dye _wire`
(`wire.py`).

## Editing other apps' files

- `util.atomic_write(path, text)` writes through symlinks (dotfiles repos) by default.
- `util.install_file(src, dst)` copies a generated file only when it changed.
- Strict JSON (Claude, T3): `util.json_set` (re-indents to 2 spaces, key order kept).
- JSONC (VS Code, vicinae): `util.jsonc_get` / `jsonc_set` / `jsonc_unset` keep comments,
  trailing commas and formatting. A file that doesn't parse is left alone and reported.
- gsettings/dconf only through `util.gset` / `util.dset`; they refuse to run in the test
  sandbox unless a private bus is named (`util.may_use_session_bus`).

## Adding an app

1. `templates/<file>.tpl` using palette keys (see themes.md), and classify `<file>` in
   `stage.py` (`DENIED_NAMES` if the app executes it or it styles privileged UI, else
   `COLOUR_ONLY`).
2. `apps/<module>.py`: `def app(ctx)`: return early if `ctx.file(...)` is missing or the
   app isn't installed; write with the util helpers above.
3. Register in `apps/__init__.py` (`VISIBLE` only if it's on screen and fast) and add a
   default in `settings.DEFAULTS["apps"]`.
4. Files edited in place go in `backup.targets` (install.sh backs them up) and need an
   undo in `uninstall.py`; add a `doctor.py` check.
5. Tests: `DYE_UPDATE_GOLDEN=1 python3 -m unittest tests.test_templates` to record the
   new golden output in `tests/fixtures/golden/`, then review it; an app test in
   `tests/test_apps.py`.
6. README "What changes when you switch" table.
