"""uninstall: install.sh's backup, a switch, then dye _uninstall, in a throwaway HOME.
dye's edits come out; the user's own, before and after the install, stay."""
import json
import subprocess
import sys
import unittest

import helpers
from dye import util

DYE = [sys.executable, str(helpers.ROOT / "bin" / "dye")]
INSTALL = (helpers.ROOT / "install.sh").read_text()
BACKUP_BLOCK = INSTALL[INSTALL.index("# ---- 1. backup"):INSTALL.index("# ---- 2. the command")]

VSCODE = '{\n  // mine\n  "editor.fontSize": 14,\n  "workbench.colorTheme": "Default Dark+"\n}\n'
GHOSTTY = "font-size = 10\n"
ZSHRC = "plugins=(git zsh-syntax-highlighting)\nsource $ZSH/oh-my-zsh.sh\n"


class Uninstall(unittest.TestCase):
    def setUp(self):
        self.home = h = helpers.tempdir(self)
        self.env = helpers.sandbox_env(h)
        for d in (".claude", ".t3/userdata", ".config/Code/User", ".vscode/extensions", ".config/ghostty",
                  ".config/gtk-3.0"):
            (h / d).mkdir(parents=True)
        (h / ".claude/settings.json").write_text('{"theme": "dark"}\n')
        (h / ".t3/userdata/settings.json").write_text('{"a": 1}\n')
        (h / ".config/Code/User/settings.json").write_text(VSCODE)
        (h / ".vscode/extensions/extensions.json").write_text("[]")
        (h / ".config/ghostty/config.ghostty").write_text(GHOSTTY)
        (h / ".config/gtk-3.0/gtk.css").write_text("/* mine */\n")
        (h / ".zshrc").write_text(ZSHRC)

        env = dict(self.env, ROOT=str(helpers.ROOT), STATE=str(h / ".local/state"))
        prelude = 'set -euo pipefail\nstep() { :; }\ndconf() { :; }\n'
        r = subprocess.run(["bash", "-c", prelude + BACKUP_BLOCK], env=env, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.dye("theme", "set", "flexoki-light", "--wait")
        # The lines install.sh adds, and a change made after installing.
        self.dye("_wire")
        self.assertIn("dye/current", (h / ".zshrc").read_text())
        claude = json.loads((h / ".claude/settings.json").read_text())
        (h / ".claude/settings.json").write_text(json.dumps(dict(claude, model="later")))

    def dye(self, *args):
        r = subprocess.run([*DYE, *args], env=self.env, capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        return r.stdout

    def test_edits_come_out(self):
        h = self.home
        self.assertEqual(json.loads((h / ".claude/settings.json").read_text())["theme"], "custom:dye")
        self.assertIn("dye-theme", (h / ".vscode/extensions/extensions.json").read_text())

        dry = self.dye("_uninstall", "--dry-run")
        self.assertIn("would set theme", dry)
        self.assertTrue((h / ".claude/themes/dye.json").exists())  # nothing changed

        self.dye("_uninstall")
        self.assertEqual(json.loads((h / ".claude/settings.json").read_text()), {"theme": "dark", "model": "later"})
        self.assertFalse((h / ".claude/themes").exists())
        self.assertEqual(json.loads((h / ".t3/userdata/settings.json").read_text()), {"a": 1})
        self.assertFalse((h / ".t3/userdata/themes").exists())
        self.assertEqual((h / ".config/Code/User/settings.json").read_text(), VSCODE)
        self.assertEqual(json.loads((h / ".vscode/extensions/extensions.json").read_text()), [])
        self.assertFalse((h / ".vscode/extensions/dye-theme").exists())
        self.assertEqual((h / ".config/ghostty/config.ghostty").read_text(), GHOSTTY)
        self.assertEqual((h / ".zshrc").read_text(), ZSHRC)
        self.assertEqual((h / ".config/gtk-3.0/gtk.css").read_text(), "/* mine */\n")
        self.assertFalse((h / ".config/gtk-4.0/gtk.css").exists())
        self.assertFalse((h / ".config/gtk-4.0/gtk-dark.css").is_symlink())

        self.assertNotIn("would", self.dye("_uninstall", "--dry-run"))  # nothing left to do


class JsoncUnset(unittest.TestCase):
    def test_unset(self):
        u = util.jsonc_unset
        self.assertEqual(u('{\n  "a": 1,\n  "b": 2,\n  // c\n  "c": 3\n}\n', "b"),
                         '{\n  "a": 1,\n  // c\n  "c": 3\n}\n')
        self.assertEqual(u('{\n  "a": 1,\n  "b": 2\n}\n', "b"), '{\n  "a": 1\n}\n')
        self.assertEqual(u('{\n  "b": 2\n}\n', "b"), '{\n}\n')
        self.assertEqual(u('{"a":1,"b":2}', "a"), '{"b":2}')
        self.assertEqual(u('{"a": 1}', "x"), '{"a": 1}')


if __name__ == "__main__":
    unittest.main()
