"""dye _uninstall: take dye's edits back out of other apps' configs.

Only what dye itself did is undone: a theme key dye set goes back to its value in
install.sh's backup (or goes, if it wasn't there), a file dye added is deleted (or
the backed-up one put back), the include lines are removed. Anything changed since
the install is kept, so this is not the same as backup/restore.sh, which puts every
file back whole. uninstall.sh does the rest (the service, the extension, the links).
"""
import ast
import configparser
import json
import re
import shutil
import subprocess
import tarfile

from . import themes, util, wire
from .apps import agents, editors, web

GHOSTTY_INCLUDE = re.compile(r"^[ \t]*config-file[ \t]*=[ \t]*\??\S*dye/current/theme/ghostty\.conf[ \t]*$")
ZSH_START, ZSH_END = wire.ZSH.splitlines()[0], wire.ZSH.splitlines()[-1]  # the hook install.sh adds

# GNOME keys a switch writes (apps/gnome.py, activate.py), as dconf paths under /org/gnome/.
GNOME_KEYS = [("desktop/interface", k) for k in ("color-scheme", "accent-color", "icon-theme", "gtk-theme")]
GNOME_KEYS += [("desktop/background", "picture-uri"), ("desktop/background", "picture-uri-dark"),
               ("desktop/screensaver", "picture-uri"),
               ("shell/extensions/tiling-assistant", "focus-hint-color")]
SHELL_UUID = "dye-shell@dye"
USER_THEME = "user-theme@gnome-shell-extensions.gcampax.github.com"  # dye-shell switches it off


