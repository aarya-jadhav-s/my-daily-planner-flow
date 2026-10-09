import json
import uuid
from datetime import date, datetime, time, timedelta
from pathlib import Path

import streamlit as st

# ---------- PAGE CONFIG (must be the first Streamlit call) ----------

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="My Daily Planner",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- CUSTOM DESIGN ----------
st.markdown(
    """
<style>
.stApp { background: #F5F7FB; color: #1E293B; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"] { background: #17243A; }
[data-testid="stSidebar"] * { color: #F1F5F9 !important; }
.block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1250px; }
h1, h2, h3 { color: #17243A; }
.hero {
    background: linear-gradient(120deg, #17243A, #235B63);
    padding: 30px; border-radius: 22px; color: white; margin-bottom: 24px;
}
.hero h1 { color: white; font-size: 36px; margin-bottom: 8px; }
.hero p { color: #DCE8EF; font-size: 16px; margin-bottom: 0; }
.stat-card {
    background: white; border: 1px solid #E4E9F1;
    padding: 20px; border-radius: 16px; min-height: 112px;
}
.stat-label { color: #64748B; font-size: 13px; margin-bottom: 8px; }
.stat-value { color: #17243A; font-size: 27px; font-weight: 700; }
.study-card {
    background: white; border: 1px solid #E2E8F0; border-left: 5px solid #168C86;
    padding: 15px 18px; border-radius: 13px; margin-bottom: 10px;
}
.break-card {
    background: white; border: 1px solid #E4E9F1;
    padding: 12px 18px; border-radius: 12px; margin-bottom: 8px;
}
.study-time { color: #64748B; font-size: 13px; }
.study-name { color: #17243A; font-weight: 650; font-size: 16px; margin-top: 4px; }
div.stButton > button,
[data-testid="stFormSubmitButton"] > button {
    border-radius: 10px; font-weight: 600;
    background: #FFFFFF !important; color: #17243A !important;
    border: 1px solid #CBD5E1 !important;
}
div.stButton > button *, [data-testid="stFormSubmitButton"] > button * { color: #17243A !important; }
div.stButton > button:hover, [data-testid="stFormSubmitButton"] > button:hover {
    border-color: #168C86 !important; background: #E8F5F4 !important;
}
div.stButton > button:disabled { opacity: 0.45; }
[data-testid="stMain"] [data-testid="stWidgetLabel"] * { color: #17243A !important; }
/* Make every button readable (works across Streamlit versions) */
[data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-secondaryFormSubmit"],
[data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primaryFormSubmit"] {
    background: #FFFFFF !important; color: #17243A !important;
    border: 1px solid #CBD5E1 !important; border-radius: 10px; font-weight: 600;
}
[data-testid="stBaseButton-secondary"] *, [data-testid="stBaseButton-secondaryFormSubmit"] *,
[data-testid="stBaseButton-primary"] *, [data-testid="stBaseButton-primaryFormSubmit"] * { color: #17243A !important; }
[data-testid="stBaseButton-secondary"]:hover, [data-testid="stBaseButton-secondaryFormSubmit"]:hover {
    border-color: #168C86 !important; background: #E8F5F4 !important;
}
/* Red delete (X) button */
[class*="st-key-del_"] button, [class*="st-key-del_"] [data-testid="stBaseButton-secondary"] {
    background: #FEF2F2 !important; border: 1px solid #FCA5A5 !important;
}
[class*="st-key-del_"] button *, [class*="st-key-del_"] [data-testid="stBaseButton-secondary"] * {
    color: #DC2626 !important; font-weight: 800;
}
[class*="st-key-del_"] button:hover { background: #FEE2E2 !important; border-color: #DC2626 !important; }
/* Sidebar open / close arrows always visible */
[data-testid="stSidebarCollapseButton"] { opacity: 1 !important; visibility: visible !important; }
[data-testid="stSidebarCollapseButton"] button, [data-testid="stSidebarCollapseButton"] * {
    color: #F1F5F9 !important; fill: #F1F5F9 !important; opacity: 1 !important;
}
[data-testid="stExpandSidebarButton"], [data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"] {
    opacity: 1 !important; visibility: visible !important;
    background: #17243A !important; border-radius: 10px !important;
}
[data-testid="stExpandSidebarButton"] *, [data-testid="collapsedControl"] *,
[data-testid="stSidebarCollapsedControl"] * { color: #F1F5F9 !important; fill: #F1F5F9 !important; opacity: 1 !important; }
[data-testid="stProgressBar"] > div > div { background-color: #168C86; }
</style>
""",
    unsafe_allow_html=True,
)

