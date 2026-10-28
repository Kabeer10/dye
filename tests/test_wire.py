"""dye _wire: install.sh's ghostty include and zsh hook, added once and only where they're used."""
import contextlib
import io
import unittest
from unittest import mock

import helpers
from dye import paths as paths_mod, wire


def sandbox(home):
    return paths_mod.Paths(home=home, config=home / ".config", data=home / ".local/share",
                           state=home / ".local/state", cache=home / ".cache", runtime=home / "run")


class Wire(unittest.TestCase):
    def setUp(self):
        self.home = helpers.tempdir(self)
        self.paths = sandbox(self.home)
        (self.home / ".config/ghostty").mkdir(parents=True)
        # In-process, so DYE_SANDBOX isn't set: keep the reload away from real ghostty windows.
        patcher = mock.patch.object(wire.util, "signal_all")
        self.signal = patcher.start()
        self.addCleanup(patcher.stop)

    def test_adds_both_once(self):
        g, z = self.home / ".config/ghostty/config.ghostty", self.home / ".zshrc"
        g.write_text("font-size = 10")  # no final newline
        z.write_text("source $ZSH/oh-my-zsh.sh\n")
        with contextlib.redirect_stdout(io.StringIO()):
            for _ in range(2):
                wire.run(self.paths)
        self.signal.assert_called_once()  # only when the include went in
        self.assertEqual(g.read_text(), "font-size = 10\n\n" + wire.GHOSTTY)
        self.assertEqual(z.read_text(), "source $ZSH/oh-my-zsh.sh\n\n" + wire.ZSH)
        self.assertTrue(wire.ghostty_wired(g.read_text()) and wire.zsh_wired(z.read_text()))  # doctor's test

    def test_an_include_in_either_file_counts(self):
        old = self.home / ".config/ghostty/config"
        old.write_text("config-file = ~/.local/state/dye/current/theme/ghostty.conf\n")
        (self.home / ".config/ghostty/config.ghostty").write_text("font-size = 10\n")
        self.assertIsNone(wire.ghostty(self.paths))
        self.assertEqual((self.home / ".config/ghostty/config.ghostty").read_text(), "font-size = 10\n")

    def test_older_config_name(self):
        old = self.home / ".config/ghostty/config"
        old.write_text("font-size = 10\n")
        self.assertEqual(wire.ghostty(self.paths), old)
        self.assertFalse((self.home / ".config/ghostty/config.ghostty").exists())

    def test_writes_through_a_dotfiles_link(self):
        real = self.home / "dotfiles/zshrc"
        real.parent.mkdir()
        real.write_text("# mine\n")
        (self.home / ".zshrc").symlink_to(real)
        wire.zsh(self.paths)
        self.assertTrue((self.home / ".zshrc").is_symlink())
        self.assertIn(wire.ZSH, real.read_text())

    def test_unused_apps_are_left_alone(self):
        with mock.patch.object(wire.shutil, "which", return_value=None):
            self.assertIsNone(wire.ghostty(self.paths))
        self.assertFalse((self.home / ".config/ghostty/config.ghostty").exists())
        self.assertIsNone(wire.zsh(self.paths))  # no ~/.zshrc: not a zsh user
        self.assertFalse((self.home / ".zshrc").exists())

    def test_new_ghostty_config_when_installed(self):
        with mock.patch.object(wire.shutil, "which", return_value="/usr/bin/ghostty"):
            f = wire.ghostty(self.paths)
        self.assertEqual(f.read_text(), wire.GHOSTTY)

    def test_readme_shows_the_same_hook(self):
        self.assertIn(wire.ZSH, (helpers.ROOT / "README.md").read_text())


if __name__ == "__main__":
    unittest.main()
