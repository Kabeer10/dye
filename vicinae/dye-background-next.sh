#!/bin/bash

# @vicinae.schemaVersion 1
# @vicinae.title Next Background
# @vicinae.mode silent
# @vicinae.icon 🖼️
# @vicinae.packageName Dye
# @vicinae.description Cycle the current theme's backgrounds

dye=$(command -v dye || echo "$HOME/.local/bin/dye")
exec "$dye" bg next
