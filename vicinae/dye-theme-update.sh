#!/bin/bash

# @vicinae.schemaVersion 1
# @vicinae.title Update Themes
# @vicinae.mode compact
# @vicinae.icon 📦
# @vicinae.packageName Dye
# @vicinae.description Pull every theme installed from git

dye=$(command -v dye || echo "$HOME/.local/bin/dye")
exec "$dye" theme update
