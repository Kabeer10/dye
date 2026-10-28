"""install.sh's backup, run against a throwaway HOME, and its restore.sh."""
import os
import re
import stat
import subprocess
import unittest

import helpers

INSTALL = (helpers.ROOT / "install.sh").read_text()
BACKUP_BLOCK = INSTALL[INSTALL.index("# ---- 1. backup"):INSTALL.index("# ---- 2. the command")]


class Backup(unittest.TestCase):
    def setUp(self):
        self.root = helpers.tempdir(self)
        self.home = self.root / "home"
        self.env = helpers.sandbox_env(self.home)
        h = self.home
        dot = self.root / "dotfiles"
        (dot / "Code").mkdir(parents=True)
        (dot / "t3").mkdir()
        (dot / "Code" / "settings.json").write_text('{"editor.fontSize": 14}\n')
        (dot / "t3" / "settings.json").write_text('{"a": 1}\n')
        (h / ".config" / "Code" / "User").mkdir(parents=True)
        (h / ".config" / "Code" / "User" / "settings.json").symlink_to(dot / "Code" / "settings.json")
        (h / ".t3" / "userdata").mkdir(parents=True)
        (h / ".t3" / "userdata" / "settings.json").symlink_to(dot / "t3" / "settings.json")
        (h / ".claude").mkdir()
        (h / ".claude" / "settings.json").write_text('{"token": "secret"}\n')
        os.chmod(h / ".claude" / "settings.json", 0o600)
        # A Zen profile outside the profile root, as profiles.ini allows.
        elsewhere = self.root / "zen-profile"
        elsewhere.mkdir()
        (elsewhere / "user.js").write_text('user_pref("a", 1);\n')
        (h / ".zen").mkdir()
        (h / ".zen" / "profiles.ini").write_text(f"[Profile0]\nName=x\nIsRelative=0\nPath={elsewhere}\n")
        self.dot, self.elsewhere = dot, elsewhere

    def bash(self, script):
        env = dict(self.env, ROOT=str(helpers.ROOT), STATE=str(self.home / ".local/state"))
        prelude = 'set -euo pipefail\nstep() { echo "== $*"; }\ndconf() { echo "[dconf dump]"; }\n'
        r = subprocess.run(["bash", "-c", prelude + script], env=env, capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        return r.stdout

    def test_backup_and_restore(self):
        self.bash(BACKUP_BLOCK)
        backup = self.home / ".local/state/dye/backup"
        listing = subprocess.run(["tar", "-tzPf", str(backup / "pre-dye.tar.gz")],
                                 capture_output=True, text=True, check=True).stdout.split("\n")
        self.assertIn(str(self.dot / "Code" / "settings.json"), listing)      # the real file
        self.assertIn(str(self.elsewhere / "user.js"), listing)              # profiles.ini's path
        self.assertIn(str(self.home / ".claude" / "settings.json"), listing)
        links = (backup / "pre-dye.links").read_text()
        self.assertIn(f"{self.home}/.t3/userdata/settings.json\t{self.dot}/t3/settings.json", links)

        self.assertEqual(stat.S_IMODE(backup.stat().st_mode), 0o700)
        for f in ("pre-dye.tar.gz", "pre-dye.links", "pre-dye.dconf"):
            self.assertEqual(stat.S_IMODE((backup / f).stat().st_mode), 0o600, f)

        # A theme switch writes through one link and replaces the other with a file.
        (self.dot / "Code" / "settings.json").write_text('{"workbench.colorTheme": "Dye"}\n')
        t3 = self.home / ".t3" / "userdata" / "settings.json"
        t3.unlink()
        t3.write_text('{"defaultTheme": "dye"}\n')
        (self.elsewhere / "user.js").write_text("changed\n")

        out = subprocess.run([str(backup / "restore.sh")], env=self.env, capture_output=True, text=True,
                             timeout=60)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual((self.dot / "Code" / "settings.json").read_text(), '{"editor.fontSize": 14}\n')
        self.assertTrue(t3.is_symlink())
        self.assertEqual(t3.read_text(), '{"a": 1}\n')
        self.assertEqual((self.elsewhere / "user.js").read_text(), 'user_pref("a", 1);\n')

    def test_existing_backup_is_made_private(self):
        backup = self.home / ".local/state/dye/backup"
        backup.mkdir(parents=True)
        for f in ("pre-dye.tar.gz", "pre-dye.dconf"):
            (backup / f).write_text("old")
            os.chmod(backup / f, 0o664)
        os.chmod(backup, 0o775)
        self.bash(BACKUP_BLOCK)
        self.assertEqual(stat.S_IMODE(backup.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE((backup / "pre-dye.tar.gz").stat().st_mode), 0o600)
        self.assertEqual((backup / "pre-dye.tar.gz").read_text(), "old")  # never overwritten

    def test_targets_follow_the_retints(self):
        names = self.bash(f'"{helpers.ROOT}/bin/dye" _backup-targets | tr "\\0" "\\n"')
        self.assertIn(str(self.elsewhere / "user.js"), names)
        self.assertTrue(re.search(r"/dotfiles/Code/settings\.json$|/Code/User/settings\.json$", names, re.M))
        self.assertTrue(re.search(r"/\.t3/userdata/settings\.json$", names, re.M))


if __name__ == "__main__":
    unittest.main()
