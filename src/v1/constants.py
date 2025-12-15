"""Constants for the global solar forecast app."""

# OCF colours (palette) - updated to new OCF colors
ocf_palette = [
    "#4675c1",
    "#65b0c9",
    "#58b0a9",
    "#ffd480",
    "#faa056",
    "#9cb6e1",
    "#a3d6e0",
    "#9ed1cd",
    "#ffe9bc",
    "#ffdabc",
]

# Chart styling constants
FORECAST_LINE_STYLE = {"color": ocf_palette[0], "width": 2}
SEASONAL_NORM_LINE_STYLE = {"color": ocf_palette[1], "width": 2, "dash": "dash"}
CHART_LEGEND_CONFIG = {
    "orientation": "h",
    "yanchor": "bottom",
    "y": 1.02,
    "xanchor": "right",
    "x": 1,
}
