"""What install.sh backs up before the first switch: every existing file a retint
edits in place, found with the same lookups the retints use (Claude accounts,
T3CODE_HOME, Zen profiles from profiles.ini...). Files dye only adds
(its own theme files) aren't listed; nothing needs them to go back.
"""
from .apps import agents, web


def targets(paths):
    c, h = paths.config, paths.home
    files = [c / "gtk-4.0" / "gtk.css", c / "gtk-4.0" / "gtk-dark.css", c / "gtk-3.0" / "gtk.css"]
    files += [d / "settings.json" for d in agents.claude_dirs(paths)]
    files += [agents.t3_userdata(paths) / "settings.json"]
    files += [c / "Code" / "User" / "settings.json", h / ".vscode" / "extensions" / "extensions.json",
              h / ".vscode" / "extensions" / ".obsolete"]
    files += [c / "vicinae" / "settings.json", c / "ghostty" / "config", c / "ghostty" / "config.ghostty"]
    for profile in web.zen_profiles(paths):
        files += [profile / "chrome" / "userChrome.css", profile / "chrome" / "userContent.css",
                  profile / "user.js"]
    seen, out = set(), []
    for f in files:
        if (f.exists() or f.is_symlink()) and f not in seen:
            seen.add(f)
            out.append(f)
    return out
