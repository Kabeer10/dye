#!/bin/bash

# @vicinae.schemaVersion 1
# @vicinae.title Set Theme
# @vicinae.mode compact
# @vicinae.icon 🎨
# @vicinae.packageName Dye
# @vicinae.description Switch to a theme by name
# @vicinae.argument1 { "type": "text", "placeholder": "theme name" }

dye=$(command -v dye || echo "$HOME/.local/bin/dye")
exec "$dye" theme set "$1"
