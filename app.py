"""
CineMindAI — Streamlit UI (fast startup; RAG loads on demand).
"""

import os
import random
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import streamlit as st
from dotenv import load_dotenv

from agent_tools import gather_tool_layer
from prompt_defense import validate_chat_input

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
MOVIES_FILE = BASE_DIR / "movies.txt"
HERO_IMAGE = BASE_DIR / "assets" / "hero_banner.jpg"

MOOD_ICONS = {
    "Action": "💥",
    "Sci-Fi": "🚀",
    "Comedy": "😂",
    "Drama": "🎭",
    "Thriller": "🔪",
    "Horror": "👻",
    "Romance": "💕",
    "Crime": "🕵️",
    "Fantasy": "🐉",
    "Family": "👨‍👩‍👧",
    "Animation": "✨",
    "Adventure": "🗺️",
}

MOOD_PROMPTS = {
    "Action": "Recommend the best action movies in the database and why each is worth watching.",
    "Sci-Fi": "Suggest the best sci-fi films in the database with a short reason for each.",
    "Comedy": "Recommend the funniest comedy films in the database for a feel-good night.",
    "Drama": "Suggest powerful drama films in the database with emotional depth.",
    "Thriller": "List the best thriller and suspense films in the database.",
    "Horror": "Give me top horror picks from the database for a scary movie night.",
    "Romance": "Recommend romantic films from the database for a date night.",
    "Crime": "Recommend crime and mystery films in the database with gripping plots.",
    "Fantasy": "Suggest the best fantasy films in the database with magical or epic worlds.",
    "Family": "What are the best family-friendly movies in the database tonight?",
    "Animation": "Recommend the best animated films in the database for all ages.",
    "Adventure": "Suggest exciting adventure films in the database for an epic watch.",
}

SAMPLE_QUESTIONS = [
    "Recommend action movies",
    "Suggest sci-fi films",
    "Movies similar to Interstellar",
    "Best family movies",
    "Horror movie recommendations",
]

APP_UI_VERSION = "5.7"
BLOCKED_MOODS = frozenset({"Marvel", "DC"})

SIDEBAR_PAGES_BEFORE_LAUNCH = [
    ("launch", "Launch"),
]

SIDEBAR_PAGES_AFTER_LAUNCH = [
    ("pick", "Pick Cine"),
    ("compare", "Compare"),
    ("chat", "Chat"),
    ("library", "Library"),
    ("watchlist", "Watchlist"),
]

POST_LAUNCH_PAGES = frozenset(k for k, _ in SIDEBAR_PAGES_AFTER_LAUNCH)


def get_sidebar_pages() -> List[tuple[str, str]]:
    if ensure_rag_ready():
        return [("dashboard", "Dashboard")] + list(SIDEBAR_PAGES_AFTER_LAUNCH)
    return list(SIDEBAR_PAGES_BEFORE_LAUNCH)


def get_app_features(movie_count: int) -> List[tuple[str, str, str]]:
    return [
        ("🎞️", "Pick Cine", "Choose a mood and get a watchlist in seconds."),
        ("⚖️", "Compare", "Two films, one CineMind verdict."),
        ("💬", "Chat", "Ask anything about movies in plain language."),
        ("📚", "Library", "Search and save from the full catalog."),
    ]


def get_openai_api_key() -> Optional[str]:
    try:
        if "OPENAI_API_KEY" in st.secrets:
            return st.secrets["OPENAI_API_KEY"]
    except Exception:
        pass
    return os.getenv("OPENAI_API_KEY")


def get_movie_titles() -> List[str]:
    return list(load_movie_catalog().keys())


@st.cache_data
def load_movie_catalog() -> Dict[str, dict]:
    catalog: Dict[str, dict] = {}
    raw = MOVIES_FILE.read_text(encoding="utf-8")
    for block in [b.strip() for b in raw.split("\n---\n") if b.strip()]:
        title_m = re.search(r"^Title:\s*(.+)$", block, re.MULTILINE)
        genre_m = re.search(r"^Genre:\s*(.+)$", block, re.MULTILINE)
        desc_m = re.search(r"^Description:\s*(.+)$", block, re.MULTILINE | re.DOTALL)
        if not title_m:
            continue
        title = title_m.group(1).strip()
        catalog[title] = {
            "title": title,
            "genre": genre_m.group(1).strip() if genre_m else "Unknown",
            "description": desc_m.group(1).strip() if desc_m else "",
        }
    return catalog


def get_movie_info(title: str) -> Optional[dict]:
    return load_movie_catalog().get(title)


def get_all_genres() -> List[str]:
    tags = set()
    for m in load_movie_catalog().values():
        for g in m["genre"].split(","):
            tags.add(g.strip())
    return sorted(tags)


def add_to_watchlist(title: str) -> None:
    if title and title not in st.session_state.watchlist:
        st.session_state.watchlist.append(title)


def remove_from_watchlist(title: str) -> None:
    st.session_state.watchlist = [t for t in st.session_state.watchlist if t != title]


def track_suggestions(titles: List[str]) -> None:
    recent = st.session_state.recent_suggestions
    for t in titles:
        if t and t not in recent:
            recent.insert(0, t)
    st.session_state.recent_suggestions = recent[:8]


