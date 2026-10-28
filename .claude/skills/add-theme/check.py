#!/usr/bin/env python3
"""Check a dye theme before it ships: palette warnings, mode, GNOME accent, icons,
wallpapers, contrast of the pairs people read, and files that override templates.

    python3 .claude/skills/add-theme/check.py <theme-name>
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "lib"))

from dye import colormath as cm, palette, paths as paths_mod, stage, themes  # noqa: E402
from dye.apps import gnome  # noqa: E402

# (foreground key, background key, floor, target, what it is). Below the floor is a
# problem (stock themes pin a fix, see emberveil's muted); between floor and target is
# a judgement call (akane's muted at 2.97 and harbor's dim text at 4.17 were kept).
PAIRS = [
    ("foreground", "background", 4.5, 7.0, "body text"),
    ("dark_foreground", "background", 3.0, 4.5, "secondary text"),
    ("muted", "background", 2.5, 3.0, "comments, hints, borders"),
    ("color8", "background", 0, 3.0, "terminal bright black (often dim on purpose)"),
    ("selection_foreground", "selection_background", 3.0, 4.5, "selected text"),
    ("ui_dim", "background", 3.0, 4.5, "dim UI text"),
    ("ui_on_accent", "accent", 3.0, 4.5, "text on the accent"),
    ("ui_inverse_fg", "ui_inverse", 3.0, 4.5, "bar capsule text"),
    ("accent", "background", 2.0, 3.0, "accent as text/indicator"),
]
# Files dye uses besides colors.toml and the template outputs.
USED = {"colors.toml", "gnome.toml", "icons.theme", "light.mode", "preview.png", "vscode.json",
        "gnome-shell.css", "alacritty.toml", "NOTICE"}


def main(name):
    paths = paths_mod.get()
    t = themes.find(paths, name)
    if t is None:
        sys.exit(f"no theme '{name}' (dye theme list)")
    print(f"{t.display}  [{t.origin}{', git' if t.git else ''}]  {' + '.join(map(str, t.dirs))}")
    problems = 0

    warnings = []
    text = t.colors_text()
    if text is None:
        sys.exit("no colors.toml")
    raw = palette.parse(text, warnings)
    c = t.palette()
    for w in warnings:
        print(f"  ! palette: {w}")
        problems += 1

    light_file = any((d / "light.mode").exists() for d in t.dirs)
    print(f"  mode       {c['mode']}  (mode key: {raw.get('mode', '-')}, light.mode file: {light_file})")
    if light_file and raw.get("mode") == "dark" or (raw.get("mode") == "light" and not light_file):
        print("  ! mode key and light.mode disagree (Omarchy reads light.mode)")

    pins = {}
    gt = t.file("gnome.toml")
    if gt:
        import tomllib
        pins = tomllib.loads(gt.read_text())
    nearest = gnome.nearest_accent(c["accent"])
    print(f"  accent     {c['accent']} -> GNOME '{pins.get('accent', nearest)}'"
          + (f" (pinned; nearest is '{nearest}')" if "accent" in pins else " (nearest; pin in gnome.toml if wrong)"))

    icons = t.file("icons.theme")
    print(f"  icons      {icons.read_text().split()[0] if icons else '- (Colloid from the accent)'}"
          + (f", pinned {pins['icons']}" if "icons" in pins else ""))
    bgs = t.backgrounds(paths)
    print(f"  wallpapers {len(bgs)}" + ("" if bgs else "  ! none: the picker card and desktop stay plain"))
    print(f"  preview    {'preview.png' if t.file('preview.png') else '- (first wallpaper is the card)'}")

    print("  contrast")
    for fg, bg, floor, target, what in PAIRS:
        if fg not in c or bg not in c:
            continue
        r = cm.contrast(c[fg], c[bg])
        flag = "  " if r >= target else (" ~" if r >= floor else " !")
        problems += r < floor
        print(f"   {flag} {r:5.2f} (≥{target}, floor {floor})  {fg} {c[fg]} on {bg} {c[bg]}  — {what}")

    shipped = sorted({p.name for d in t.dirs for p in d.iterdir() if p.is_file()})
    tpls = {p.name[:-4] for p in (ROOT / "templates").glob("*.tpl")}
    overrides = [f for f in shipped if f in tpls]
    if overrides:
        print(f"  overrides  {', '.join(overrides)} (used instead of dye's templates)")
    unused = [f for f in shipped if f not in tpls and f not in USED and not stage.QUIET.match(f)]
    code = [f for f in unused if stage.denied(f)]
    if code:
        print(f"  ! ships {', '.join(code)}: runs code and dye doesn't use it; leave it out")
        problems += 1
    rest = [f for f in unused if f not in code]
    if rest:
        print(f"  ~ ships {', '.join(rest)}: dye doesn't use it (stock themes leave these out)")

    print(f"\n{problems} problem(s)" if problems else "\nlooks good")
    return 1 if problems else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1]))
