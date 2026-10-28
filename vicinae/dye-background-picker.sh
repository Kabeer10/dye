#!/bin/bash

# @vicinae.schemaVersion 1
# @vicinae.title Pick Background
# @vicinae.mode silent
# @vicinae.icon 🖼️
# @vicinae.packageName Dye
# @vicinae.description Open the background carousel for the current theme

dye=$(command -v dye || echo "$HOME/.local/bin/dye")
exec "$dye" bg picker
