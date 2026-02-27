# gantt_chart.py
import io
from datetime import date, timedelta
from urllib.request import urlopen

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle
import matplotlib.dates as mdates
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import numpy as np

from config import TASK_COLOURS

# ── Layout ────────────────────────────────────────────────────────────────────
A3_LANDSCAPE_INCHES = (16.54, 11.69)
BAR_HEIGHT          = 0.38
MILESTONE_SIZE      = 140
LEFT_PANEL_FRAC     = 0.30
FONT_FAMILY         = "DejaVu Sans"

# ── Palette ───────────────────────────────────────────────────────────────────
BG_COLOUR     = "#FFFFFF"
ALT_ROW       = "#F2F5F9"
GRID_COLOUR   = "#DDE3EC"
HEADER_BG     = "#0A2647"
HEADER_FG     = "#FFFFFF"
SUBHEADER_BG  = "#144272"
TODAY_COLOUR  = "#C0392B"
BORDER_COLOUR = "#C5CDD8"
TEXT_DARK     = "#1A2433"
TEXT_MID      = "#4A5568"
LABEL_FG      = "#FFFFFF"
DEP_ARROW     = "#7A8FA6"

WT_LOGO_URL = (
    "https://woodthilsted.com/wp-content/uploads/2024/12/"
    "Wood-Thilsted_10-Year-Anniverary_High_Res_White-no-border-scaled.png"
)


def _month_ticks(start: date, end: date):
    ticks, y, m = [], start.year, start.month
    while True:
        d = date(y, m, 1)
        if d > end + timedelta(days=31):
            break
        ticks.append(d)
        m += 1
        if m > 12:
            m, y = 1, y + 1
    return ticks


def _load_logo():
    """Fetch WT logo; return None on failure."""
    try:
        from PIL import Image
        import io as _io
        data = urlopen(WT_LOGO_URL, timeout=4).read()
        return Image.open(_io.BytesIO(data))
    except Exception:
        return None


