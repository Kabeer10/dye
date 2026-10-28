#!/bin/bash

# @vicinae.schemaVersion 1
# @vicinae.title Previous Theme
# @vicinae.mode silent
# @vicinae.icon 🎨
# @vicinae.packageName Dye
# @vicinae.description Switch to the previous theme

dye=$(command -v dye || echo "$HOME/.local/bin/dye")
exec "$dye" theme prev
