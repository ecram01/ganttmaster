# gantt_chart.py
# Renders the Gantt chart using Matplotlib and exports to PDF (A3 landscape)

import io
import math
from datetime import date, timedelta

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import matplotlib.dates as mdates
import numpy as np

from config import TASK_COLOURS

# ── Layout constants ────────────────────────────────────────────────────────
A3_LANDSCAPE_INCHES = (16.54, 11.69)   # exact A3 landscape
ROW_HEIGHT          = 0.55
BAR_HEIGHT          = 0.32
MILESTONE_SIZE      = 120              # scatter marker size
LEFT_PANEL_FRAC     = 0.28             # fraction of figure width for task list
FONT_FAMILY         = "DejaVu Sans"

# Colour helpers
BG_COLOUR     = "#F7F9FC"
GRID_COLOUR   = "#DDE3EC"
HEADER_BG     = "#1B3A6B"
HEADER_FG     = "white"
ALT_ROW       = "#EEF2F8"
TODAY_COLOUR  = "#E05252"
BORDER_COLOUR = "#C0C8D8"


def _month_ticks(start: date, end: date):
    """Generate first-of-month dates covering [start, end]."""
    ticks = []
    y, m = start.year, start.month
    while True:
        d = date(y, m, 1)
        if d > end + timedelta(days=31):
            break
        ticks.append(d)
        m += 1
        if m > 12:
            m, y = 1, y + 1
    return ticks


