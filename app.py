# app.py  –  Streamlit Gantt Chart Tool
import streamlit as st
import pandas as pd
from datetime import date, timedelta

from config import PROJECT_COMPLEXITIES, TASK_COLOURS, DEFAULT_COLOUR
from gantt_data import create_project, df_to_tasks, tasks_to_df, resolve_dependencies
from gantt_chart import build_chart, fig_to_pdf_bytes, fig_to_png_bytes

st.set_page_config(
    page_title="Gantt Chart Builder",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    .stApp { background-color: #F4F6F9; }
    .gantt-header {
        background: linear-gradient(135deg, #0A2647 0%, #144272 100%);
        padding: 1.1rem 2rem;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .gantt-header h1 { color:white!important;font-size:1.5rem!important;font-weight:700!important;margin:0!important;letter-spacing:0.02em; }
    .gantt-header p  { color:#A8C4E0!important;font-size:0.82rem!important;margin:0.15rem 0 0 0!important; }
    .card { background:white;border-radius:4px;padding:1.2rem 1.4rem;box-shadow:0 1px 4px rgba(10,38,71,0.08);margin-bottom:1rem;border-left:3px solid #144272; }
    .card h3 { color:#0A2647;font-size:0.95rem;font-weight:600;margin-bottom:0.7rem;text-transform:uppercase;letter-spacing:0.05em; }
    div.stButton > button { border-radius:2px;font-weight:600;font-size:0.85rem;padding:0.45rem 1.2rem;border:none; }
    div.stButton > button[kind="primary"] { background:#144272;color:white; }
    div.stButton > button[kind="primary"]:hover { background:#0A2647; }
    .block-container { padding-top:0rem; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
for k, v in [("tasks",[]),("show_chart",False),("project_name",""),
             ("df_data",None),("project_initialised",False)]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="gantt-header">
  <div>
    <h1>📊 Gantt Chart Builder</h1>
    <p>Create, edit and export professional project timelines</p>
  </div>
  <div>
    <img src="https://woodthilsted.com/wp-content/uploads/2024/12/Wood-Thilsted_10-Year-Anniverary_High_Res_White-no-border-scaled.png"
         style="height:42px;object-fit:contain;" alt="Wood Thilsted">
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 – Project Setup
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="card"><h3>⚙️ Project Setup</h3>', unsafe_allow_html=True)

col_name, col_cplx, col_btn, col_info = st.columns([3, 3, 2, 2])
with col_name:
    project_name_input = st.text_input(
        "Project Name", value=st.session_state.project_name,
        placeholder="e.g. Offshore Wind Farm Phase 2",
        key="project_name_input",
    )
with col_cplx:
    complexity_labels = [o["label"] for o in PROJECT_COMPLEXITIES]
    selected_label = st.selectbox("Project Complexity", options=complexity_labels)
with col_btn:
    st.markdown("<div style='height:1.9rem'></div>", unsafe_allow_html=True)
    create_clicked = st.button("🚀 Create New Project", type="primary", use_container_width=True)
with col_info:
    if st.session_state.tasks:
        st.markdown("<div style='height:1.6rem'></div>", unsafe_allow_html=True)
        st.info(f"**{len(st.session_state.tasks)}** tasks loaded", icon="📋")

if create_clicked:
    task_count = next(o["task_count"] for o in PROJECT_COMPLEXITIES if o["label"] == selected_label)
    st.session_state.project_name = project_name_input.strip() or "Untitled Project"
    tasks = create_project(task_count)
    st.session_state.tasks = tasks
    st.session_state.df_data = tasks_to_df(tasks).to_dict("list")
    st.session_state.show_chart = False
    st.session_state.project_initialised = True
    st.success(f"✅ '{st.session_state.project_name}' created with {task_count} tasks.")

st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 – Task Editor
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.project_initialised and st.session_state.df_data:

    st.markdown('<div class="card"><h3>✏️ Edit Tasks</h3>', unsafe_allow_html=True)
    st.caption(
        "Edit any cell directly. **Duration = 0** marks a Milestone (◆).  "
        "**Dependency**: enter a Task ID (e.g. `T-002`) — pressing *Update Gantt Chart* will cascade dates automatically."
    )

    working_df = pd.DataFrame(st.session_state.df_data)
    colour_options = list(TASK_COLOURS.keys())

    col_config = {
        "ID":         st.column_config.TextColumn("ID", disabled=True, width="small"),
        "Task Name":  st.column_config.TextColumn("Task Name", width="medium"),
        "Duration":   st.column_config.NumberColumn("Duration (days)", min_value=0, max_value=3650, step=1, width="small", help="0 = Milestone"),
        "Start Date": st.column_config.DateColumn("Start Date", width="small", min_value=date(2000,1,1), max_value=date(2100,12,31)),
        "End Date":   st.column_config.DateColumn("End Date", disabled=True, width="small", help="Auto-calculated"),
        "Colour":     st.column_config.SelectboxColumn("Colour", options=colour_options, width="small"),
        "Dependency": st.column_config.TextColumn("Dependency (Task ID)", width="small", help="e.g. T-001"),
    }

    # KEY FIX: fixed widget key + we never re-assign st.session_state.df_data
    # during the same run the editor renders — only on Update button press.
    edited_df = st.data_editor(
        working_df,
        column_config=col_config,
        use_container_width=True,
        num_rows="fixed",
        hide_index=True,
        key="gantt_editor",
    )

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Buttons ───────────────────────────────────────────────────────────────
    st.markdown('<div class="card">', unsafe_allow_html=True)
    btn1, btn2, _ = st.columns([2, 2, 5])

    with btn1:
        update_clicked = st.button("📊 Update Gantt Chart", type="primary", use_container_width=True)

    with btn2:
        if st.session_state.show_chart and st.session_state.tasks:
            fig_pdf = build_chart(st.session_state.tasks, project_name=st.session_state.project_name)
            pdf_bytes = fig_to_pdf_bytes(fig_pdf)
            st.download_button(
                label="⬇️ Export PDF (A3 landscape)",
                data=pdf_bytes,
                file_name=f"gantt_{st.session_state.project_name.replace(' ','_')}_{date.today().isoformat()}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

    st.markdown('</div>', unsafe_allow_html=True)

    if update_clicked:
        # 1. Recompute end dates from start + duration
        for idx, row in edited_df.iterrows():
            start = row["Start Date"]
            if hasattr(start, "date"):
                start = start.date()
            dur = int(row["Duration"])
            edited_df.at[idx, "End Date"] = start if dur == 0 else start + timedelta(days=dur)

        # 2. Build task objects
        tasks = df_to_tasks(edited_df)

        # 3. Cascade finish-to-start dependencies
        tasks = resolve_dependencies(tasks)

        # 4. Persist resolved state and re-render editor with new dates
        st.session_state.df_data = tasks_to_df(tasks).to_dict("list")
        st.session_state.tasks = tasks
        st.session_state.show_chart = True
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 – Chart
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.show_chart and st.session_state.tasks:
    st.markdown('<div class="card"><h3>📈 Gantt Chart</h3>', unsafe_allow_html=True)
    with st.spinner("Rendering…"):
        fig = build_chart(st.session_state.tasks, project_name=st.session_state.project_name)
        png_bytes = fig_to_png_bytes(fig)
    st.image(png_bytes, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

elif not st.session_state.project_initialised:
    st.markdown("""
    <div style="text-align:center;padding:3rem 1rem;color:#94A3B8;">
        <div style="font-size:3rem">📊</div>
        <h3 style="color:#64748B;margin-top:0.5rem">No project loaded</h3>
        <p>Enter a project name, choose a complexity, then click <strong>Create New Project</strong>.</p>
    </div>
    """, unsafe_allow_html=True)
