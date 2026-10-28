#!/bin/bash

# @vicinae.schemaVersion 1
# @vicinae.title Dye Doctor
# @vicinae.mode fullOutput
# @vicinae.icon 🩺
# @vicinae.packageName Dye
# @vicinae.description Check that every app follows the theme

dye=$(command -v dye || echo "$HOME/.local/bin/dye")
exec "$dye" doctor
