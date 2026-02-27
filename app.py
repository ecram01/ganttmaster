# app.py  –  Streamlit Gantt Chart Tool
import streamlit as st
import pandas as pd
from datetime import date, timedelta

from config import PROJECT_COMPLEXITIES, TASK_COLOURS, DEFAULT_COLOUR
from gantt_data import create_project, df_to_tasks, tasks_to_df
from gantt_chart import build_chart, fig_to_pdf_bytes, fig_to_png_bytes

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Gantt Chart Builder",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Main background */
    .stApp { background-color: #F7F9FC; }

    /* Top header bar */
    .gantt-header {
        background: linear-gradient(135deg, #1B3A6B 0%, #2A5298 100%);
        padding: 1.2rem 2rem 1rem 2rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    .gantt-header h1 {
        color: white !important;
        font-size: 1.7rem !important;
        font-weight: 700 !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    .gantt-header p {
        color: #B0C4E8 !important;
        font-size: 0.88rem !important;
        margin: 0 !important;
    }

    /* Card panels */
    .card {
        background: white;
        border-radius: 10px;
        padding: 1.2rem 1.4rem;
        box-shadow: 0 1px 6px rgba(27,58,107,0.08);
        margin-bottom: 1rem;
    }
    .card h3 {
        color: #1B3A6B;
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 0.6rem;
    }

    /* Buttons */
    div.stButton > button {
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.88rem;
        padding: 0.45rem 1.2rem;
        border: none;
        transition: opacity 0.15s;
    }
    div.stButton > button:hover { opacity: 0.88; }
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #1B3A6B, #2A5298);
        color: white;
    }

    /* Data editor tweaks */
    .stDataFrame { border-radius: 8px; overflow: hidden; }

    /* Streamlit default padding reduction */
    .block-container { padding-top: 1rem; }

    /* Divider */
    hr { border-color: #DDE3EC; margin: 0.8rem 0; }
</style>
""", unsafe_allow_html=True)

# ── Session state init ────────────────────────────────────────────────────────
if "tasks" not in st.session_state:
    st.session_state.tasks = []
if "show_chart" not in st.session_state:
    st.session_state.show_chart = False
if "edited_df" not in st.session_state:
    st.session_state.edited_df = None

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="gantt-header">
    <div>
        <h1>📊 Gantt Chart Builder</h1>
        <p>Create, edit and export professional project timelines in seconds</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 – Project Setup
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="card"><h3>⚙️ Project Setup</h3>', unsafe_allow_html=True)

setup_col1, setup_col2, setup_col3 = st.columns([3, 2, 2])

with setup_col1:
    complexity_labels = [opt["label"] for opt in PROJECT_COMPLEXITIES]
    selected_label = st.selectbox(
        "Project Complexity",
        options=complexity_labels,
        help="Choose how many tasks to pre-populate your project with."
    )

with setup_col2:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 Create New Project", type="primary", use_container_width=True):
        task_count = next(
            opt["task_count"] for opt in PROJECT_COMPLEXITIES
            if opt["label"] == selected_label
        )
        st.session_state.tasks = create_project(task_count)
        st.session_state.edited_df = tasks_to_df(st.session_state.tasks)
        st.session_state.show_chart = False
        st.success(f"✅ Project created with {task_count} tasks.")

with setup_col3:
    if st.session_state.tasks:
        st.markdown("<br>", unsafe_allow_html=True)
        st.info(f"**{len(st.session_state.tasks)}** tasks loaded", icon="📋")

st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 – Task Editor
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.tasks:
    st.markdown('<div class="card"><h3>✏️ Edit Tasks</h3>', unsafe_allow_html=True)
    st.caption(
        "Edit any field below. Set **Duration = 0** to mark a task as a **Milestone** (◆). "
        "Use the **Dependency** column to enter another Task ID (e.g. `T-001`) to draw a link arrow."
    )

    colour_options = list(TASK_COLOURS.keys())
    df = st.session_state.edited_df.copy()

    # Column configuration for the data editor
    col_config = {
        "ID": st.column_config.TextColumn(
            "ID", disabled=True, width="small"
        ),
        "Task Name": st.column_config.TextColumn(
            "Task Name", width="medium"
        ),
        "Duration": st.column_config.NumberColumn(
            "Duration (days)", min_value=0, max_value=3650,
            step=1, width="small",
            help="Set to 0 for a Milestone"
        ),
        "Start Date": st.column_config.DateColumn(
            "Start Date", width="small",
            min_value=date(2000, 1, 1),
            max_value=date(2100, 12, 31),
        ),
        "End Date": st.column_config.DateColumn(
            "End Date", disabled=True, width="small",
            help="Auto-calculated from Start Date + Duration"
        ),
        "Colour": st.column_config.SelectboxColumn(
            "Colour", options=colour_options, width="medium"
        ),
        "Dependency": st.column_config.TextColumn(
            "Dependency (Task ID)", width="medium",
            help="Enter a Task ID (e.g. T-001) to draw an arrow from that task"
        ),
    }

    edited = st.data_editor(
        df,
        column_config=col_config,
        use_container_width=True,
        num_rows="fixed",
        key="task_editor",
        hide_index=True,
    )

    # Recalculate end dates automatically after each edit
    if edited is not None:
        from datetime import timedelta
        for idx, row in edited.iterrows():
            start = row["Start Date"]
            if hasattr(start, "date"):
                start = start.date()
            dur = int(row["Duration"])
            edited.at[idx, "End Date"] = (
                start if dur == 0 else start + timedelta(days=dur)
            )
        st.session_state.edited_df = edited

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Update chart button ───────────────────────────────────────────────────
    st.markdown('<div class="card">', unsafe_allow_html=True)
    btn_col1, btn_col2, _ = st.columns([2, 2, 4])

    with btn_col1:
        if st.button("📊 Update Gantt Chart", type="primary", use_container_width=True):
            tasks = df_to_tasks(st.session_state.edited_df)
            st.session_state.tasks = tasks
            st.session_state.show_chart = True

    with btn_col2:
        if st.session_state.show_chart and st.session_state.tasks:
            fig = build_chart(st.session_state.tasks)
            pdf_bytes = fig_to_pdf_bytes(fig)
            st.download_button(
                label="⬇️ Export as PDF (A3)",
                data=pdf_bytes,
                file_name=f"gantt_chart_{date.today().isoformat()}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 – Gantt Chart Display
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.show_chart and st.session_state.tasks:
    st.markdown('<div class="card"><h3>📈 Gantt Chart</h3>', unsafe_allow_html=True)

    with st.spinner("Rendering chart…"):
        fig = build_chart(st.session_state.tasks)
        png_bytes = fig_to_png_bytes(fig)

    st.image(png_bytes, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ── Empty state ───────────────────────────────────────────────────────────────
elif not st.session_state.tasks:
    st.markdown("""
    <div style="text-align:center; padding: 3rem 1rem; color: #94A3B8;">
        <div style="font-size:3rem">📊</div>
        <h3 style="color:#64748B; margin-top:0.5rem">No project loaded</h3>
        <p>Select a complexity level above and click <strong>Create New Project</strong> to begin.</p>
    </div>
    """, unsafe_allow_html=True)
