/* dye-shell colours for {{ dye_theme_name }} (dye template). Appended to the
   theme's shell stylesheet; the layout lives in the extension's stylesheet.css.
   Colours are !important so they win over the extension's stylesheet and over
   shell themes that mark their panel colours !important. */

/* ---- bar islands ------------------------------------------------------------ */

#panelBox #panel.dye-bar #panelLeft,
#panelBox #panel.dye-bar #panelRight {
  border-color: rgba({{ foreground_rgb }}, 0.14) !important;
  background-color: rgba({{ ui_surface_rgb }}, 0.95) !important;
}

#panelBox #panel.dye-bar .panel-button {
  background-color: transparent !important;
  box-shadow: none !important;
}

#panelBox #panel.dye-bar .panel-button,
#panelBox #panel.dye-bar .panel-button StIcon,
#panelBox #panel.dye-bar .panel-button StLabel {
  color: {{ foreground }} !important;
}

#panelBox #panel.dye-bar .panel-button:hover,
#panelBox #panel.dye-bar .panel-button:focus {
  box-shadow: inset 0 0 0 100px rgba({{ foreground_rgb }}, 0.08) !important;
}

#panelBox #panel.dye-bar .panel-button:active,
#panelBox #panel.dye-bar .panel-button:checked {
  box-shadow: inset 0 0 0 100px rgba({{ foreground_rgb }}, 0.13) !important;
}

#panelBox #panel.dye-bar .panel-button#panelActivities .workspace-dot {
  background-color: {{ foreground }} !important;
}

#panelBox #panel.dye-bar .dye-sep {
  background-color: {{ ui_border }} !important;
}

#panelBox #panel.dye-bar .ai-usage-value.ai-usage-warn { color: {{ ui_warning }} !important; }
#panelBox #panel.dye-bar .ai-usage-value.ai-usage-crit,
#panelBox #panel.dye-bar .ai-usage-alert { color: {{ ui_danger }} !important; }
#panelBox #panel.dye-bar .ai-usage-value.ai-usage-dim { color: {{ ui_faint }} !important; }

/* ---- the capsule (the inverse surface) ----------------------------------------- */

#panelBox #panel.dye-bar .panel-button.dye-capsule {
  background-color: {{ ui_inverse }} !important;
}

#panelBox #panel.dye-bar .panel-button.dye-capsule:hover,
#panelBox #panel.dye-bar .panel-button.dye-capsule:focus {
  box-shadow: none !important;
  background-color: {{ mix ui_inverse ui_inverse_fg 7% }} !important;
}

#panelBox #panel.dye-bar .panel-button.dye-capsule:active,
#panelBox #panel.dye-bar .panel-button.dye-capsule:checked {
  box-shadow: none !important;
  background-color: {{ mix ui_inverse ui_inverse_fg 12% }} !important;
}

#panelBox #panel.dye-bar .dye-capsule .dye-main {
  color: {{ ui_inverse_fg }} !important;
}

#panelBox #panel.dye-bar .dye-capsule .dye-lead,
#panelBox #panel.dye-bar .dye-capsule .dye-trail {
  color: {{ ui_inverse_dim }} !important;
}

#panelBox #panel.dye-bar .dye-capsule .dye-meeting .dye-trail,
#panelBox #panel.dye-bar .dye-capsule .messages-indicator {
  color: {{ ui_inverse_accent }} !important;
}

#panelBox #panel.dye-bar .dye-capsule .dye-meeting .dye-badge {
  background-color: {{ ui_inverse_accent }} !important;
}

#panelBox #panel.dye-bar .dye-capsule .dye-meeting .dye-badge-icon {
  color: {{ ui_inverse_on_accent }} !important;
}

#panelBox #panel.dye-bar .dye-capsule .dye-flash .dye-badge {
  background-color: rgba({{ ui_inverse_fg_rgb }}, 0.12) !important;
}

#panelBox #panel.dye-bar .dye-capsule .dye-flash .dye-badge-icon {
  color: {{ ui_inverse_fg }} !important;
}

/* ---- pickers ------------------------------------------------------------------- */

.dye-picker {
  background-color: rgba({{ background_rgb }}, 0.86) !important;
}

.dye-picker-card {
  background-color: {{ ui_surface }} !important;
  border-color: rgba({{ foreground_rgb }}, 0.10) !important;
}

.dye-picker-card.dye-picker-selected {
  border-color: {{ accent }} !important;
}

.dye-picker-title {
  color: {{ foreground }} !important;
}

.dye-picker-subtitle,
.dye-picker-hint {
  color: {{ ui_dim }} !important;
}

.dye-picker-filter {
  color: {{ ui_on_accent }} !important;
  background-color: {{ accent }} !important;
}

.dye-picker-confirm {
  color: {{ foreground }} !important;
  background-color: {{ ui_surface }} !important;
  border-color: {{ ui_danger }} !important;
}

.dye-picker-badge {
  color: {{ ui_on_accent }} !important;
  background-color: {{ accent }} !important;
}