# ---------- DATA STORAGE (saved in a JSON file, one entry per day) ----------
DATA_FILE = Path("studyflow_data.json")
DEFAULT_TARGET_HOURS = 11.0
DAY_START_HOUR = 5  # times before 5 AM are treated as "after midnight" of the same day


def load_all():
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_all(data):
    DATA_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_day(data, day_key):
    if day_key not in data:
        data[day_key] = {"target": DEFAULT_TARGET_HOURS, "items": []}
    return data[day_key]


# ---------- HELPERS ----------
def to_minutes(t_str):
    h, m = map(int, t_str.split(":"))
    return h * 60 + m


def duration_minutes(start_str, end_str):
    diff = (to_minutes(end_str) - to_minutes(start_str)) % 1440
    return diff


def fmt_time(t_str):
    return datetime.strptime(t_str, "%H:%M").strftime("%I:%M %p").lstrip("0")


def fmt_duration(minutes):
    h, m = divmod(minutes, 60)
    if h and m:
        return f"{h} hr {m} min"
    if h:
        return f"{h} hr"
    return f"{m} min"


def sort_key(item):
    mins = to_minutes(item["start"])
    return mins + 1440 if mins < DAY_START_HOUR * 60 else mins


def hours_text(hours):
    return f"{hours:.1f}".rstrip("0").rstrip(".") + " hrs"


# ---------- LOAD TODAY ----------
data = load_all()
today_key = date.today().isoformat()
day = get_day(data, today_key)
items = sorted(day["items"], key=sort_key)
day["items"] = items

# ---------- SIDEBAR ----------
with st.sidebar:
    st.markdown("# 📚 StudyFlow")
    st.caption("YOUR PERSONAL PRODUCTIVITY SPACE")
    st.divider()

    page = st.radio("NAVIGATION", ["Dashboard", "Daily Timetable"])

    st.divider()
    st.markdown("### 🎯 Daily target")
    new_target = st.number_input(
        "Study / Office work hours today",
        min_value=1.0,
        max_value=20.0,
        value=float(day.get("target", DEFAULT_TARGET_HOURS)),
        step=0.5,
    )
    if new_target != day.get("target"):
        day["target"] = new_target
        save_all(data)
    st.caption("One session at a time. Keep going!")

# ---------- NUMBERS ----------
target_hours = float(day["target"])
study_items = [i for i in items if i["study"]]
planned_hours = sum(duration_minutes(i["start"], i["end"]) for i in study_items) / 60
done_hours = sum(duration_minutes(i["start"], i["end"]) for i in study_items if i["done"]) / 60
percentage = min(done_hours / target_hours, 1.0) if target_hours else 0
completed = sum(1 for i in study_items if i["done"])
total = len(study_items)

# ---------- HERO ----------
st.markdown(
    f"""
<div class="hero">
    <h1>Make today count.</h1>
    <p>{date.today().strftime('%A, %d %B %Y')} · Plan your day, then check off each study / office work session.</p>
</div>
""",
    unsafe_allow_html=True,
)