def _parse(text):
    """A JSON or JSONC object, or None."""
    try:
        data = json.loads(util._jsonc_strict(text))
    except (util.ConfigEditError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


class Undo:
    def __init__(self, paths, dry_run=False):
        self.paths, self.dry = paths, dry_run
        self.backup = paths.state_dir / "backup"
        self.problems = []
        self.old = {}  # real path -> its text before dye
        tgz = self.backup / "pre-dye.tar.gz"
        self.has_backup = tgz.is_file()
        if self.has_backup:
            with tarfile.open(tgz) as tar:
                for m in tar.getmembers():
                    if m.isfile():
                        self.old["/" + m.name.lstrip("/")] = tar.extractfile(m).read().decode(errors="replace")
        self.links = {}  # symlink -> target, for configs that pointed into a dotfiles repo
        try:
            for line in (self.backup / "pre-dye.links").read_text().splitlines():
                link, _, target = line.partition("\t")
                if link:
                    self.links[link] = target
        except OSError:
            pass

    # -- plumbing -------------------------------------------------------------------
    def say(self, msg):
        print(f"    {'would ' if self.dry else ''}{msg}")

    def old_text(self, f):
        return self.old.get(str(f.resolve()))

    def write(self, f, text, what):
        self.say(what)
        if not self.dry:
            util.atomic_write(f, text)  # through a symlink, as dye wrote it

    def remove(self, f):
        if not (f.exists() or f.is_symlink()):
            return
        self.say(f"remove {f}")
        if not self.dry:
            shutil.rmtree(f) if f.is_dir() and not f.is_symlink() else f.unlink()
            try:
                f.parent.rmdir()  # a themes/ or chrome/ folder dye made, if now empty
            except OSError:
                pass

    def put_back(self, f):
        """A file dye replaced whole (gtk.css, userChrome.css): the backed-up one, the
        symlink it was, or nothing if dye made it."""
        if str(f) in self.links:
            self.say(f"relink {f} -> {self.links[str(f)]}")
            if not self.dry:
                f.unlink(missing_ok=True)
                f.symlink_to(self.links[str(f)])
        elif self.old_text(f) is not None:
            if f.read_text() != self.old_text(f):
                self.write(f, self.old_text(f), f"restore {f}")
        else:
            self.remove(f)

    def owned(self, f):
        """A file every switch overwrites whole (a theme may ship its own, so the header
        needn't say dye). Without a backup, only one whose first line names dye."""
        if not f.is_file():
            return False
        if self.has_backup:
            return True
        try:
            return "dye" in f.read_text().split("\n", 1)[0]
        except OSError:
            return False

    def json_key(self, f, key, dye_values, jsonc=False):
        """Put key back to its pre-dye value, if it still holds one dye set."""
        if not f.is_file():
            return
        text = f.read_text()
        data = _parse(text)
        if data is None:
            self.problems.append(f"{f}: doesn't parse; {key} left as it is")
            return
        if data.get(key) not in dye_values:
            return
        old = _parse(self.old_text(f) or "") or {}
        if key in old and old[key] == data[key]:
            return  # a dye theme that names the theme you had
        try:
            if jsonc:
                new = util.jsonc_set(text, key, old[key]) if key in old else util.jsonc_unset(text, key)
            else:
                if key in old:
                    data[key] = old[key]
                else:
                    del data[key]
                new = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        except util.ConfigEditError as e:
            self.problems.append(f"{f}: {e}")
            return
        shown = json.dumps(old[key]) if key in old else "(unset)"
        self.write(f, new, f"set {key} = {shown} in {f}")

    # -- apps -----------------------------------------------------------------------
    def agents(self):
        for d in agents.claude_dirs(self.paths):
            self.json_key(d / "settings.json", "theme", {"custom:dye"})
            self.remove(d / "themes" / "dye.json")
        userdata = agents.t3_userdata(self.paths)
        self.json_key(userdata / "settings.json", "defaultTheme", {"dye"})
        self.remove(userdata / "themes" / "dye.json")

    def vscode(self):
        names = {"Dye"}  # the generated theme, and any marketplace theme a dye theme named
        for t in themes.all_themes(self.paths).values():
            for d in (t.user, t.base):
                data = _parse((d / "vscode.json").read_text()) if d and (d / "vscode.json").is_file() else None
                if data and isinstance(data.get("name"), str):
                    names.add(data["name"])
        settings = self.paths.config / "Code" / "User" / "settings.json"
        for key in ("workbench.colorTheme", "workbench.preferredDarkColorTheme",
                    "workbench.preferredLightColorTheme"):
            self.json_key(settings, key, names, jsonc=True)
        ext_dir = self.paths.home / ".vscode" / "extensions"
        self.remove(ext_dir / editors.EXT_NAME)
        registry = ext_dir / "extensions.json"
        try:
            entries = json.loads(registry.read_text())
        except (OSError, json.JSONDecodeError):
            return
        kept = [e for e in entries if e.get("identifier", {}).get("id") != editors.EXT_ID]
        if kept != entries:
            self.write(registry, json.dumps(kept), f"unregister {editors.EXT_ID} in {registry}")

    def vicinae(self):
        settings = self.paths.config / "vicinae" / "settings.json"
        if settings.is_file():
            text = new = settings.read_text()
            old = (_parse(self.old_text(settings) or "") or {}).get("theme") or {}
            for scheme in ("light", "dark"):
                name = (old.get(scheme) or {}).get("name") if isinstance(old.get(scheme), dict) else None
                if isinstance(name, str) and name != "dye":
                    new = re.sub(r'("' + scheme + r'"\s*:\s*\{[^{}]*?"name"\s*:\s*)"dye"',
                                 lambda m: m.group(1) + json.dumps(name), new)
            if new != text:
                self.write(settings, new, f"set vicinae's theme back in {settings}")
            elif '"dye"' in text:
                self.problems.append(f"{settings}: no pre-dye theme name in the backup; still says dye")
        self.remove(self.paths.data / "vicinae" / "themes" / "dye.toml")
        if not self.dry and not util.SANDBOX:
            subprocess.run(["systemctl", "--user", "try-restart", "vicinae.service"], capture_output=True, timeout=15)

    def ghostty(self):
        for f in (self.paths.config / "ghostty" / "config", self.paths.config / "ghostty" / "config.ghostty"):
            if f.is_file():
                self.drop_lines(f, lambda lines, i: GHOSTTY_INCLUDE.match(lines[i]) and 1, "the ghostty theme include")

    def zsh(self):
        def block(lines, i):
            if lines[i].rstrip("\n") != ZSH_START:
                return 0
            for j in range(i, min(i + 15, len(lines))):
                if ZSH_END in lines[j]:
                    return j - i + 1
            return 0
        f = self.paths.home / ".zshrc"
        if f.is_file():
            self.drop_lines(f, block, "dye's zsh hook")

    def drop_lines(self, f, match, what):
        """Remove the lines match(lines, i) counts, with a "# dye" comment and a blank
        line just above them."""
        lines, out, i, hit = f.read_text().splitlines(keepends=True), [], 0, False
        while i < len(lines):
            n = match(lines, i)
            if not n:
                out.append(lines[i])
                i += 1
                continue
            commented = lines[i].startswith("# dye")
            hit, i = True, i + n
            if out and out[-1].startswith("# dye"):
                out.pop()
                commented = True
            if commented and out and not out[-1].strip():
                out.pop()
        if hit:
            self.write(f, "".join(out), f"remove {what} from {f}")

    def gtk(self):
        for f in (self.paths.config / "gtk-4.0" / "gtk.css", self.paths.config / "gtk-3.0" / "gtk.css"):
            if self.owned(f):
                self.put_back(f)
        dark = self.paths.config / "gtk-4.0" / "gtk-dark.css"
        if dark.is_symlink() and str(dark) not in self.links and dark.readlink().name == "gtk.css":
            self.remove(dark)

    def zen(self):
        for profile in web.zen_profiles(self.paths):
            for name in ("userChrome.css", "userContent.css"):
                if self.owned(profile / "chrome" / name):
                    self.put_back(profile / "chrome" / name)
            user_js = profile / "user.js"
            if not user_js.is_file():
                continue
            text, old = user_js.read_text(), self.old_text(user_js)
            before = [m.group(3) for m in web._PREF_LINE.finditer(web._without_comments(old or ""))]
            if before:  # it was there already: back to the value it had
                spans = list(web._PREF_LINE.finditer(web._without_comments(text)))
                new = text
                for m in reversed(spans):
                    a, b = m.span(3)
                    new = new[:a] + before[-1] + new[b:]
            else:  # dye added the line
                line = f'user_pref("{web.STYLESHEETS_PREF}", true);\n'
                new = text.replace(line, "")
            if new != text:
                if not new.strip() and old is None:
                    self.remove(user_js)
                else:
                    self.write(user_js, new, f"put {web.STYLESHEETS_PREF} back in {user_js}")

    def gnome(self):
        """dye-shell off, and the keys a switch writes back to their pre-dye values."""
        if util.SANDBOX:
            return  # dconf isn't sandboxed: never touch the real desktop from a test
        enabled = ast.literal_eval((util.gget("org.gnome.shell", "enabled-extensions") or "[]").replace("@as ", ""))
        dump = configparser.ConfigParser(interpolation=None, strict=False)
        dump.optionxform = str
        try:
            dump.read(self.backup / "pre-dye.dconf")
        except configparser.Error as e:
            self.problems.append(f"pre-dye.dconf: {e}")
        if not dump.sections():
            self.problems.append("no pre-dye GNOME settings in the backup; colours and wallpaper left as they are")
            return
        was = ast.literal_eval(dump.get("shell", "enabled-extensions", fallback="[]").replace("@as ", ""))
        new = [u for u in enabled if u != SHELL_UUID]
        if USER_THEME in was and USER_THEME not in new:
            new.append(USER_THEME)
        if new != enabled:
            self.say(f"set enabled-extensions to {new}")
            if not self.dry:
                util.run(["gsettings", "set", "org.gnome.shell", "enabled-extensions", str(new)])
        for section, key in GNOME_KEYS:
            path = f"/org/gnome/{section}/{key}"
            old = dump.get(section, key, fallback=None)
            now = util.run(["dconf", "read", path], check=False).stdout.strip()
            if old == now or (old is None and not now):
                continue
            self.say(f"set {path} = {old}" if old is not None else f"reset {path}")
            if not self.dry:
                util.run(["dconf", "write", path, old] if old is not None else ["dconf", "reset", path])
        self.say("reset /org/gnome/shell/extensions/dye-shell/")
        if not self.dry:
            util.run(["dconf", "reset", "-f", "/org/gnome/shell/extensions/dye-shell/"], check=False)

    def run(self):
        if not self.old and not self.links:
            print("    (no pre-dye backup found: keys dye set are removed, not restored)")
        for step in (self.gnome, self.agents, self.vscode, self.vicinae, self.ghostty, self.zsh,
                     self.gtk, self.zen):
            try:
                step()
            except Exception as e:  # one app's trouble shouldn't stop the rest
                self.problems.append(f"{step.__name__}: {e}")
        for p in self.problems:
            print(f"  ! {p}")
        return 1 if self.problems else 0