def ensure_rag_ready() -> bool:
    return bool(st.session_state.get("rag_ready") and st.session_state.get("qa_chain"))


def start_rag(api_key: str) -> None:
    import rag_core

    st.session_state.qa_chain = rag_core.build_rag_chain(api_key)
    st.session_state.rag_ready = True


def reset_rag_state() -> None:
    st.session_state.pop("qa_chain", None)
    st.session_state.rag_ready = False


def enrich_question_for_retrieval(question: str) -> str:
    """Pull mentioned library titles into the query so compare/similar requests retrieve more than one film."""
    catalog = load_movie_catalog()
    mentioned = [t for t in catalog if t.lower() in question.lower()]
    if not mentioned:
        return question
    hints = []
    for title in mentioned[:4]:
        info = catalog[title]
        hints.append(f"{title} ({info['genre']})")
    extra = " | ".join(hints)
    q_lower = question.lower()
    if "compare" in q_lower or " vs " in q_lower or "versus" in q_lower:
        return (
            f"{question}\n\n"
            f"Use facts for: {extra}\n"
            "Pick exactly ONE film as tonight's choice. State the winner in your first sentence and explain why in 3–5 sentences."
        )
    if "similar" in q_lower:
        return f"{question}\n\nAlso retrieve other library films with similar genre or tone to: {extra}"
    return f"{question}\n\nRelevant library films: {extra}"


def ask_cinemind(
    qa_chain, question: str, api_key: Optional[str] = None
) -> tuple[str, list]:
    safe, err = validate_chat_input(question)
    if err:
        return err, []

    tool_layer = ""
    if api_key:
        tool_layer = gather_tool_layer(api_key, safe)
    query = enrich_question_for_retrieval(safe)
    if tool_layer:
        query = (
            f"{query}\n\n[Structured library facts from tools — use only if consistent "
            f"with retrieved context:]\n{tool_layer}"
        )
    result = qa_chain.invoke({"query": query})
    answer = result.get("result", "Sorry, I could not generate a response.").strip()
    return answer, result.get("source_documents", [])


def get_mood_options() -> List[str]:
    """Moods shown in UI — never includes removed franchise labels."""
    return [m for m in MOOD_PROMPTS if m not in BLOCKED_MOODS]


def purge_legacy_session() -> None:
    """Drop cached widget state from older builds (Marvel/DC moods, old UI)."""
    if st.session_state.get("_ui_version") == APP_UI_VERSION:
        mood = st.session_state.get("selected_mood")
        if mood in BLOCKED_MOODS:
            st.session_state.selected_mood = "Action"
        return
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state._ui_version = APP_UI_VERSION


