# config.py
# Edit this file to change project complexity options and task counts

PROJECT_COMPLEXITIES = [
    {"label": "Quick Win (3 tasks)",        "task_count": 3},
    {"label": "Small Project (5 tasks)",    "task_count": 5},
    {"label": "Medium Project (10 tasks)",  "task_count": 10},
    {"label": "Large Project (15 tasks)",   "task_count": 15},
    {"label": "Enterprise (20 tasks)",      "task_count": 20},
]

# Colour palette (name → hex)
TASK_COLOURS = {
    "Dark Blue":   "#1B3A6B",
    "Steel Blue":  "#4A90D9",
    "Teal":        "#2A7F7F",
    "Slate Grey":  "#5A6A7A",
    "Charcoal":    "#3C3C3C",
}

DEFAULT_DURATION_DAYS = 10
DEFAULT_START_OFFSET_DAYS = 5   # days from today
DEFAULT_COLOUR = "Dark Blue"
