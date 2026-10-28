#!/bin/bash

# @vicinae.schemaVersion 1
# @vicinae.title Pick Theme
# @vicinae.mode silent
# @vicinae.icon 🎨
# @vicinae.packageName Dye
# @vicinae.description Open the theme carousel

dye=$(command -v dye || echo "$HOME/.local/bin/dye")
exec "$dye" theme picker