# ---------- DASHBOARD ----------
if page == "Dashboard":
    st.markdown("## Your daily overview")

    c1, c2, c3, c4 = st.columns(4)
    cards = [
        (c1, "📚 STUDY / OFFICE TARGET", hours_text(target_hours)),
        (c2, "🗓️ PLANNED", hours_text(planned_hours)),
        (c3, "✅ COMPLETED", f"{hours_text(done_hours)} ({completed}/{total})"),
        (c4, "📈 DAILY PROGRESS", f"{percentage:.0%}"),
    ]
    for col, label, value in cards:
        with col:
            st.markdown(
                f"""<div class="stat-card">
                <div class="stat-label">{label}</div>
                <div class="stat-value">{value}</div></div>""",
                unsafe_allow_html=True,
            )

    st.write("")
    st.markdown("### Today's progress")
    st.progress(
        percentage,
        text=f"{hours_text(done_hours)} of {hours_text(target_hours)} done",
    )

    if not study_items:
        st.info(
            "You haven't planned any study / office work sessions yet. "
            "Go to **Daily Timetable** in the sidebar and write today's plan."
        )
    else:
        if planned_hours < target_hours:
            st.warning(
                f"Your planned study / office work time ({hours_text(planned_hours)}) is less than "
                f"your target ({hours_text(target_hours)}). Add more sessions in the timetable."
            )

        st.markdown("### Your study / office work sessions")
        changed = False
        for item in study_items:
            mins = duration_minutes(item["start"], item["end"])
            with st.container(border=True):
                left, right = st.columns([4, 1])
                with left:
                    st.caption(
                        f"🕒 {fmt_time(item['start'])} – {fmt_time(item['end'])}  ·  {fmt_duration(mins)}"
                    )
                    st.markdown(f"**{item['activity']}**")
                with right:
                    checked = st.checkbox("Done", value=item["done"], key=f"done_{item['id']}")
                    if checked != item["done"]:
                        item["done"] = checked
                        changed = True
        if changed:
            save_all(data)
            st.rerun()

        if total and completed == total and done_hours >= target_hours:
            st.success("🎉 Amazing! You've hit your study / office work target for today.")
        elif total and completed == total:
            st.success("🎉 You've checked off every planned session.")

        if st.button("Reset today's checkboxes"):
            for item in items:
                item["done"] = False
                st.session_state.pop(f"done_{item['id']}", None)
            save_all(data)
            st.rerun()

