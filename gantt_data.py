# gantt_data.py
# Data structures and business logic for the Gantt chart tool

from datetime import date, timedelta
from dataclasses import dataclass, field
from typing import Optional
import pandas as pd

from config import DEFAULT_DURATION_DAYS, DEFAULT_START_OFFSET_DAYS, DEFAULT_COLOUR


@dataclass
class Task:
    task_id: str
    name: str
    duration: int           # days (0 = milestone)
    start_date: date
    end_date: date
    colour: str
    dependency: str         # free-text, e.g. "T-001" or blank

    @property
    def is_milestone(self) -> bool:
        return self.duration == 0


def make_default_task(index: int) -> Task:
    """Return a task populated with sensible defaults."""
    start = date.today() + timedelta(days=DEFAULT_START_OFFSET_DAYS)
    end   = start + timedelta(days=DEFAULT_DURATION_DAYS)
    task_id = f"T-{index:03d}"
    return Task(
        task_id    = task_id,
        name       = f"Task {index}",
        duration   = DEFAULT_DURATION_DAYS,
        start_date = start,
        end_date   = end,
        colour     = DEFAULT_COLOUR,
        dependency = "",
    )


def create_project(task_count: int) -> list[Task]:
    """Initialise a project with `task_count` default tasks."""
    return [make_default_task(i + 1) for i in range(task_count)]


def recalc_end(task: Task) -> date:
    """Recompute end date from start + duration (milestone stays on start date)."""
    if task.duration == 0:
        return task.start_date
    return task.start_date + timedelta(days=task.duration)


def tasks_to_df(tasks: list[Task]) -> pd.DataFrame:
    """Convert task list to a DataFrame for easy display / editing."""
    rows = []
    for t in tasks:
        rows.append({
            "ID":         t.task_id,
            "Task Name":  t.name,
            "Duration":   t.duration,
            "Start Date": t.start_date,
            "End Date":   t.end_date,
            "Colour":     t.colour,
            "Dependency": t.dependency,
        })
    return pd.DataFrame(rows)


def df_to_tasks(df: pd.DataFrame) -> list[Task]:
    """Reconstruct task list from an edited DataFrame."""
    tasks = []
    for _, row in df.iterrows():
        start = row["Start Date"]
        if hasattr(start, "date"):      # pandas Timestamp → date
            start = start.date()
        dur = int(row["Duration"])
        end = start + timedelta(days=dur) if dur > 0 else start
        tasks.append(Task(
            task_id    = str(row["ID"]),
            name       = str(row["Task Name"]),
            duration   = dur,
            start_date = start,
            end_date   = end,
            colour     = str(row["Colour"]),
            dependency = str(row["Dependency"]) if row["Dependency"] else "",
        ))
    return tasks
