# Install, backup, uninstall

## install.sh (safe to re-run)

1. **Backup**, first run only: every file a retint edits in place (`dye _backup-targets`
   = `backup.targets`, by real path; symlinks recorded in `pre-dye.links`) into
   `~/.local/state/dye/backup/pre-dye.tar.gz`, plus `dconf dump /org/gnome/` →
   `pre-dye.dconf`, and a generated `restore.sh`. Mode 700/600.
2. Link `~/.local/bin/dye` → `bin/dye`.
3. Link the extension, compile its schemas, add `dye-shell@dye` to `enabled-extensions`
   (loads at next login).
4. Link and enable `dye-mode-watch.service`.
5. First theme, only if none is set (`DYE_FIRST_THEME`, else vesper / flexoki-light by
   the current Dark Style).
6. `dye _wire` (`wire.py`): the ghostty include
   `config-file = ?~/.local/state/dye/current/theme/ghostty.conf` (in `config.ghostty` or
   `config`, or a new `config.ghostty` if ghostty is installed) and the zsh hook from the
   README at the end of `~/.zshrc` (if there is one), each only if missing. Then vicinae
   script links; Colloid icons in every accent (cloned to `~/.cache/dye/colloid-src`) if
   missing; `dye doctor`.

Re-running doesn't retake the backup, change the theme or add the lines twice.

## uninstall.sh

`--dry-run` lists, `--purge` also removes `~/.config/dye`, `~/.local/share/dye` and the
backup, `-y` skips the prompt.

1. Stop/disable mode-watch first (restoring `color-scheme` would otherwise trigger a switch).
2. `dye _uninstall` (`uninstall.Undo`): undo dye's edits only, using the backup for old
   values: theme keys restored or removed, files dye added deleted (or the backed-up one
   put back), ghostty include and zsh hook removed, GNOME keys from `pre-dye.dconf`,
   `dye-shell@dye` off (`user-theme` back on if it was). Changes made since install stay.
3. Remove links pointing into the checkout; delete state (except `backup/`) and cache.

`backup/restore.sh` is the blunt alternative: every backed-up file back whole.

## doctor

`dye doctor [--json]` (`doctor.py`): theme and generated files, extension enabled and
answering `org.dye.Dye.Ping`, conflicting extensions, service, icons, Yaru base, ghostty
include, zsh hook, each app's setting, last switch's log.
