"""Zen (native or the Flathub flatpak): userChrome.css / userContent.css."""
import re

from .. import util


def zen_profiles(paths):
    for root in (paths.home / ".var/app/app.zen_browser.zen/.zen", paths.home / ".zen"):
        ini = root / "profiles.ini"
        if not ini.is_file():
            continue
        for m in re.finditer(r"(?m)^Path=(.+)$", ini.read_text()):
            p = root / m.group(1).strip()
            if p.is_dir():
                yield p


def zen(ctx):
    chrome, content = ctx.file("userChrome.css"), ctx.file("userContent.css")
    if not chrome:
        return
    for profile in zen_profiles(ctx.paths):
        d = profile / "chrome"
        d.mkdir(exist_ok=True)
        util.install_file(chrome, d / "userChrome.css")
        if content:
            util.install_file(content, d / "userContent.css")
        # userChrome.css is only read when this pref is on.
        user_js = profile / "user.js"
        text = user_js.read_text() if user_js.is_file() else ""
        new = zen_enable_stylesheets(text)
        if new != text:
            util.atomic_write(user_js, new)


STYLESHEETS_PREF = "toolkit.legacyUserProfileCustomizations.stylesheets"
# An active user_pref line for it (not one in a comment), any quoting and spacing.
_PREF_LINE = re.compile(r'(?m)^([ \t]*user_pref\(\s*(["\'])' + re.escape(STYLESHEETS_PREF)
                        + r'\2\s*,\s*)(true|false)(\s*\)\s*;?)')


def _without_comments(text):
    """text with // and /* */ comments blanked out (same length, newlines kept), so
    matches in it are active code. Strings are skipped while looking for comments."""
    out, i, n = list(text), 0, len(text)
    while i < n:
        ch = text[i]
        if ch in "\"'":
            j = i + 1
            while j < n and text[j] != ch and text[j] != "\n":
                j += 2 if text[j] == "\\" else 1
            i = j + 1
        elif text.startswith("//", i):
            j = text.find("\n", i)
            j = n if j < 0 else j
            out[i:j] = " " * (j - i)
            i = j
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out[i:j] = [c if c == "\n" else " " for c in text[i:j]]
            i = j
        else:
            i += 1
    return "".join(out)


def zen_enable_stylesheets(text):
    """user.js with the stylesheet pref on; the last active line wins in Firefox, so
    every active one is set to true. Comments (// and /* */) and other prefs are kept."""
    spans = [m for m in _PREF_LINE.finditer(_without_comments(text))]
    if spans:
        for m in reversed(spans):  # same offsets in text: blanking keeps lengths
            a, b = m.span(3)
            text = text[:a] + "true" + text[b:]
        return text
    pref = f'user_pref("{STYLESHEETS_PREF}", true);'
    return text + ("\n" if text and not text.endswith("\n") else "") + pref + "\n"

