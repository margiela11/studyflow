import sqlite3
from contextlib import contextmanager
from pathlib import Path

import streamlit as st


# ==========================================
# 1. SETTINGS AND DATABASE
# ==========================================

DB_PATH = Path(__file__).parent / "studyflow.db"


@contextmanager
def database_connection():
    """Open, commit or roll back, and always close a database connection."""
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Create the tasks table if it does not exist yet."""
    with database_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                subject TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0
            )
            """
        )


def migrate_old_tasks():
    """Move tasks from the old session-state list into an empty database."""
    old_tasks = st.session_state.get("tasks", [])
    if not old_tasks:
        return

    with database_connection() as conn:
        task_count = conn.execute(
            "SELECT COUNT(*) FROM tasks"
        ).fetchone()[0]

        if task_count == 0:
            for task in old_tasks:
                conn.execute(
                    """
                    INSERT INTO tasks (title, subject, done)
                    VALUES (?, ?, ?)
                    """,
                    (
                        task["title"],
                        task["subject"],
                        int(task.get("done", False)),
                    ),
                )


def add_task(title, subject):
    """Add a task and return its database ID."""
    with database_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO tasks (title, subject, done)
            VALUES (?, ?, 0)
            """,
            (title, subject),
        )
        return cursor.lastrowid


def get_tasks():
    """Return all tasks as dictionaries, newest first."""
    with database_connection() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, title, subject, done
            FROM tasks
            ORDER BY id DESC
            """
        ).fetchall()

    tasks = []
    for row in rows:
        task = dict(row)
        task["done"] = bool(task["done"])
        tasks.append(task)

    return tasks


def update_task(task_id, done):
    """Update the completion status of a task."""
    with database_connection() as conn:
        conn.execute(
            "UPDATE tasks SET done = ? WHERE id = ?",
            (int(done), task_id),
        )


def delete_task(task_id):
    """Delete a task from the database."""
    with database_connection() as conn:
        conn.execute(
            "DELETE FROM tasks WHERE id = ?",
            (task_id,),
        )


# ==========================================
# 2. APP INITIALIZATION
# ==========================================

st.set_page_config(
    page_title="StudyFlow",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed",
)

init_db()
migrate_old_tasks()

PAGES = ["Обзор", "Мои задачи", "Предметы", "Статистика"]
st.session_state.setdefault("page", PAGES[0])


def go_to(page_name):
    """Callback for hero buttons: switch the top navigation."""
    st.session_state["page"] = page_name


