# dye-shell (GNOME Shell extension)

UUID `dye-shell@dye`, symlinked by install.sh into
`~/.local/share/gnome-shell/extensions/`. GNOME (Wayland) only loads a new or changed
extension at login, so JS changes need a log out and back in. `metadata.json` declares
`shell-version: ["50"]`.

| file | what |
| --- | --- |
| `extension.js` | enable/disable; switches off superseded extensions (`user-theme`); session-mode handling (lock screen keeps the stylesheet; bar, keybindings and pickers only in the user session) |
| `theme.js` | `ThemeManager`: D-Bus service, stylesheet swap (`Main.setThemeStylesheet`), colour scheme/accent/wallpaper, cross-fade |
| `picker.js` | full-screen theme and background carousels |
| `bar.js` | the top bar: floating islands + centre capsule (notifications, meetings, a new track for 4 s or on hover, clock with a now-playing badge); `bar-size` toggles the `dye-compact` class |
| `calendar_helper.py` | meeting lookup for the capsule |
| `stylesheet.css` | bar/picker layout (colours come from the theme's `dye-bar.css`) |
| `schemas/` | `org.gnome.shell.extensions.dye-shell`: `theme-picker`, `background-picker` (keybindings), `dye-command` (path to `dye`; empty = PATH / `~/.local/bin`), `bar-size` (`normal` / `compact`, set by `dye bar`) |

## D-Bus

Name/interface `org.dye.Dye`, object `/org/dye/Dye`, exported on the shell's session
connection (so the bus name is `org.gnome.Shell`). The engine calls it from
`lib/dye/apps/gnome.py` (`DBUS_PATH`, `DBUS_IFACE`, `dbus_call`).

| method | |
| --- | --- |
| `Ping() → s` | version; `dye doctor`'s liveness check |
| `ApplyTheme(s generation) → b` | re-read `current/theme` (gnome.json, gnome-shell.css) and apply stylesheet, scheme, accent, wallpaper |
| `BeginTransition()` / `EndTransition()` | the screen cross-fade around a switch |
| `OpenThemePicker()` / `OpenBackgroundPicker()` | the carousels |
| `SetBackground(s path)` | wallpaper only |
| `ReloadPalette()` | same apply as `ApplyTheme`, without a new generation |
| signal `ThemeApplied(s name)` | |

With `DYE_SHELL_DEBUG=1` in the shell's environment it also exports
`org.dye.Dye.Debug` (screenshot, drive the picker) for tests.

Without the extension (not logged in again yet, or disabled), `gnome.shell` falls back
to gsettings: colour scheme, accent and wallpaper still change; the shell stylesheet
doesn't.