def build_chart(tasks, project_name: str = "Project") -> plt.Figure:
    if not tasks:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "No tasks to display", ha="center", va="center")
        return fig

    n = len(tasks)

    fig = plt.figure(figsize=A3_LANDSCAPE_INCHES, dpi=150)
    fig.patch.set_facecolor(BG_COLOUR)

    # ── Reserve space: title band at top, legend at bottom ───────────────────
    TOP    = 0.90
    BOTTOM = 0.07
    LEFT   = 0.01
    RIGHT  = 0.99

    left_ax  = fig.add_axes([LEFT,  BOTTOM, LEFT_PANEL_FRAC - LEFT - 0.005, TOP - BOTTOM])
    right_ax = fig.add_axes([LEFT_PANEL_FRAC, BOTTOM, RIGHT - LEFT_PANEL_FRAC, TOP - BOTTOM])

    for ax in (left_ax, right_ax):
        ax.set_ylim(-0.5, n - 0.5)
        ax.invert_yaxis()

    # Left panel styling
    for spine in left_ax.spines.values():
        spine.set_visible(False)
    left_ax.set_facecolor(BG_COLOUR)
    left_ax.tick_params(left=False, bottom=False, labelbottom=False)
    left_ax.set_xlim(0, 1)
    left_ax.set_yticks([])

    # ── Date range ────────────────────────────────────────────────────────────
    proj_start = min(t.start_date for t in tasks) - timedelta(days=2)
    proj_end   = max(t.end_date   for t in tasks) + timedelta(days=2)

    right_ax.set_xlim(mdates.date2num(proj_start), mdates.date2num(proj_end))
    right_ax.set_facecolor(BG_COLOUR)
    for spine in right_ax.spines.values():
        spine.set_color(BORDER_COLOUR)
        spine.set_linewidth(0.6)

    # ── Alternating row bands ─────────────────────────────────────────────────
    for i in range(n):
        c = ALT_ROW if i % 2 == 0 else BG_COLOUR
        left_ax.axhspan(i - 0.5, i + 0.5,  color=c, zorder=0)
        right_ax.axhspan(i - 0.5, i + 0.5, color=c, zorder=0)

    # ── Monthly vertical grid lines ───────────────────────────────────────────
    for d in _month_ticks(proj_start, proj_end):
        right_ax.axvline(mdates.date2num(d), color=GRID_COLOUR, linewidth=0.6, zorder=1)

    # ── X-axis (monthly, no rotation, clean) ──────────────────────────────────
    right_ax.xaxis.set_major_locator(mdates.MonthLocator())
    right_ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    right_ax.xaxis.set_tick_params(labelsize=6.5, rotation=0, labelcolor=TEXT_MID, pad=3)
    right_ax.tick_params(axis="y", left=False, labelleft=False)
    right_ax.tick_params(axis="x", which="major", length=3, color=BORDER_COLOUR)

    # Stagger alternate month labels to avoid overlap
    for i, label in enumerate(right_ax.xaxis.get_ticklabels()):
        if i % 2 != 0:
            label.set_y(label.get_position()[1] - 0.04)

    # ── Today line ────────────────────────────────────────────────────────────
    today = date.today()
    if proj_start <= today <= proj_end:
        tn = mdates.date2num(today)
        right_ax.axvline(tn, color=TODAY_COLOUR, linewidth=1.0, linestyle="--", zorder=6)
        right_ax.text(tn + 0.3, -0.42, "Today", color=TODAY_COLOUR,
                      fontsize=6, va="top", fontweight="bold", zorder=7)

    # ── Column layout for left panel ──────────────────────────────────────────
    col_widths = [0.08, 0.46, 0.20, 0.26]   # ID | Name | Dur | Dates
    col_x      = [sum(col_widths[:i]) for i in range(len(col_widths))]
    headers    = ["ID", "Task Name", "Dur.", "Start → End"]

    # Header bar (left)
    left_ax.add_patch(Rectangle((0, -0.5), 1, 0.52,
        facecolor=HEADER_BG, edgecolor="none", zorder=3, clip_on=False))
    for hx, hw, hl in zip(col_x, col_widths, headers):
        left_ax.text(hx + hw / 2, -0.25, hl, ha="center", va="center",
                     fontsize=7, fontweight="bold", color=HEADER_FG, zorder=4)

    # Header bar (right) — thin accent only
    right_ax.add_patch(Rectangle(
        (mdates.date2num(proj_start), -0.5),
        mdates.date2num(proj_end) - mdates.date2num(proj_start), 0.52,
        facecolor=HEADER_BG, edgecolor="none", zorder=3, clip_on=False))

    # ── Draw rows ─────────────────────────────────────────────────────────────
    for i, task in enumerate(tasks):
        hex_col = TASK_COLOURS.get(task.colour, "#144272")

        # Left panel cells
        cell_vals = [
            task.task_id,
            task.name,
            "●" if task.is_milestone else f"{task.duration}d",
            task.start_date.strftime("%d %b") + " → " + task.end_date.strftime("%d %b"),
        ]
        for cx, cw, cv in zip(col_x, col_widths, cell_vals):
            left_ax.text(cx + cw / 2, i, cv,
                         ha="center", va="center", fontsize=6.5,
                         color=TEXT_DARK, fontfamily=FONT_FAMILY, clip_on=True)

        # Right panel bar / milestone
        if task.is_milestone:
            mx = mdates.date2num(task.start_date)
            right_ax.scatter(mx, i, marker="D", s=MILESTONE_SIZE,
                             color=hex_col, zorder=5,
                             edgecolors="white", linewidths=0.8)
        else:
            x0    = mdates.date2num(task.start_date)
            x1    = mdates.date2num(task.end_date)
            width = x1 - x0
            # Sharp rectangle — no rounded corners
            bar = Rectangle((x0, i - BAR_HEIGHT / 2), width, BAR_HEIGHT,
                             facecolor=hex_col, edgecolor="none", zorder=4)
            right_ax.add_patch(bar)
            # Subtle inner highlight
            right_ax.add_patch(Rectangle(
                (x0, i - BAR_HEIGHT / 2), width, BAR_HEIGHT * 0.3,
                facecolor="white", alpha=0.12, edgecolor="none", zorder=5))
            # Text label if bar is wide enough
            if width > 6:
                right_ax.text(x0 + width / 2, i, task.name,
                               ha="center", va="center", fontsize=5.8,
                               color=LABEL_FG, fontweight="bold",
                               clip_on=True, zorder=6)

    # ── Dependency arrows (right-angle connector) ─────────────────────────────
    id_to_task = {t.task_id: (idx, t) for idx, t in enumerate(tasks)}
    for i, task in enumerate(tasks):
        dep = task.dependency.strip() if task.dependency else ""
        if dep and dep in id_to_task:
            src_i, src_task = id_to_task[dep]
            x_src = mdates.date2num(src_task.end_date)
            x_dst = mdates.date2num(task.start_date)
            y_src = src_i
            y_dst = i
            # Right-angle: horizontal then vertical then horizontal
            mid_x = (x_src + x_dst) / 2
            right_ax.plot([x_src, mid_x, mid_x, x_dst],
                          [y_src, y_src, y_dst, y_dst],
                          color=DEP_ARROW, linewidth=0.8,
                          linestyle="-", zorder=3)
            right_ax.annotate("", xy=(x_dst, y_dst),
                               xytext=(x_dst - 0.5, y_dst),
                               arrowprops=dict(arrowstyle="-|>",
                                               color=DEP_ARROW, lw=0.8),
                               zorder=3)

    # ── Vertical separator line ───────────────────────────────────────────────
    fig.add_artist(plt.Line2D(
        [LEFT_PANEL_FRAC, LEFT_PANEL_FRAC], [BOTTOM, TOP],
        transform=fig.transFigure,
        color=BORDER_COLOUR, linewidth=1.0, zorder=10
    ))

    # ── Legend ────────────────────────────────────────────────────────────────
    legend_handles = [
        mpatches.Patch(facecolor=hc, label=nm, edgecolor="none")
        for nm, hc in TASK_COLOURS.items()
    ]
    legend_handles.append(
        plt.scatter([], [], marker="D", color="#555", s=55,
                    label="Milestone", edgecolors="white", linewidths=0.6)
    )
    fig.legend(handles=legend_handles,
               loc="lower center", ncol=len(legend_handles),
               fontsize=6.5, frameon=True, framealpha=0.95,
               edgecolor=BORDER_COLOUR,
               bbox_to_anchor=(0.5, 0.005),
               handlelength=1.4, handleheight=0.9,
               borderpad=0.5)

    # ── Title block ───────────────────────────────────────────────────────────
    # Dark banner at very top
    banner = fig.add_axes([0, TOP, 1, 1 - TOP])
    banner.set_facecolor(HEADER_BG)
    banner.axis("off")

    fig.text(0.38, (TOP + 1) / 2, project_name,
             ha="center", va="center",
             fontsize=13, fontweight="bold", color=HEADER_FG,
             fontfamily=FONT_FAMILY, transform=fig.transFigure)
    fig.text(0.38, TOP + 0.008,
             f"Generated {today.strftime('%d %B %Y')}  ·  {n} tasks  ·  "
             f"{min(t.start_date for t in tasks).strftime('%b %Y')} – "
             f"{max(t.end_date for t in tasks).strftime('%b %Y')}",
             ha="center", va="bottom",
             fontsize=7, color="#8BAED4", fontfamily=FONT_FAMILY,
             transform=fig.transFigure)

    # Logo in banner (top-right)
    logo_img = _load_logo()
    if logo_img is not None:
        logo_ax = fig.add_axes([0.80, TOP + 0.001, 0.18, 1 - TOP - 0.002])
        logo_ax.imshow(np.array(logo_img))
        logo_ax.axis("off")

    return fig


def fig_to_pdf_bytes(fig: plt.Figure) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="pdf", bbox_inches="tight",
                facecolor=fig.get_facecolor())
    buf.seek(0)
    return buf.read()


def fig_to_png_bytes(fig: plt.Figure) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    buf.seek(0)
    return buf.read()