# ==========================================
# 3. DESIGN: BLACK + NEON GREEN (HERO STYLE)
# ==========================================

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');

    :root {
        --green: #3CFF5E;
        --green-glow: rgba(60, 255, 94, 0.45);
        --bg: #030303;
        --card: #0B0B0C;
        --card-border: #1E1E20;
        --gray-btn: #2B2B2E;
        --text-soft: #D6D6D6;
    }

    /* ---------- Base ---------- */
    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"] {
        background:
            radial-gradient(circle at 85% 15%, rgba(60, 255, 94, 0.10), transparent 40%),
            radial-gradient(circle at 10% 90%, rgba(60, 255, 94, 0.05), transparent 35%),
            var(--bg) !important;
        color: #FFFFFF !important;
    }

    .stApp, .stApp button, .stApp input, .stApp textarea,
    .stApp p, .stApp label, .stApp span, .stApp h1, .stApp h2, .stApp h3 {
        font-family: "Outfit", "Inter", sans-serif !important;
    }

    header[data-testid="stHeader"] {
        background: transparent !important;
    }

    /* Hide the sidebar: navigation is on top now */
    [data-testid="stSidebar"],
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"] {
        display: none !important;
    }

    .block-container {
        max-width: 1200px;
        padding-top: 1.5rem;
        padding-bottom: 4rem;
    }

    /* ---------- Top bar ---------- */
    .logo {
        font-size: 26px;
        font-weight: 800;
        letter-spacing: -0.5px;
        color: #FFFFFF;
        line-height: 1.1;
        padding-top: 6px;
    }
    .logo span {
        color: var(--green);
        text-shadow: 0 0 14px var(--green-glow);
    }

    /* Navigation (horizontal radio) looks like plain links */
    [data-testid="stRadio"] [role="radiogroup"] {
        justify-content: flex-end;
        gap: 6px;
    }
    [data-testid="stRadio"] label {
        background: transparent !important;
        border: none !important;
        padding: 6px 14px !important;
        border-radius: 999px !important;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    [data-testid="stRadio"] label > div:first-child {
        display: none !important;  /* hide the radio circle */
    }
    [data-testid="stRadio"] label p {
        font-size: 15px !important;
        font-weight: 500 !important;
        color: #FFFFFF !important;
        margin: 0 !important;
    }
    [data-testid="stRadio"] label:hover p {
        color: var(--green) !important;
    }
    [data-testid="stRadio"] label:has(input:checked) {
        background: rgba(60, 255, 94, 0.10) !important;
        box-shadow: 0 0 14px rgba(60, 255, 94, 0.18);
    }
    [data-testid="stRadio"] label:has(input:checked) p {
        color: var(--green) !important;
    }

    /* ---------- Hero ---------- */
    .hero {
        padding: 5rem 0 1.5rem 0;
    }
    .hero.small {
        padding: 3rem 0 1rem 0;
    }
    .eyebrow {
        color: var(--green);
        font-size: 13px;
        font-weight: 600;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 1.2rem;
    }
    .hero-title {
        color: #FFFFFF;
        font-size: clamp(42px, 7vw, 76px);
        font-weight: 700;
        line-height: 1.05;
        letter-spacing: -1.5px;
        margin: 0 0 1.6rem 0;
    }
    .hero.small .hero-title {
        font-size: clamp(36px, 5vw, 56px);
        margin-bottom: 1rem;
    }
    .hero-text {
        color: var(--text-soft);
        font-size: 18px;
        font-weight: 300;
        line-height: 1.8;
        max-width: 560px;
    }

    /* ---------- Typography elsewhere ---------- */
    h2, h3, [data-testid="stHeading"] h2, [data-testid="stHeading"] h3 {
        color: #FFFFFF !important;
        font-weight: 600 !important;
        letter-spacing: -0.5px;
    }
    .stMarkdown p {
        color: var(--text-soft);
    }
    [data-testid="stCaptionContainer"] p {
        color: #8C8C8C !important;
    }
    hr {
        border-color: var(--card-border) !important;
    }

    /* ---------- Buttons: pills ---------- */
    .stButton button,
    .stFormSubmitButton button {
        border-radius: 999px !important;
        padding: 0.85rem 2rem !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        border: none !important;
        transition: all 0.25s ease;
    }

    /* Primary: solid neon green with glow */
    button[kind="primary"],
    button[kind="primaryFormSubmit"],
    [data-testid="stBaseButton-primary"],
    [data-testid="stBaseButton-primaryFormSubmit"] {
        background-color: var(--green) !important;
        color: #000000 !important;
        box-shadow: 0 8px 30px var(--green-glow);
    }
    button[kind="primary"]:hover,
    button[kind="primaryFormSubmit"]:hover,
    [data-testid="stBaseButton-primary"]:hover,
    [data-testid="stBaseButton-primaryFormSubmit"]:hover {
        background-color: #66FF82 !important;
        color: #000000 !important;
        box-shadow: 0 10px 40px rgba(60, 255, 94, 0.65);
        transform: translateY(-1px);
    }

    /* Secondary: dark gray pill with green text */
    button[kind="secondary"],
    [data-testid="stBaseButton-secondary"] {
        background-color: var(--gray-btn) !important;
        color: var(--green) !important;
    }
    button[kind="secondary"]:hover,
    [data-testid="stBaseButton-secondary"]:hover {
        background-color: #3A3A3E !important;
        color: var(--green) !important;
        box-shadow: 0 0 18px rgba(60, 255, 94, 0.20);
    }

    /* Small round delete button inside the task list */
    .task-row button {
        padding: 0.4rem 0.9rem !important;
    }

    /* ---------- Cards ---------- */
    div[data-testid="stMetric"] {
        background: var(--card) !important;
        border: 1px solid var(--card-border) !important;
        border-radius: 24px;
        padding: 24px 26px;
        transition: all 0.25s ease;
    }
    div[data-testid="stMetric"]:hover {
        border-color: rgba(60, 255, 94, 0.55) !important;
        box-shadow: 0 0 24px rgba(60, 255, 94, 0.18);
    }
    div[data-testid="stMetricValue"] {
        color: var(--green) !important;
        font-size: 44px !important;
        font-weight: 700 !important;
        text-shadow: 0 0 16px rgba(60, 255, 94, 0.35);
    }
    div[data-testid="stMetricLabel"] p {
        color: #9A9A9A !important;
        font-size: 15px !important;
    }

    /* ---------- Inputs ---------- */
    .stTextInput input {
        background-color: #0E0E10 !important;
        color: #FFFFFF !important;
        border: 1px solid var(--card-border) !important;
        border-radius: 16px !important;
        padding: 14px 18px !important;
    }
    .stTextInput input:focus {
        border-color: var(--green) !important;
        box-shadow: 0 0 0 1px var(--green), 0 0 18px rgba(60, 255, 94, 0.25) !important;
    }
    [data-baseweb="select"] > div {
        background-color: #0E0E10 !important;
        border: 1px solid var(--card-border) !important;
        border-radius: 16px !important;
    }
    [data-testid="stForm"] {
        background: var(--card);
        border: 1px solid var(--card-border) !important;
        border-radius: 28px;
        padding: 1.8rem;
    }
    [data-testid="stWidgetLabel"] p {
        color: var(--text-soft) !important;
        font-size: 15px !important;
    }

    /* Checkbox */
    [data-testid="stCheckbox"] input {
        accent-color: var(--green);
    }
    [data-testid="stCheckbox"] label p {
        font-size: 17px !important;
        color: #FFFFFF !important;
    }

    /* ---------- Kill the remaining blue ---------- */
    :root, .stApp {
        --primary-color: #3CFF5E !important;
    }

    /* Nav: hide the radio circles for good */
    [data-testid="stRadio"] label[data-baseweb="radio"] > div:first-child,
    [data-testid="stRadio"] [data-baseweb="radio"] > div:first-child {
        display: none !important;
    }

    /* Selectbox: dark field, green focus, white text */
    [data-baseweb="select"] > div,
    [data-baseweb="select"] > div > div,
    [data-baseweb="select"] div[value] {
        background-color: #0E0E10 !important;
        background-image: none !important;
        color: #FFFFFF !important;
    }
    [data-baseweb="select"] > div:focus-within {
        border-color: var(--green) !important;
        box-shadow: 0 0 0 1px var(--green), 0 0 18px rgba(60, 255, 94, 0.25) !important;
    }
    [data-baseweb="select"] svg {
        fill: var(--green) !important;
    }

    /* Dropdown list */
    [data-baseweb="popover"] ul,
    [data-baseweb="menu"] {
        background-color: #0E0E10 !important;
        border: 1px solid var(--card-border);
        border-radius: 16px !important;
    }
    [data-baseweb="popover"] li {
        background-color: transparent !important;
        color: #FFFFFF !important;
    }
    [data-baseweb="popover"] li:hover,
    [data-baseweb="popover"] li[aria-selected="true"] {
        background-color: rgba(60, 255, 94, 0.14) !important;
        color: var(--green) !important;
    }

    /* Checkbox: green when checked */
    [data-baseweb="checkbox"] > span:first-child {
        border-color: #3A3A3E !important;
        background-color: #0E0E10 !important;
        border-radius: 6px !important;
    }
    [data-baseweb="checkbox"]:has(input:checked) > span:first-child {
        background-color: var(--green) !important;
        border-color: var(--green) !important;
        box-shadow: 0 0 12px var(--green-glow);
    }
    [data-baseweb="checkbox"]:has(input:checked) > span:first-child svg,
    [data-baseweb="checkbox"]:has(input:checked) > span:first-child svg path {
        color: #000000 !important;
        fill: #000000 !important;
        stroke: #000000 !important;
    }

    /* Text inside buttons */
    [data-testid="stBaseButton-primary"] p,
    [data-testid="stBaseButton-primaryFormSubmit"] p,
    button[kind="primary"] p,
    button[kind="primaryFormSubmit"] p {
        color: #000000 !important;
        font-weight: 600 !important;
    }
    [data-testid="stBaseButton-secondary"] p,
    button[kind="secondary"] p {
        color: var(--green) !important;
    }

    /* Links and text selection */
    a { color: var(--green) !important; }
    ::selection { background: rgba(60, 255, 94, 0.35); color: #FFFFFF; }

    /* Progress bar */
    [data-testid="stProgressBar"] > div {
        background-color: #1A1A1C !important;
        border-radius: 999px;
    }
    [data-testid="stProgressBar"] > div > div {
        background-color: var(--green) !important;
        border-radius: 999px;
        box-shadow: 0 0 14px var(--green-glow);
    }

    /* Alerts */
    [data-testid="stAlert"] {
        background-color: var(--card) !important;
        border: 1px solid var(--card-border) !important;
        border-radius: 18px !important;
        color: #FFFFFF !important;
    }
    /* ---------- Mobile version ---------- */
    @media (max-width: 768px) {
        .block-container {
            padding: 1rem 1rem 3rem 1rem !important;
        }

        .logo {
            font-size: 22px;
            padding-top: 0;
        }

        /* Navigation: compact pills that wrap onto 2 rows if needed */
        [data-testid="stRadio"] [role="radiogroup"] {
            justify-content: flex-start;
            flex-wrap: wrap;
            gap: 2px;
        }
        [data-testid="stRadio"] label {
            padding: 6px 12px !important;
        }
        [data-testid="stRadio"] label p {
            font-size: 14px !important;
        }

        /* Hero */
        .hero {
            padding: 2rem 0 0.5rem 0;
        }
        .hero.small {
            padding: 1.5rem 0 0.5rem 0;
        }
        .eyebrow {
            font-size: 11px;
            letter-spacing: 1.5px;
            margin-bottom: 0.8rem;
        }
        .hero-title,
        .hero.small .hero-title {
            font-size: clamp(34px, 11vw, 48px);
            letter-spacing: -1px;
            margin-bottom: 1rem;
        }
        .hero-text {
            font-size: 16px;
            line-height: 1.7;
        }

        /* Buttons: full-width pills */
        .stButton button,
        .stFormSubmitButton button {
            width: 100%;
            padding: 0.8rem 1.4rem !important;
        }

        /* Cards */
        div[data-testid="stMetric"] {
            padding: 16px 20px;
            border-radius: 20px;
        }
        div[data-testid="stMetricValue"] {
            font-size: 34px !important;
        }

        /* Form */
        [data-testid="stForm"] {
            padding: 1.1rem;
            border-radius: 22px;
        }
        .stTextInput input {
            font-size: 16px !important;
        }

        /* Task rows stay in one line: text on the left, trash on the right */
        [data-testid="stHorizontalBlock"]:has(.task-row-marker) {
            flex-wrap: nowrap !important;
            gap: 0.5rem !important;
        }
        [data-testid="stHorizontalBlock"]:has(.task-row-marker) > div {
            min-width: 0 !important;
        }
        [data-testid="stHorizontalBlock"]:has(.task-row-marker) .stButton button {
            padding: 0.5rem 0.6rem !important;
        }
        [data-testid="stCheckbox"] label p {
            font-size: 16px !important;
        }

        h2, h3 {
            font-size: 22px !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def page_header(eyebrow, title, text="", small=False):
    """Big hero-style header: green eyebrow, huge white title, soft text."""
    size = "hero small" if small else "hero"
    text_html = f'<div class="hero-text">{text}</div>' if text else ""
    st.markdown(
        f"""
        <div class="{size}">
            <div class="eyebrow">{eyebrow}</div>
            <div class="hero-title">{title}</div>
            {text_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==========================================
# 4. TOP NAVIGATION
# ==========================================

logo_col, nav_col = st.columns([1, 2])

with logo_col:
    st.markdown(
        '<div class="logo">Study<span>Flow</span></div>',
        unsafe_allow_html=True,
    )

with nav_col:
    page = st.radio(
        "Навигация",
        PAGES,
        horizontal=True,
        key="page",
        label_visibility="collapsed",
    )


# ==========================================
# 5. OVERVIEW PAGE
# ==========================================

if page == "Обзор":
    page_header(
        "Твой личный планировщик учёбы",
        "Учись в потоке,<br>а не в хаосе",
        "StudyFlow — это место, где все твои задачи и предметы под "
        "контролем: добавляй, отмечай выполненное и смотри свой "
        "прогресс.",
    )

    btn1, btn2, _ = st.columns([1, 1, 3])
    with btn1:
        st.button(
            "Мои задачи",
            type="primary",
            use_container_width=True,
            on_click=go_to,
            args=("Мои задачи",),
        )
    with btn2:
        st.button(
            "Статистика",
            use_container_width=True,
            on_click=go_to,
            args=("Статистика",),
        )

    st.write("")
    st.write("")

    tasks = get_tasks()
    total_tasks = len(tasks)
    completed_tasks = sum(task["done"] for task in tasks)
    progress = (
        int(completed_tasks / total_tasks * 100)
        if total_tasks > 0
        else 0
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Всего задач", total_tasks)

    with col2:
        st.metric("Выполнено", completed_tasks)

    with col3:
        st.metric("Прогресс", f"{progress}%")

    st.write("")
    st.progress(progress)
    st.caption(f"Выполнено {progress}% задач")
    st.divider()

    st.subheader("Последние задачи")

    if tasks:
        for task in tasks[:5]:
            status = "✅" if task["done"] else "⬜"
            st.write(
                f"{status} **{task['title']}** — {task['subject']}"
            )
    else:
        st.info("Пока задач нет. Добавь первую!")


# ==========================================
# 6. MY TASKS PAGE
# ==========================================

elif page == "Мои задачи":
    page_header(
        "Задачи",
        "Мои задачи",
        "Управляй своими учебными заданиями.",
        small=True,
    )

    st.subheader("Добавить задачу")

    with st.form("task_form", clear_on_submit=True):
        task_title = st.text_input(
            "Название задачи",
            placeholder="Например: решить 5 задач по информатике",
        )

        subject = st.selectbox(
            "Предмет",
            ["Информатика", "Математика", "Русский язык", "Другое"],
        )

        submitted = st.form_submit_button(
            "Добавить задачу", type="primary"
        )

    if submitted:
        if task_title.strip():
            add_task(task_title.strip(), subject)
            st.success("Задача добавлена!")
        else:
            st.warning("Введите название задачи")

    st.divider()
    st.subheader("Список задач")

    tasks = get_tasks()

    if tasks:
        for task in tasks:
            col_task, col_delete = st.columns([0.85, 0.15])
            task_key = f"task_done_{task['id']}"

            if task_key not in st.session_state:
                st.session_state[task_key] = task["done"]

            with col_task:
                st.markdown(
                    '<span class="task-row-marker"></span>',
                    unsafe_allow_html=True,
                )
                done = st.checkbox(
                    task["title"],
                    key=task_key,
                )

                if done != task["done"]:
                    update_task(task["id"], done)

                st.caption(f"Предмет: {task['subject']}")

            with col_delete:
                if st.button(
                    "🗑️",
                    key=f"delete_{task['id']}",
                    help="Удалить задачу",
                ):
                    delete_task(task["id"])
                    st.session_state.pop(task_key, None)
                    st.rerun()
    else:
        st.info("Пока задач нет. Добавь первую!")


# ==========================================
# 7. SUBJECTS PAGE
# ==========================================

elif page == "Предметы":
    page_header(
        "Предметы",
        "Мои предметы",
        "Прогресс по каждому предмету отдельно.",
        small=True,
    )

    tasks = get_tasks()
    subjects = sorted({task["subject"] for task in tasks})

    if subjects:
        for subject in subjects:
            subject_tasks = [
                task for task in tasks
                if task["subject"] == subject
            ]
            completed = sum(task["done"] for task in subject_tasks)

            st.subheader(subject)
            st.metric(
                "Выполнено",
                f"{completed} / {len(subject_tasks)}",
            )
    else:
        st.info("Сначала добавь несколько задач!")


# ==========================================
# 8. STATISTICS PAGE
# ==========================================

elif page == "Статистика":
    page_header(
        "Статистика",
        "Твой прогресс",
        "Сколько уже сделано и сколько осталось.",
        small=True,
    )

    tasks = get_tasks()
    total = len(tasks)
    completed = sum(task["done"] for task in tasks)
    remaining = total - completed
    progress = (
        int(completed / total * 100)
        if total > 0
        else 0
    )

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Всего задач", total)

    with col2:
        st.metric("Осталось выполнить", remaining)

    st.subheader("Общий прогресс")
    st.progress(progress)
    st.write(f"Выполнено: {progress}%")

    if total > 0 and completed == total:
        st.success("Все задачи выполнены! Отличная работа!")
    elif total == 0:
        st.info("Пока недостаточно данных для статистики.")
