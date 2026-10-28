#!/bin/bash

# @vicinae.schemaVersion 1
# @vicinae.title Toggle Light/Dark Theme
# @vicinae.mode silent
# @vicinae.icon 🌗
# @vicinae.packageName Dye
# @vicinae.description Switch to the current theme's light or dark pair

dye=$(command -v dye || echo "$HOME/.local/bin/dye")
exec "$dye" mode toggle