def build_chart(tasks) -> plt.Figure:
    """Build and return a Matplotlib figure of the Gantt chart."""
    if not tasks:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "No tasks to display", ha="center", va="center")
        return fig

    n = len(tasks)
    fig_h = max(A3_LANDSCAPE_INCHES[1], ROW_HEIGHT * n + 2.5)
    fig = plt.figure(figsize=A3_LANDSCAPE_INCHES, dpi=150)
    fig.patch.set_facecolor(BG_COLOUR)

    # ── Axes setup ──────────────────────────────────────────────────────────
    left_ax  = fig.add_axes([0.01, 0.08, LEFT_PANEL_FRAC - 0.01, 0.82])
    right_ax = fig.add_axes([LEFT_PANEL_FRAC, 0.08, 0.99 - LEFT_PANEL_FRAC, 0.82])

    for spine in left_ax.spines.values():
        spine.set_visible(False)
    left_ax.set_facecolor(BG_COLOUR)
    left_ax.tick_params(left=False, bottom=False, labelbottom=False)
    left_ax.set_xlim(0, 1)
    left_ax.set_ylim(-0.5, n - 0.5)
    left_ax.invert_yaxis()
    left_ax.set_yticks([])

    # ── Date range ──────────────────────────────────────────────────────────
    all_starts = [t.start_date for t in tasks]
    all_ends   = [t.end_date   for t in tasks]
    proj_start = min(all_starts) - timedelta(days=3)
    proj_end   = max(all_ends)   + timedelta(days=3)

    right_ax.set_xlim(
        mdates.date2num(proj_start),
        mdates.date2num(proj_end)
    )
    right_ax.set_ylim(-0.5, n - 0.5)
    right_ax.invert_yaxis()
    right_ax.set_facecolor(BG_COLOUR)
    for spine in right_ax.spines.values():
        spine.set_color(BORDER_COLOUR)

    # ── Row alternating bands ────────────────────────────────────────────────
    for i in range(n):
        colour = ALT_ROW if i % 2 == 0 else BG_COLOUR
        left_ax.axhspan(i - 0.5, i + 0.5, color=colour, zorder=0)
        right_ax.axhspan(i - 0.5, i + 0.5, color=colour, zorder=0)

    # ── Vertical grid (monthly) ──────────────────────────────────────────────
    month_ticks = _month_ticks(proj_start, proj_end)
    for d in month_ticks:
        right_ax.axvline(mdates.date2num(d), color=GRID_COLOUR,
                         linewidth=0.7, zorder=1)

    # ── X-axis (months) ──────────────────────────────────────────────────────
    right_ax.xaxis.set_major_locator(mdates.MonthLocator())
    right_ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    right_ax.xaxis.set_tick_params(labelsize=7, rotation=35,
                                   labelcolor="#334155")
    right_ax.tick_params(axis="y", left=False, labelleft=False)

    # ── Today line ──────────────────────────────────────────────────────────
    today_num = mdates.date2num(date.today())
    if proj_start <= date.today() <= proj_end:
        right_ax.axvline(today_num, color=TODAY_COLOUR,
                         linewidth=1.2, linestyle="--", zorder=5)
        right_ax.text(today_num, -0.45, " Today",
                      color=TODAY_COLOUR, fontsize=6.5, va="top", zorder=6)

    # ── Draw tasks ───────────────────────────────────────────────────────────
    col_widths = [0.06, 0.44, 0.24, 0.26]   # ID | Name | Duration | Dates
    col_x      = [sum(col_widths[:i]) for i in range(len(col_widths))]
    headers    = ["ID", "Task Name", "Duration", "Dates"]

    # Header row
    left_ax.add_patch(FancyBboxPatch(
        (0, -0.5), 1, 0.5,
        boxstyle="square,pad=0",
        facecolor=HEADER_BG, edgecolor="none", zorder=3,
        transform=left_ax.transData, clip_on=False
    ))
    for hx, hw, hl in zip(col_x, col_widths, headers):
        left_ax.text(hx + hw / 2, -0.25, hl,
                     ha="center", va="center",
                     fontsize=7.5, fontweight="bold",
                     color=HEADER_FG, zorder=4)

    right_ax.add_patch(FancyBboxPatch(
        (mdates.date2num(proj_start), -0.5),
        mdates.date2num(proj_end) - mdates.date2num(proj_start), 0.5,
        boxstyle="square,pad=0",
        facecolor=HEADER_BG, edgecolor="none", zorder=3,
        transform=right_ax.transData, clip_on=False
    ))
    right_ax.text(
        (mdates.date2num(proj_start) + mdates.date2num(proj_end)) / 2,
        -0.25, "Project Timeline",
        ha="center", va="center",
        fontsize=8, fontweight="bold", color=HEADER_FG, zorder=4
    )

    for i, task in enumerate(tasks):
        hex_col = TASK_COLOURS.get(task.colour, "#1B3A6B")

        # ── Left panel text ──────────────────────────────────────────────────
        cell_vals = [
            task.task_id,
            task.name,
            "Milestone" if task.is_milestone else f"{task.duration}d",
            task.start_date.strftime("%d %b") + " → " +
            task.end_date.strftime("%d %b"),
        ]
        for cx, cw, cv in zip(col_x, col_widths, cell_vals):
            left_ax.text(
                cx + cw / 2, i, cv,
                ha="center", va="center",
                fontsize=6.8, color="#1E293B",
                fontfamily=FONT_FAMILY
            )

        # ── Right panel bar / milestone ──────────────────────────────────────
        if task.is_milestone:
            mx = mdates.date2num(task.start_date)
            right_ax.scatter(mx, i, marker="D",
                             s=MILESTONE_SIZE, color=hex_col,
                             zorder=4, edgecolors="white", linewidths=0.6)
        else:
            x0   = mdates.date2num(task.start_date)
            x1   = mdates.date2num(task.end_date)
            width = x1 - x0
            bar  = FancyBboxPatch(
                (x0, i - BAR_HEIGHT / 2), width, BAR_HEIGHT,
                boxstyle="round,pad=0.3",
                facecolor=hex_col, edgecolor="white",
                linewidth=0.5, zorder=4
            )
            right_ax.add_patch(bar)
            # Label inside bar if wide enough
            if width > 5:
                right_ax.text(
                    x0 + width / 2, i,
                    task.name, ha="center", va="center",
                    fontsize=5.8, color="white",
                    fontweight="bold", clip_on=True, zorder=5
                )

    # ── Dependency arrows ────────────────────────────────────────────────────
    id_to_idx = {t.task_id: idx for idx, t in enumerate(tasks)}
    for i, task in enumerate(tasks):
        if task.dependency and task.dependency in id_to_idx:
            src_idx = id_to_idx[task.dependency]
            src_task = tasks[src_idx]
            x_start = mdates.date2num(src_task.end_date)
            x_end   = mdates.date2num(task.start_date)
            right_ax.annotate(
                "", xy=(x_end, i), xytext=(x_start, src_idx),
                arrowprops=dict(
                    arrowstyle="->", color=BORDER_COLOUR,
                    lw=1.0, connectionstyle="arc3,rad=0.1"
                ),
                zorder=3
            )

    # ── Legend ───────────────────────────────────────────────────────────────
    legend_handles = []
    for name, hex_c in TASK_COLOURS.items():
        legend_handles.append(
            mpatches.Patch(facecolor=hex_c, label=name, edgecolor="white")
        )
    # Milestone marker
    legend_handles.append(
        plt.scatter([], [], marker="D", color="#555", s=60,
                    label="Milestone", edgecolors="white")
    )
    fig.legend(
        handles=legend_handles,
        loc="lower center", ncol=len(legend_handles),
        fontsize=7, framealpha=0.9,
        bbox_to_anchor=(0.5, 0.01),
        handlelength=1.5, handleheight=0.9
    )

    # ── Title ────────────────────────────────────────────────────────────────
    fig.text(0.5, 0.93, "Project Gantt Chart",
             ha="center", va="center",
             fontsize=14, fontweight="bold",
             color=HEADER_BG, fontfamily=FONT_FAMILY)
    fig.text(0.5, 0.905,
             f"Generated {date.today().strftime('%d %B %Y')} · "
             f"{n} tasks · "
             f"{proj_start.strftime('%b %Y')} – {proj_end.strftime('%b %Y')}",
             ha="center", va="center", fontsize=8, color="#64748B")

    plt.tight_layout(rect=[0, 0.06, 1, 0.90])
    return fig


def fig_to_pdf_bytes(fig: plt.Figure) -> bytes:
    """Serialise figure to PDF bytes at A3 landscape size."""
    buf = io.BytesIO()
    fig.savefig(buf, format="pdf",
                bbox_inches="tight",
                facecolor=fig.get_facecolor())
    buf.seek(0)
    return buf.read()


def fig_to_png_bytes(fig: plt.Figure) -> bytes:
    """Serialise figure to PNG bytes (for Streamlit display)."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150,
                bbox_inches="tight",
                facecolor=fig.get_facecolor())
    buf.seek(0)
    return buf.read()
