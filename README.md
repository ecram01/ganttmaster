# 📊 Gantt Chart Builder

A professional, interactive Gantt chart tool built with **Python**, **Streamlit**, and **Matplotlib**.

---

## Features

- **Project complexity presets** — choose from 3 to 20 tasks (configurable in `config.py`)
- **Interactive task editor** — edit task names, durations, start dates, colours and dependencies
- **Milestone support** — set duration to `0` to render a task as a ◆ diamond milestone
- **Dependency arrows** — enter a Task ID in the Dependency column to draw linking arrows
- **Live Gantt chart** — rendered at A3 landscape with monthly X-axis scaling
- **PDF export** — download the chart as a print-ready A3 PDF

---

## Project Structure

```
gantt_tool/
├── app.py            # Streamlit UI
├── config.py         # ← Edit complexity options & colours here
├── gantt_data.py     # Data models & business logic
├── gantt_chart.py    # Matplotlib chart renderer
├── requirements.txt
└── README.md
```

---

## Quick Start

### 1. Clone / initialise the repo

```bash
git init
git add .
git commit -m "Initial commit – Gantt Chart Builder"
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Run the app

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`.

---

## Customising Complexity Options

Open `config.py` and edit `PROJECT_COMPLEXITIES`:

```python
PROJECT_COMPLEXITIES = [
    {"label": "Quick Win (3 tasks)",        "task_count": 3},
    {"label": "Small Project (5 tasks)",    "task_count": 5},
    # Add or remove entries as needed
]
```

---

## Deploying to Streamlit Cloud

1. Push the repo to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect your repo.
3. Set the main file path to `app.py`.
