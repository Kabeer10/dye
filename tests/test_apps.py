"""The config edits the retints make: other people's settings files survive them."""
import json
import unittest

import helpers
from dye import paths as paths_mod
from dye import util
from dye.apps import Context, agents, editors, web

def context(home, theme_dir, mode="dark"):
    p = paths_mod.Paths(home=home, config=home / ".config", data=home / ".local/share",
                        state=home / ".local/state", cache=home / ".cache", runtime=home / "run")
    return Context(paths=p, settings={}, name="sample", display="Sample", colors={"mode": mode},
                   mode=mode, dir=theme_dir, generation="1-1")


class Claude(unittest.TestCase):
    def setUp(self):
        self.home = helpers.tempdir(self)
        self.theme = self.home / "theme"
        self.theme.mkdir()
        (self.theme / "claude.json").write_text('{"name": "dye"}\n')

    def test_empty_settings_stay_valid(self):
        d = self.home / ".claude"
        d.mkdir()
        (d / "settings.json").write_text("{}")
        agents.claude(context(self.home, self.theme))
        self.assertEqual(json.loads((d / "settings.json").read_text()), {"theme": "custom:dye"})

    def test_one_broken_account_is_left_alone_and_reported(self):
        good, bad = self.home / ".claude", self.home / ".claude-work"
        for d in (good, bad):
            d.mkdir()
        (good / "settings.json").write_text('{"model": "opus"}\n')
        (bad / "settings.json").write_text('{"model": "opus",}\n')
        with self.assertRaises(RuntimeError):
            agents.claude(context(self.home, self.theme))
        self.assertEqual(json.loads((good / "settings.json").read_text())["theme"], "custom:dye")
        self.assertEqual((bad / "settings.json").read_text(), '{"model": "opus",}\n')


class VsCode(unittest.TestCase):
    def test_jsonc_settings(self):
        home = helpers.tempdir(self)
        theme = home / "theme"
        theme.mkdir()
        (theme / "vscode-theme.json").write_text('{"colors": {}}')
        settings = home / ".config/Code/User/settings.json"
        settings.parent.mkdir(parents=True)
        text = ('{\n  // "workbench.colorTheme": "Commented",\n  "window.autoDetectColorScheme": true,\n'
                '  "[python]": {"workbench.colorTheme": "Nested"},\n  "workbench.colorTheme": "Default Dark+",\n}\n')
        settings.write_text(text)
        (home / ".vscode/extensions").mkdir(parents=True)
        editors.vscode(context(home, theme))
        out = settings.read_text()
        self.assertEqual(util.jsonc_get(out, "workbench.colorTheme"), "Dye")
        self.assertEqual(util.jsonc_get(out, "workbench.preferredDarkColorTheme"), "Dye")
        self.assertIn('"Commented"', out)
        self.assertIn('"Nested"', out)


class Zen(unittest.TestCase):
    PREF = 'user_pref("toolkit.legacyUserProfileCustomizations.stylesheets", true);'

    def test_false_becomes_true(self):
        out = web.zen_enable_stylesheets('user_pref("a", 1);\n'
                                         'user_pref("toolkit.legacyUserProfileCustomizations.stylesheets", false);\n')
        self.assertIn(self.PREF, out)
        self.assertNotIn("false", out)
        self.assertIn('user_pref("a", 1);', out)

    def test_a_comment_doesnt_count(self):
        text = '// user_pref("toolkit.legacyUserProfileCustomizations.stylesheets", false);\n'
        out = web.zen_enable_stylesheets(text)
        self.assertTrue(out.startswith(text))
        self.assertTrue(out.rstrip().endswith(self.PREF))

    def test_block_comments_dont_count(self):
        text = '/*\nuser_pref("toolkit.legacyUserProfileCustomizations.stylesheets", false);\n*/\n'
        out = web.zen_enable_stylesheets(text)
        self.assertTrue(out.startswith(text))
        self.assertTrue(out.rstrip().endswith(self.PREF))
        text = 'user_pref("x", "/* not a comment");\nuser_pref("toolkit.legacyUserProfileCustomizations.stylesheets", false);\n'
        self.assertEqual(web.zen_enable_stylesheets(text), text.replace("false", "true"))

    def test_already_on(self):
        text = "  user_pref('toolkit.legacyUserProfileCustomizations.stylesheets' , true );\n"
        self.assertEqual(web.zen_enable_stylesheets(text), text)
        self.assertEqual(web.zen_enable_stylesheets(""), self.PREF + "\n")


if __name__ == "__main__":
    unittest.main()
