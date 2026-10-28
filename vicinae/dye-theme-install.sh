#!/bin/bash

# @vicinae.schemaVersion 1
# @vicinae.title Install Theme
# @vicinae.mode compact
# @vicinae.icon 📦
# @vicinae.packageName Dye
# @vicinae.description Install a theme from a git repository (Omarchy format)
# @vicinae.argument1 { "type": "text", "placeholder": "git URL" }

dye=$(command -v dye || echo "$HOME/.local/bin/dye")
exec "$dye" theme install "$1"
