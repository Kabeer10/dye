#!/bin/bash

# @vicinae.schemaVersion 1
# @vicinae.title Next Theme
# @vicinae.mode silent
# @vicinae.icon 🎨
# @vicinae.packageName Dye
# @vicinae.description Switch to the next theme

dye=$(command -v dye || echo "$HOME/.local/bin/dye")
exec "$dye" theme next
