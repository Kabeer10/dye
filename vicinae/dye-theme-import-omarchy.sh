#!/bin/bash

# @vicinae.schemaVersion 1
# @vicinae.title Import Omarchy Themes
# @vicinae.mode compact
# @vicinae.icon 📦
# @vicinae.packageName Dye
# @vicinae.description Copy Omarchy's stock themes into dye

dye=$(command -v dye || echo "$HOME/.local/bin/dye")
exec "$dye" theme import-omarchy --all
