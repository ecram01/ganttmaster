# gantt_data.py
from datetime import date, timedelta
from dataclasses import dataclass
from typing import List
import pandas as pd

from config import DEFAULT_DURATION_DAYS, DEFAULT_START_OFFSET_DAYS, DEFAULT_COLOUR


@dataclass
class Task:
    task_id: str
    name: str
    duration: int
    start_date: date
    end_date: date
    colour: str
    dependency: str

    @property
    def is_milestone(self) -> bool:
        return self.duration == 0


def make_default_task(index: int) -> Task:
    start = date.today() + timedelta(days=DEFAULT_START_OFFSET_DAYS)
    end   = start + timedelta(days=DEFAULT_DURATION_DAYS)
    return Task(
        task_id    = f"T-{index:03d}",
        name       = f"Task {index}",
        duration   = DEFAULT_DURATION_DAYS,
        start_date = start,
        end_date   = end,
        colour     = DEFAULT_COLOUR,
        dependency = "",
    )


def create_project(task_count: int) -> List[Task]:
    return [make_default_task(i + 1) for i in range(task_count)]


def resolve_dependencies(tasks: List[Task]) -> List[Task]:
    """
    Cascade finish-to-start dependencies.
    If task B depends on task A, B.start_date = A.end_date,
    and B.end_date = B.start_date + B.duration.
    Processes tasks in list order; handles simple chains.
    """
    id_to_task = {t.task_id: t for t in tasks}
    # Iterate until stable (handles chains of any depth, up to len(tasks) passes)
    for _ in range(len(tasks)):
        changed = False
        for task in tasks:
            dep_id = task.dependency.strip() if task.dependency else ""
            if dep_id and dep_id in id_to_task:
                parent = id_to_task[dep_id]
                new_start = parent.end_date
                if new_start != task.start_date:
                    task.start_date = new_start
                    task.end_date   = new_start if task.duration == 0 else new_start + timedelta(days=task.duration)
                    changed = True
        if not changed:
            break
    return tasks


def tasks_to_df(tasks: List[Task]) -> pd.DataFrame:
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


def df_to_tasks(df: pd.DataFrame) -> List[Task]:
    tasks = []
    for _, row in df.iterrows():
        start = row["Start Date"]
        if hasattr(start, "date"):
            start = start.date()
        dur = int(row["Duration"])
        end = start if dur == 0 else start + timedelta(days=dur)
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