def init_session_state() -> None:
    defaults = {
        "messages": [],
        "pending_question": None,
        "last_spotlight": None,
        "rag_ready": False,
        "qa_chain": None,
        "selected_mood": "Action",
        "page": "dashboard",
        "watchlist": [],
        "recent_suggestions": [],
        "return_after_chat": None,
        "compare_context": None,
        "chat_rec_title": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val
    if st.session_state.get("selected_mood") in BLOCKED_MOODS:
        st.session_state.selected_mood = "Action"
    # migrate old session key
    if "view" in st.session_state and "page" not in st.session_state:
        st.session_state.page = st.session_state.view


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

        html, body, [class*="css"] { font-family: 'Inter', system-ui, sans-serif; }
        .stApp { background: #0a0a0a; }

        #MainMenu, footer { visibility: hidden; }
        [data-testid="stDecoration"] { display: none; }

        /* Keep sidebar visible and reopen control accessible */
        [data-testid="stSidebar"] {
            visibility: visible !important;
        }
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="collapsedControl"],
        button[data-testid="baseButton-headerNoPadding"] {
            visibility: visible !important;
            display: flex !important;
        }
        .block-container { padding-top: 1.5rem; max-width: 920px; }

        [data-testid="stSidebar"] {
            background: #0f0f0f !important;
            border-right: 1px solid #1f1f1f;
            min-width: 16rem;
        }
        [data-testid="stSidebar"] .block-container { padding-top: 1.25rem; }
        [data-testid="stSidebar"] h3 {
            color: #fff !important;
            font-weight: 600 !important;
            font-size: 1.1rem !important;
            -webkit-text-fill-color: #fff !important;
            background: none !important;
        }

        .cine-hero-wrap {
            position: relative;
            border-radius: 16px;
            overflow: hidden;
            margin-bottom: 1.25rem;
            border: 1px solid #3a2020;
            box-shadow: 0 12px 40px rgba(229, 9, 20, 0.15);
        }
        .cine-hero-overlay {
            background: linear-gradient(90deg, rgba(0,0,0,0.92) 0%, rgba(0,0,0,0.5) 55%, rgba(0,0,0,0.2) 100%);
            padding: 2rem 2.25rem;
            margin-top: -6px;
        }
        .cine-logo {
            font-size: 2.75rem;
            font-weight: 800;
            letter-spacing: 0.04em;
            background: linear-gradient(135deg, #ff1a1a 0%, #f5c518 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 0;
            line-height: 1.1;
        }
        .cine-tagline {
            color: #b0b0b0;
            font-size: 1rem;
            margin: 0.35rem 0 0 0;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            font-weight: 600;
        }

        .stat-card {
            background: #141414;
            border: 1px solid #2a2a2a;
            border-radius: 12px;
            padding: 1rem 1.1rem;
            text-align: center;
        }
        .stat-card h3 {
            margin: 0;
            font-size: 1.75rem;
            font-weight: 800;
            color: #f5c518;
        }
        .stat-card p {
            margin: 0.25rem 0 0 0;
            color: #888;
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }

        .panel {
            background: #111;
            border: 1px solid #222;
            border-radius: 8px;
            padding: 1.1rem 1.25rem;
            margin: 1rem 0;
        }
        .panel-title {
            color: #eee;
            font-size: 1rem;
            font-weight: 600;
            margin: 0 0 0.35rem 0;
        }
        .panel-sub { color: #888; font-size: 0.9rem; margin: 0; }

        .spotlight-box {
            background: #111;
            border: 1px solid #222;
            border-radius: 8px;
            padding: 1.1rem 1.25rem;
            margin: 0.5rem 0 1rem 0;
        }
        .spotlight-label {
            color: #666;
            font-size: 0.8rem;
            margin: 0;
        }
        .spotlight-film {
            color: #fff;
            font-size: 1.35rem;
            font-weight: 600;
            margin: 0.25rem 0 0 0;
        }

        .launch-card {
            background: linear-gradient(145deg, #161616, #0f0f0f);
            border: 1px solid #333;
            border-radius: 14px;
            padding: 1.5rem;
            text-align: center;
            height: 100%;
        }
        .launch-card .icon { font-size: 2rem; margin-bottom: 0.5rem; }
        .launch-card h4 { color: #fff; margin: 0.4rem 0; font-size: 1rem; }
        .launch-card p { color: #888; font-size: 0.85rem; margin: 0; }

        div[data-testid="stMetric"] {
            background: #141414;
            border: 1px solid #2a2a2a;
            border-radius: 12px;
            padding: 0.75rem;
        }

        .stButton > button[kind="primary"] {
            background: #e50914 !important;
            border: none !important;
            font-weight: 500 !important;
            border-radius: 8px !important;
            padding: 0.55rem 1rem !important;
        }
        .stButton > button[kind="secondary"] {
            background: transparent !important;
            border: 1px solid #333 !important;
            color: #ccc !important;
            border-radius: 8px !important;
            font-weight: 500 !important;
        }
        .stButton > button:hover { opacity: 0.92; }

        div[data-testid="stChatMessage"] {
            background: #141414 !important;
            border: 1px solid #2a2a2a !important;
            border-radius: 12px !important;
        }

        [data-testid="stImage"] img {
            border-radius: 10px;
            display: block;
            max-height: 280px;
            width: 100%;
            object-fit: cover;
            border: 1px solid #222;
        }

        .vault-tip {
            background: #1a1508;
            border: 1px solid #4a3a10;
            border-radius: 10px;
            padding: 0.75rem 1rem;
            color: #d4c4a0;
            font-size: 0.88rem;
            line-height: 1.45;
            margin: 0.5rem 0 1rem 0;
        }
        .vault-tip strong { color: #f5c518; }

        .reel-help {
            color: #9ca3af;
            font-size: 0.88rem;
            margin: -0.25rem 0 0.75rem 0;
            line-height: 1.5;
        }

        .mood-active {
            display: inline-block;
            color: #aaa;
            font-size: 0.85rem;
            font-weight: 500;
            margin-bottom: 0.5rem;
        }

        .page-header {
            background: #111;
            border: 1px solid #222;
            border-radius: 10px;
            padding: 1.25rem 1.35rem;
            margin-bottom: 1.25rem;
        }
        .page-header h1 {
            margin: 0;
            font-size: 1.5rem;
            font-weight: 600;
            color: #fff;
        }
        .page-header .meta {
            color: #888;
            font-size: 0.9rem;
            margin: 0.35rem 0 0 0;
        }
        .page-header .status { font-size: 0.8rem; margin-top: 0.35rem; }

        .feature-card {
            background: #111;
            border: 1px solid #222;
            border-radius: 8px;
            padding: 0.85rem 1rem;
        }
        .feature-card h4 {
            color: #eee;
            margin: 0 0 0.25rem 0;
            font-size: 0.9rem;
            font-weight: 600;
        }
        .feature-card p {
            color: #777;
            margin: 0;
            font-size: 0.82rem;
            line-height: 1.4;
        }

        div[data-testid="stExpander"] {
            border: 1px solid #4a2020 !important;
            border-radius: 12px !important;
            background: #0f0f0f !important;
        }
        div[data-testid="stExpander"] summary {
            font-weight: 700 !important;
            color: #f5f5f5 !important;
        }

        .nav-hint {
            color: #9ca3af;
            font-size: 0.9rem;
            margin: 0 0 1rem 0;
        }

        .dash-stat {
            background: #111;
            border: 1px solid #222;
            border-radius: 8px;
            padding: 1rem 0.75rem;
            text-align: center;
        }
        .dash-stat .num { font-size: 1.5rem; font-weight: 600; color: #fff; }
        .dash-stat .lbl { color: #666; font-size: 0.75rem; margin-top: 0.25rem; }

        .dash-hero { margin-bottom: 1.5rem; }
        .dash-hero .dash-greet {
            color: #666;
            font-size: 0.85rem;
            margin: 0 0 0.25rem 0;
        }
        .dash-hero .dash-title {
            color: #fff;
            font-size: 1.75rem;
            font-weight: 600;
            margin: 0;
            line-height: 1.25;
        }
        .dash-hero .dash-sub {
            color: #888;
            font-size: 0.95rem;
            margin: 0.5rem 0 0 0;
            line-height: 1.5;
            max-width: 36rem;
        }

        .dash-section-title {
            color: #eee;
            font-size: 0.95rem;
            font-weight: 600;
            margin: 1.5rem 0 0.5rem 0;
        }
        .dash-section-hint {
            color: #666;
            font-size: 0.85rem;
            margin: -0.25rem 0 0.75rem 0;
        }

        .dash-chip {
            background: #111;
            border: 1px solid #222;
            border-radius: 8px;
            padding: 0.6rem 0.8rem;
            margin-bottom: 0.35rem;
        }
        .dash-chip .dc-title { color: #eee; font-size: 0.88rem; font-weight: 500; margin: 0; }
        .dash-chip .dc-genre { color: #666; font-size: 0.78rem; margin: 0.15rem 0 0 0; }

        .simple-note {
            color: #666;
            font-size: 0.88rem;
            margin: 0 0 1rem 0;
            line-height: 1.5;
        }

        .movie-card {
            background: #111;
            border: 1px solid #222;
            border-radius: 8px;
            padding: 0.9rem 1rem;
            margin-bottom: 0.5rem;
        }
        .movie-card h4 { color: #eee; margin: 0 0 0.25rem 0; font-size: 0.95rem; font-weight: 600; }
        .movie-card .genre { color: #666; font-size: 0.78rem; margin-bottom: 0.35rem; }
        .movie-card p { color: #9ca3af; font-size: 0.82rem; margin: 0; line-height: 1.4; }

        .genre-pill {
            display: inline-block;
            background: #1f1f1f;
            border: 1px solid #444;
            color: #ddd;
            padding: 0.3rem 0.65rem;
            border-radius: 999px;
            font-size: 0.78rem;
            margin: 0.15rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )



def get_dashboard_greeting() -> str:
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    if hour < 17:
        return "Good afternoon"
    return "Good evening"


def get_dashboard_featured() -> Optional[dict]:
    title = st.session_state.get("last_spotlight")
    if not title:
        title = st.session_state.get("dash_featured_title")
    if not title:
        catalog = list(load_movie_catalog().values())
        if not catalog:
            return None
        title = random.choice(catalog)["title"]
        st.session_state.dash_featured_title = title
    return get_movie_info(title)


def shuffle_dashboard_featured() -> None:
    catalog = list(load_movie_catalog().values())
    if not catalog:
        return
    pick = random.choice(catalog)
    st.session_state.dash_featured_title = pick["title"]
    st.session_state.last_spotlight = None


def run_launch(api_key: str, button_key: str = "launch_main") -> None:
    if st.button("Launch CineMind", type="primary", use_container_width=True, key=button_key):
        with st.status("Loading your movie library…", expanded=True) as status:
            st.write("Preparing recommendations...")
            st.write("Indexing films...")
            try:
                start_rag(api_key)
                status.update(label="Ready!", state="complete")
                st.balloons()
                st.session_state.page = "dashboard"
                st.rerun()
            except Exception as e:
                status.update(label="Launch failed", state="error")
                st.error(str(e))
                st.exception(e)
                reset_rag_state()


def render_offline_welcome(api_key: str, movie_count: int) -> None:
    render_dashboard_hero(False)
    if HERO_IMAGE.exists():
        st.image(str(HERO_IMAGE), use_container_width=True)
    st.markdown(
        '<p class="simple-note">First launch takes about 1–2 minutes to load your film library. '
        "Then Pick Cine, Compare, Chat, and Library unlock.</p>",
        unsafe_allow_html=True,
    )
    run_launch(api_key, "launch_dashboard")


def render_dashboard_hero(online: bool) -> None:
    greet = get_dashboard_greeting()
    if online:
        title = "Pick Cine"
        sub = "CineMindAI is ready — choose a mood, compare two films, or open Chat."
    else:
        title = "CineMindAI"
        sub = "Your AI movie guide. Launch once, then use Pick Cine, Compare, Chat, and Library."
    st.markdown(
        f"""
        <div class="dash-hero">
            <p class="dash-greet">{greet} · CineMindAI</p>
            <h1 class="dash-title">{title}</h1>
            <p class="dash-sub">{sub}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_dashboard_stats() -> None:
    wl = len(st.session_state.watchlist)
    chats = len([m for m in st.session_state.messages if m["role"] == "assistant"])
    moods = len(get_mood_options())
    recent_n = len(st.session_state.recent_suggestions)
    stats = [
        (str(wl), "Watchlist"),
        (str(chats), "Chat replies"),
        (str(moods), "Moods"),
        (str(recent_n), "Recent picks"),
    ]
    cols = st.columns(4)
    for col, (num, lbl) in zip(cols, stats):
        with col:
            st.markdown(
                f'<div class="dash-stat"><div class="num">{num}</div>'
                f'<div class="lbl">{lbl}</div></div>',
                unsafe_allow_html=True,
            )


def render_dashboard_actions() -> None:
    st.markdown('<p class="dash-section-title">Pages</p>', unsafe_allow_html=True)
    pages = [
        ("pick", "🎞️ Pick Cine"),
        ("compare", "⚖️ Compare"),
        ("chat", "💬 Chat"),
        ("library", "📚 Library"),
        ("watchlist", "⭐ Watchlist"),
    ]
    cols = st.columns(5)
    for col, (page, label) in zip(cols, pages):
        with col:
            if st.button(label, key=f"dash_go_{page}", use_container_width=True):
                st.session_state.page = page
                st.rerun()


def render_page_header(movie_count: int, online: bool) -> None:
    status = "Ready" if online else "Not loaded yet"
    status_color = "#4ade80" if online else "#fbbf24"
    st.markdown(
        f"""
        <div class="page-header">
            <h1>🎬 CineMindAI</h1>
            <p class="meta">Your personal movie guide</p>
            <p class="status" style="color:{status_color};">● {status}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_cinema_showcase(movie_count: int, online: bool, expanded: bool = True) -> None:
    """Banner + feature grid inside an expander (what 'Show cinema banner' was meant to be)."""
    status_note = (
        "Vault is live — expand anytime to review what CineMind can do."
        if online
        else "Vault is offline — browse features below, then launch when ready."
    )
    with st.expander("🎬 Cinema showcase — banner & features", expanded=expanded):
        st.caption(status_note)
        if HERO_IMAGE.exists():
            st.image(str(HERO_IMAGE), use_container_width=True)
        st.markdown(
            """
            <p style="color:#b0b0b0;font-size:0.9rem;margin:0.5rem 0 1rem 0;text-transform:uppercase;letter-spacing:0.1em;font-weight:600;">
            Your personal movie guide — powered by CineMindAI
            </p>
            """,
            unsafe_allow_html=True,
        )
        features = get_app_features(movie_count)
        for row_start in range(0, len(features), 3):
            row = features[row_start : row_start + 3]
            cols = st.columns(len(row))
            for col, (icon, title, desc) in zip(cols, row):
                with col:
                    st.markdown(
                        f"""
                        <div class="feature-card">
                            <div class="feature-icon">{icon}</div>
                            <h4>{title}</h4>
                            <p>{desc}</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )


def render_hero_block(movie_count: int, online: bool, compact: bool = False) -> None:
    if HERO_IMAGE.exists() and not compact:
        st.image(str(HERO_IMAGE), use_container_width=True)
    status = "VAULT ONLINE" if online else "VAULT OFFLINE"
    status_color = "#4ade80" if online else "#fbbf24"
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(90deg, #120000 0%, #161616 50%, #121000 100%);
            border: 1px solid #3a2020;
            border-radius: 0 0 14px 14px;
            padding: 1.25rem 1.75rem;
            margin-top: -4px;
            margin-bottom: 1.25rem;
        ">
            <span style="font-size:2.4rem;font-weight:800;background:linear-gradient(90deg,#ff2a2a,#f5c518);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">CineMindAI</span>
            <p style="margin:0.35rem 0 0 0;color:#9ca3af;font-size:0.9rem;">Your personal movie guide</p>
            <p style="margin:0.5rem 0 0 0;font-size:0.75rem;color:{status_color};font-weight:700;">● {status}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )



def render_movie_card(movie: dict, key_prefix: str = "", return_page: Optional[str] = None) -> None:
    desc = movie["description"]
    if len(desc) > 180:
        desc = desc[:180] + "..."
    st.markdown(
        f"""<div class="movie-card">
            <h4>{movie['title']}</h4>
            <p class="genre">{movie['genre']}</p>
            <p>{desc}</p>
        </div>""",
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Add to watchlist", key=f"{key_prefix}_wl_{movie['title']}", use_container_width=True):
            add_to_watchlist(movie["title"])
            st.toast(f"Added {movie['title']}")
    with c2:
        if st.button("Ask CineMind", key=f"{key_prefix}_ask_{movie['title']}", use_container_width=True):
            st.session_state.pending_question = (
                f"Tell me about '{movie['title']}' and suggest 3 similar films from the database."
            )
            if return_page:
                st.session_state.return_after_chat = return_page
                st.session_state.compare_context = None
            st.session_state.page = "chat"
            st.rerun()


def render_library_page() -> None:
    st.markdown("## Browse library")
    catalog = load_movie_catalog()
    c1, c2 = st.columns([2, 1])
    with c1:
        query = st.text_input("Search by title", placeholder="e.g. Inception")
    with c2:
        genre_filter = st.selectbox("Genre", ["All"] + get_all_genres())

    results = []
    for m in catalog.values():
        if query and query.lower() not in m["title"].lower():
            continue
        if genre_filter != "All" and genre_filter.lower() not in m["genre"].lower():
            continue
        results.append(m)
    results.sort(key=lambda x: x["title"])
    st.caption(f"{len(results)} films")

    for m in results[:40]:
        with st.expander(m["title"], expanded=False):
            render_movie_card(m, key_prefix="lib")
    if len(results) > 40:
        st.info("Showing first 40. Refine your search.")


def render_watchlist_page() -> None:
    st.markdown("## My watchlist")
    wl = st.session_state.watchlist
    if not wl:
        st.info("Your watchlist is empty. Add films from Browse library or after a recommendation.")
        if st.button("Browse library"):
            st.session_state.page = "library"
            st.rerun()
        return

    if st.button("Ask CineMind about my watchlist", type="primary"):
        titles = ", ".join(wl)
        st.session_state.pending_question = (
            f"I want to watch these films: {titles}. Rank them for a great movie night and say why."
        )
        st.session_state.page = "chat"
        st.rerun()

    for title in wl:
        info = get_movie_info(title)
        col1, col2 = st.columns([4, 1])
        with col1:
            if info:
                st.markdown(f"**{title}** — {info['genre']}")
            else:
                st.markdown(f"**{title}**")
        with col2:
            if st.button("Remove", key=f"rm_{title}"):
                remove_from_watchlist(title)
                st.rerun()

    if st.button("Clear watchlist"):
        st.session_state.watchlist = []
        st.rerun()


def render_compare_page(movie_count: int, titles: List[str]) -> None:
    render_page_header(movie_count, True)
    st.markdown(
        """
        <div class="panel">
            <p class="panel-title">Compare two films</p>
            <p class="panel-sub">Pick two titles, read the details, then let CineMind recommend which to watch tonight.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        a = st.selectbox("Film A", titles, key="cmp_a")
    with c2:
        b = st.selectbox("Film B", titles, index=min(1, len(titles) - 1), key="cmp_b")

    if a and b and a == b:
        st.warning("Pick two different films to compare.")
        return

    if a and b:
        ia, ib = get_movie_info(a), get_movie_info(b)
        if ia and ib:
            col1, col2 = st.columns(2)
            with col1:
                render_movie_card(ia, "cmp1", return_page="compare")
            with col2:
                render_movie_card(ib, "cmp2", return_page="compare")

        if st.button("Compare with CineMind", type="primary", use_container_width=True):
            st.session_state.pending_question = (
                f"Compare '{a}' and '{b}' using only information from the database. "
                "Pick exactly ONE film I should watch tonight — name the winner first and explain why in 3–5 sentences."
            )
            st.session_state.return_after_chat = "compare"
            st.session_state.compare_context = (a, b)
            st.session_state.page = "chat"
            st.rerun()


def render_dashboard_featured() -> None:
    featured = get_dashboard_featured()
    if not featured:
        return
    label = "Last spotlight" if st.session_state.get("last_spotlight") else "Tonight's inspiration"
    desc = featured["description"]
    if len(desc) > 200:
        desc = desc[:200] + "..."
    st.markdown(
        f'<p class="dash-section-title">{label}</p>',
        unsafe_allow_html=True,
    )
    hc1, hc2 = st.columns([1.2, 1])
    with hc1:
        st.markdown(
            f"""
            <div class="spotlight-box" style="text-align:left;margin:0;">
                <p class="spotlight-label">{featured['genre']}</p>
                <p class="spotlight-film" style="font-size:1.65rem;text-align:left;">{featured['title']}</p>
                <p style="color:#9ca3af;font-size:0.88rem;margin:0.65rem 0 0 0;line-height:1.45;">{desc}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with hc2:
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        if st.button("Random", use_container_width=True, key="dash_shuffle"):
            shuffle_dashboard_featured()
            st.rerun()
        if st.button("🎞️ Pick by mood", type="primary", use_container_width=True, key="dash_to_pick"):
            st.session_state.page = "pick"
            st.rerun()
        if st.button("💬 Ask about this film", use_container_width=True, key="dash_ask_feat"):
            st.session_state.pending_question = (
                f"Tell me about '{featured['title']}' and suggest 3 similar films from the database."
            )
            st.session_state.return_after_chat = "dashboard"
            st.session_state.page = "chat"
            st.rerun()
        if st.button("⭐ Add to watchlist", use_container_width=True, key="dash_wl_feat"):
            add_to_watchlist(featured["title"])
            st.toast(f"Added {featured['title']}")


def render_dashboard(movie_count: int, online: bool, api_key: str) -> None:
    if online:
        render_dashboard_hero(online)
        render_dashboard_stats()
        render_dashboard_featured()
        render_dashboard_actions()

        st.markdown('<p class="dash-section-title">Quick mood</p>', unsafe_allow_html=True)
        moods = get_mood_options()
        for row_start in range(0, min(12, len(moods)), 6):
            row = moods[row_start : row_start + 6]
            mcols = st.columns(len(row))
            for col, mood in zip(mcols, row):
                with col:
                    icon = MOOD_ICONS.get(mood, "🎬")
                    if st.button(f"{icon} {mood}", key=f"dash_{mood}", use_container_width=True):
                        st.session_state.selected_mood = mood
                        st.session_state.page = "pick"
                        st.rerun()

        recent = st.session_state.recent_suggestions
        if recent:
            st.markdown(
                '<p class="dash-section-title">Recently suggested</p>',
                unsafe_allow_html=True,
            )
            rcols = st.columns(min(len(recent), 4))
            for col, title in zip(rcols, recent[:4]):
                info = get_movie_info(title)
                genre = info["genre"] if info else ""
                with col:
                    st.markdown(
                        f"""
                        <div class="dash-chip">
                            <p class="dc-title">{title}</p>
                            <p class="dc-genre">{genre}</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    if st.button("Ask CineMind", key=f"rec_{title}", use_container_width=True):
                        st.session_state.pending_question = f"Why should I watch '{title}'?"
                        st.session_state.return_after_chat = "dashboard"
                        st.session_state.page = "chat"
                        st.rerun()
    else:
        render_offline_welcome(api_key, movie_count)

def render_launch_page(api_key: str, movie_count: int) -> None:
    render_offline_welcome(api_key, movie_count)


def render_page_gate() -> bool:
    if ensure_rag_ready():
        return True
    st.warning("Launch CineMind from the Dashboard first.")
    if st.button("🏠 Go to Dashboard", type="primary"):
        st.session_state.page = "dashboard"
        st.rerun()
    return False



def render_reel_studio(titles: List[str]) -> None:
    st.subheader("What are you in the mood for?")

    mood_cols = st.columns(4)
    moods = get_mood_options()
    selected_mood = st.session_state.get("selected_mood", moods[0])
    if selected_mood not in moods:
        selected_mood = moods[0]
        st.session_state.selected_mood = selected_mood

    for i, mood in enumerate(moods):
        with mood_cols[i % 4]:
            icon = MOOD_ICONS.get(mood, "🎬")
            if st.button(f"{icon} {mood}", key=f"mood_{mood}", use_container_width=True):
                st.session_state.selected_mood = mood

    selected_mood = st.session_state.get("selected_mood", moods[0])
    icon = MOOD_ICONS.get(selected_mood, "🎬")
    st.markdown(
        f'<p class="mood-active">{icon} {selected_mood}</p>',
        unsafe_allow_html=True,
    )

    anchor = st.selectbox("Similar to a film you like (optional)", ["— none —"] + titles)

    b1, b2 = st.columns([2, 1])
    with b1:
        if st.button("Pick Cine", type="primary", use_container_width=True):
            q = MOOD_PROMPTS[selected_mood]
            if anchor != "— none —":
                q += f" Include films similar to '{anchor}'."
            st.session_state.pending_question = q
            st.session_state.return_after_chat = "pick"
            st.session_state.compare_context = None
            st.session_state.page = "chat"
            st.rerun()
    with b2:
        if st.button("Random", use_container_width=True):
            pick = random.choice(titles)
            st.session_state.pending_question = (
                f"Describe '{pick}' and recommend 3 similar films from the database."
            )
            st.session_state.return_after_chat = "pick"
            st.session_state.compare_context = None
            st.session_state.page = "chat"
            st.rerun()


def get_chat_recommendation() -> Optional[dict]:
    title = st.session_state.get("last_spotlight")
    if not title and st.session_state.recent_suggestions:
        title = st.session_state.recent_suggestions[0]
    if not title:
        title = st.session_state.get("chat_rec_title")
    if not title:
        catalog = list(load_movie_catalog().values())
        if not catalog:
            return None
        title = random.choice(catalog)["title"]
        st.session_state.chat_rec_title = title
    return get_movie_info(title)


def render_chat_recommendation() -> None:
    movie = get_chat_recommendation()
    if not movie:
        return
    title = movie["title"]
    desc = movie.get("description", "")
    if len(desc) > 200:
        desc = desc[:200] + "..."
    st.markdown(
        f"""
        <div class="spotlight-box" style="text-align:left;margin-bottom:0.75rem;">
            <p class="spotlight-label">Recommendation</p>
            <p class="spotlight-film" style="font-size:1.5rem;text-align:left;">{title}</p>
            <p style="color:#888;margin:0.25rem 0 0.5rem 0;font-size:0.82rem;">{movie['genre']}</p>
            <p style="color:#aaa;margin:0;font-size:0.88rem;line-height:1.45;">{desc}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Add to watchlist", key="chat_rec_wl", use_container_width=True):
            add_to_watchlist(title)
            st.toast(f"Added {title}")
    with c2:
        if st.button("Ask about this", key="chat_rec_ask", use_container_width=True):
            st.session_state.pending_question = (
                f"Tell me about '{title}' and suggest 3 similar films from the database."
            )
            st.rerun()


def render_spotlight(title: Optional[str]) -> None:
    if not title:
        return
    info = get_movie_info(title)
    genre = info["genre"] if info else ""
    st.markdown(
        f"""
        <div class="spotlight-box">
            <p class="spotlight-label">Recommendation</p>
            <p class="spotlight-film">{title}</p>
            <p style="color:#888;margin:0.35rem 0 0 0;font-size:0.85rem;">{genre}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if info and info.get("description"):
        st.caption(info["description"][:220] + ("..." if len(info["description"]) > 220 else ""))
    if st.button("Add to watchlist", key=f"spot_wl_{title}"):
        add_to_watchlist(title)
        st.toast(f"Added {title}")


def render_chat(qa_chain) -> None:
    st.subheader("Chat with CineMind")
    render_chat_recommendation()

    if not st.session_state.messages:
        st.caption("Try a starter below or type your own question.")
        chip_cols = st.columns(len(SAMPLE_QUESTIONS))
        for col, q in zip(chip_cols, SAMPLE_QUESTIONS):
            with col:
                if st.button(q, key=f"chip_{q}", use_container_width=True):
                    st.session_state.pending_question = q
                    st.rerun()

    for msg in st.session_state.messages:
        avatar = "🍿" if msg["role"] == "user" else "🎬"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    user_text = st.session_state.pending_question
    if user_text:
        st.session_state.pending_question = None

    if prompt := st.chat_input("What do you want to watch?"):
        user_text = prompt

    if user_text:
        st.session_state.messages.append({"role": "user", "content": user_text})
        with st.spinner("Finding movies for you…"):
            try:
                answer, sources = ask_cinemind(
                    qa_chain, user_text, get_openai_api_key()
                )
                src_titles = []
                for doc in sources:
                    t = doc.metadata.get("title")
                    if t and t not in src_titles:
                        src_titles.append(t)
                if src_titles:
                    refs = " · ".join(src_titles[:5])
                    answer += f"\n\n*Films from your library in this reply:* {refs}"
                track_suggestions(src_titles)
                if src_titles:
                    st.session_state.last_spotlight = src_titles[0]
                    st.session_state.chat_rec_title = src_titles[0]
                else:
                    st.session_state.last_spotlight = None
            except Exception as e:
                answer = f"⚠️ Something went wrong: {e}"
                st.session_state.last_spotlight = None
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.rerun()


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("### CineMindAI")
        st.caption("Pick Cine · powered by CineMindAI")
        st.divider()
        st.markdown("##### Pages")
        page = st.session_state.get("page", "dashboard")
        for key, label in get_sidebar_pages():
            if st.button(
                label,
                use_container_width=True,
                type="primary" if page == key else "secondary",
                key=f"nav_{key}",
            ):
                st.session_state.page = key
                if key != "chat":
                    st.session_state.return_after_chat = None
                    st.session_state.compare_context = None
                st.rerun()

        if not ensure_rag_ready():
            st.caption("Launch to unlock all pages.")

        wl_n = len(st.session_state.get("watchlist", []))
        if wl_n:
            st.caption(f"Watchlist · {wl_n}")
        st.divider()
        st.markdown("##### Controls")
        if ensure_rag_ready() and st.button("Clear chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.last_spotlight = None
            st.rerun()
        if st.button("Reset app", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


def run_app() -> None:
    inject_styles()
    purge_legacy_session()
    init_session_state()

    if st.session_state.get("rag_ready") and not st.session_state.get("qa_chain"):
        reset_rag_state()

    render_sidebar()

    api_key = get_openai_api_key()
    if not api_key or api_key.strip() in ("", "your_api_key_here"):
        st.error("⚠️ OpenAI API key required")
        st.markdown(
            """
            **Local:** add `OPENAI_API_KEY` to your `.env` file.

            **Streamlit Cloud:** open **Manage app → Settings → Secrets** and add:

            ```toml
            OPENAI_API_KEY = "sk-your-key-here"
            ```
            """
        )
        st.stop()

    if not MOVIES_FILE.exists():
        st.error("Missing `movies.txt` in the repository.")
        st.stop()

    movie_count = len(get_movie_titles())
    online = ensure_rag_ready()
    page = st.session_state.get("page", "dashboard")

    if not online and page in POST_LAUNCH_PAGES:
        st.session_state.page = "dashboard"
        page = "dashboard"

    if online and page == "launch":
        st.session_state.page = "dashboard"
        page = "dashboard"

    if page == "dashboard":
        render_dashboard(movie_count, online, api_key)
    elif page == "launch":
        render_launch_page(api_key, movie_count)
    elif page == "pick":
        if render_page_gate():
            render_reel_studio(get_movie_titles())
    elif page == "compare":
        if render_page_gate():
            render_compare_page(movie_count, get_movie_titles())
    elif page == "library":
        if render_page_gate():
            render_library_page()
    elif page == "watchlist":
        if render_page_gate():
            render_watchlist_page()
    elif page == "chat":
        if render_page_gate():
            render_chat(st.session_state.qa_chain)


# =============================================================================
# Main app flow
# =============================================================================
st.set_page_config(
    page_title="CineMindAI",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

try:
    run_app()
except Exception as exc:
    st.error("CineMindAI failed to start")
    st.exception(exc)
    st.info(
        "If this is on Streamlit Cloud: check **Secrets** (`OPENAI_API_KEY`), "
        "then **Manage app → Logs**. Redeploy after updating `requirements.txt`."
    )