# ---------- TIMETABLE (user writes it themselves) ----------
else:
    st.markdown("## 🗓️ Write your timetable for today")
    st.caption("Add each activity with its start and end time. Tick 'Study / office work' for the ones that count toward your target. Use ✏️ to edit an entry.")

    def time_picker(label, key, default_24):
        """12-hour picker (hour, minute, AM/PM) returning 'HH:MM' in 24-hour form."""
        dh, dm = map(int, default_24.split(":"))
        h12 = (dh % 12) or 12
        minutes = sorted(set(range(0, 60, 5)) | {dm})
        st.markdown(f"**{label}**")
        h_col, m_col, p_col = st.columns(3)
        hour = h_col.selectbox("Hour", list(range(1, 13)), index=h12 - 1,
                               key=f"{key}_h", label_visibility="collapsed")
        minute = m_col.selectbox("Min", minutes, index=minutes.index(dm), key=f"{key}_m",
                                 format_func=lambda m: f"{m:02d}",
                                 label_visibility="collapsed")
        ampm = p_col.selectbox("AM/PM", ["AM", "PM"], index=0 if dh < 12 else 1,
                               key=f"{key}_p", label_visibility="collapsed")
        hour24 = (hour % 12) + (12 if ampm == "PM" else 0)
        return f"{hour24:02d}:{minute:02d}"

    def validate(activity, start_s, end_s, next_day):
        crosses_midnight = to_minutes(end_s) <= to_minutes(start_s)
        if not activity.strip():
            return "Please type what the activity is."
        if start_s == end_s:
            return "Start and end time can't be the same."
        if crosses_midnight and not next_day:
            return (
                f"End time ({fmt_time(end_s)}) is earlier than start time ({fmt_time(start_s)}). "
                "Check AM/PM, or tick 'Ends after midnight' if it really runs into the next day."
            )
        if next_day and not crosses_midnight:
            return "You ticked 'Ends after midnight' but the end time is later than the start time on the same day. Please check AM/PM."
        return None

    # ----- Add form -----
    with st.form("add_item", clear_on_submit=True):
        activity = st.text_input("Activity", placeholder="e.g. Maths revision, or Office project report")
        c1, c2 = st.columns(2)
        with c1:
            start_s = time_picker("Start time", "start", "09:00")
        with c2:
            end_s = time_picker("End time", "end", "11:00")
        o1, o2 = st.columns(2)
        with o1:
            is_study = st.checkbox("Study / office work", value=True)
        with o2:
            next_day = st.checkbox("Ends after midnight (next day)", value=False)
        submitted = st.form_submit_button("➕ Add to timetable")

    if submitted:
        error = validate(activity, start_s, end_s, next_day)
        if error:
            st.error(error)
        else:
            items.append(
                {
                    "id": uuid.uuid4().hex,
                    "start": start_s,
                    "end": end_s,
                    "activity": activity.strip(),
                    "study": is_study,
                    "done": False,
                }
            )
            save_all(data)
            st.rerun()

    # ----- Shortcuts -----
    yesterday_key = (date.today() - timedelta(days=1)).isoformat()
    yesterday_items = data.get(yesterday_key, {}).get("items", [])
    b1, b2, _ = st.columns([1.3, 1, 3])
    with b1:
        if st.button("📋 Copy yesterday's plan", disabled=not yesterday_items):
            day["items"] = [
                {**i, "id": uuid.uuid4().hex, "done": False} for i in yesterday_items
            ]
            st.session_state.pop("editing_id", None)
            save_all(data)
            st.rerun()
    with b2:
        if st.button("🗑️ Clear today", disabled=not items):
            day["items"] = []
            st.session_state.pop("editing_id", None)
            save_all(data)
            st.rerun()

    st.write("")
    if not items:
        st.info("Your timetable is empty. Add your first activity above.")
    else:
        st.markdown(
            f"**Total study / office work time planned: {hours_text(planned_hours)}** (target {hours_text(target_hours)})"
        )
        editing_id = st.session_state.get("editing_id")

        for item in items:
            # ----- Edit mode for this entry -----
            if item["id"] == editing_id:
                with st.form(f"edit_{item['id']}"):
                    st.markdown("**✏️ Editing this entry**")
                    new_activity = st.text_input("Activity", value=item["activity"])
                    e1, e2 = st.columns(2)
                    with e1:
                        new_start = time_picker("Start time", f"e_{item['id']}_start", item["start"])
                    with e2:
                        new_end = time_picker("End time", f"e_{item['id']}_end", item["end"])
                    f1, f2 = st.columns(2)
                    with f1:
                        new_study = st.checkbox("Study / office work", value=item["study"])
                    with f2:
                        new_next_day = st.checkbox(
                            "Ends after midnight (next day)",
                            value=to_minutes(item["end"]) <= to_minutes(item["start"]),
                        )
                    s_col, c_col, _ = st.columns([1, 1, 4])
                    save_clicked = s_col.form_submit_button("💾 Save")
                    cancel_clicked = c_col.form_submit_button("Cancel")

                if cancel_clicked:
                    st.session_state.pop("editing_id", None)
                    st.rerun()
                if save_clicked:
                    error = validate(new_activity, new_start, new_end, new_next_day)
                    if error:
                        st.error(error)
                    else:
                        item["activity"] = new_activity.strip()
                        item["start"] = new_start
                        item["end"] = new_end
                        item["study"] = new_study
                        st.session_state.pop("editing_id", None)
                        save_all(data)
                        st.rerun()
                continue

            # ----- Normal display -----
            mins = duration_minutes(item["start"], item["end"])
            col, edit_btn, del_btn = st.columns([8, 0.7, 0.7])
            with col:
                if item["study"]:
                    st.markdown(
                        f"""<div class="study-card">
                        <div class="study-time">{fmt_time(item['start'])} – {fmt_time(item['end'])} · {fmt_duration(mins)}</div>
                        <div class="study-name">💼 {item['activity']}</div></div>""",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"""<div class="break-card">
                        <span style="color:#64748B;font-size:13px">{fmt_time(item['start'])} – {fmt_time(item['end'])}</span><br>
                        <span style="color:#1E293B;font-weight:600">{item['activity']}</span>
                        <span style="color:#64748B;font-size:13px"> · {fmt_duration(mins)}</span></div>""",
                        unsafe_allow_html=True,
                    )
            with edit_btn:
                if st.button("✏️", key=f"edit_btn_{item['id']}", help="Edit this activity"):
                    st.session_state["editing_id"] = item["id"]
                    st.rerun()
            with del_btn:
                if st.button("✖", key=f"del_{item['id']}", help="Remove this activity"):
                    day["items"] = [i for i in items if i["id"] != item["id"]]
                    if st.session_state.get("editing_id") == item["id"]:
                        st.session_state.pop("editing_id", None)
                    save_all(data)
                    st.rerun()

st.divider()
st.caption("STUDYFLOW  ·  Built with Python and Streamlit")