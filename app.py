import streamlit as st
import plotly.graph_objects as go
import time
import base64

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Alexandrei Nash Dinapo | Portfolio",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session State ─────────────────────────────────────────────────────────────
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
if "profile_photo_b64" not in st.session_state:
    st.session_state.profile_photo_b64 = None
if "profile_photo_mime" not in st.session_state:
    st.session_state.profile_photo_mime = None

# ── Theme Variables ───────────────────────────────────────────────────────────
if st.session_state.dark_mode:
    BG          = "#0d0d1a"
    CARD_BG     = "#1a1a2e"
    CARD_BORDER = "rgba(201,168,76,0.25)"
    TEXT        = "#eaeaf5"               # primary text colour
    TEXT_MUTED  = TEXT                      # keep muted text the same as primary so nothing fades out
    HEADING     = "#ffffff"
    SIDEBAR_BG  = "#08080f"
    SIDEBAR_TEXT= "#f0f0f5"              # sidebar always dark so text stays light
    PLOT_TEXT   = "#eaeaf5"
    PLOT_GRID   = "rgba(201,168,76,0.15)"
    QUOTE_BG    = "#1a1a2e"
    QUOTE_TEXT  = "#ddddf5"
    STAT_BG     = "#1a1a2e"
    CONTACT_BG  = "#1a1a2e"
    INPUT_BG    = "#22223a"
    SHADOW      = "rgba(0,0,0,0.4)"
else:
    BG          = "#f5f0eb"
    CARD_BG     = "#ffffff"
    CARD_BORDER = "rgba(201,168,76,0.2)"
    TEXT        = "#1a1a2e"
    TEXT_MUTED  = TEXT                      # keep everything readable rather than muted
    HEADING     = "#1a1a2e"
    SIDEBAR_BG  = "#1a1a2e"
    SIDEBAR_TEXT= "#f0f0f5"              # sidebar remains dark so text stays light
    PLOT_TEXT   = "#1a1a2e"
    PLOT_GRID   = "rgba(26,26,46,0.12)"
    QUOTE_BG    = "#ffffff"
    QUOTE_TEXT  = "#2a2a4e"
    STAT_BG     = "#1a1a2e"
    CONTACT_BG  = "#ffffff"
    INPUT_BG    = "#ffffff"
    SHADOW      = "rgba(0,0,0,0.08)"

GOLD = "#c9a84c"
SKILL_TAG_BG = "#2a2a4a" if st.session_state.dark_mode else "#1a1a2e"

# ── Avatar Helper ─────────────────────────────────────────────────────────────
def avatar_html(size=110, font_size="2rem", border=3):
    if st.session_state.profile_photo_b64:
        return f'<img src="data:{st.session_state.profile_photo_mime};base64,{st.session_state.profile_photo_b64}" style="width:{size}px;height:{size}px;border-radius:50%;object-fit:cover;border:{border}px solid {GOLD};box-shadow:0 4px 20px rgba(0,0,0,0.25);display:block;margin:0 auto;" />'
    else:
        return f'<div style="width:{size}px;height:{size}px;border-radius:50%;background:linear-gradient(135deg,#1a1a2e,{GOLD});margin:0 auto;display:flex;align-items:center;justify-content:center;font-family:Playfair Display,serif;font-size:{font_size};color:#f5f0eb;font-weight:700;border:{border}px solid {GOLD};">AND</div>'

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=DM+Sans:wght@300;400;500&family=DM+Mono&display=swap');

/* ── Base ── */
html, body, [class*="css"] {{
    font-family: 'DM Sans', sans-serif !important;
    color: {TEXT} !important;
}}
.stApp {{
    background: {BG} !important;
}}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {{
    background: {SIDEBAR_BG} !important;
    border-right: 2px solid {GOLD} !important;
}}
section[data-testid="stSidebar"] *,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] div {{
    color: {SIDEBAR_TEXT} !important;
}}

/* ── Main content text — force visibility ── */
.main p, .main li, .main span:not(.skill-tag):not(.hero-badge),
.main label, .block-container p, .block-container li {{
    color: {TEXT} !important;
}}

/* ── Hero ── */
.hero-container {{
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 60%, #0f3460 100%);
    border-radius: 20px;
    padding: 60px 50px;
    /* text must stay light against the dark gradient regardless of theme */
    color: #f5f0eb;
    position: relative;
    overflow: hidden;
    margin-bottom: 30px;
}}
.hero-container::before {{
    content: '';
    position: absolute;
    top: -80px; right: -80px;
    width: 300px; height: 300px;
    background: radial-gradient(circle, rgba(201,168,76,0.3) 0%, transparent 70%);
    border-radius: 50%;
}}
.hero-container::after {{
    content: '';
    position: absolute;
    bottom: -60px; left: -60px;
    width: 220px; height: 220px;
    background: radial-gradient(circle, rgba(201,168,76,0.15) 0%, transparent 70%);
    border-radius: 50%;
}}
.hero-name {{
    font-family: 'Playfair Display', serif !important;
    font-size: 3.4rem;
    font-weight: 700;
    line-height: 1.1;
    margin: 0;
    background: linear-gradient(90deg, #f5f0eb, {GOLD});
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}
.hero-tagline {{
    font-size: 1rem;
    color: {GOLD} !important;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin: 8px 0 20px 0;
    font-weight: 300;
}}
.hero-desc {{
    font-size: 1.05rem;
    /* ensure maximum contrast against dark background */
    color: #ffffff !important;
    text-shadow: 0 0 6px rgba(0,0,0,0.6);
    line-height: 1.7;
    max-width: 600px;
}}
.hero-badge {{
    display: inline-block;
    background: rgba(201,168,76,0.2);
    border: 1px solid {GOLD};
    color: {GOLD} !important;
    border-radius: 50px;
    padding: 6px 18px;
    font-size: 0.82rem;
    letter-spacing: 0.08em;
    margin: 4px;
    font-weight: 500;
}}

/* ── Section headings ── */
.section-heading {{
    font-family: 'Playfair Display', serif !important;
    font-size: 2rem;
    color: {HEADING} !important;
    margin-bottom: 6px;
}}
.section-rule {{
    height: 3px;
    background: linear-gradient(90deg, {GOLD}, transparent);
    border: none;
    margin-bottom: 28px;
}}

/* ── Cards ── */
.card {{
    background: {CARD_BG} !important;
    border-radius: 14px;
    padding: 26px 28px;
    box-shadow: 0 2px 20px {SHADOW};
    border: 1px solid {CARD_BORDER};
    margin-bottom: 16px;
    transition: transform 0.2s, box-shadow 0.2s;
}}
.card:hover {{
    transform: translateY(-3px);
    box-shadow: 0 8px 30px {SHADOW};
}}
.card-title {{
    font-family: 'Playfair Display', serif !important;
    font-size: 1.2rem;
    color: {HEADING} !important;
    font-weight: 700;
    margin-bottom: 4px;
}}
.card-subtitle {{
    font-size: 0.85rem;
    color: {GOLD} !important;
    font-weight: 500;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin-bottom: 10px;
}}
.card-body {{
    font-size: 0.95rem;
    color: {TEXT_MUTED} !important;
    line-height: 1.6;
}}
.card-body p, .card-body strong, .card-body em {{
    color: {TEXT_MUTED} !important;
}}
.card strong {{
    color: {TEXT} !important;
}}

/* ── Skill tags ── */
.skill-tag {{
    display: inline-block;
    background: {SKILL_TAG_BG} !important;
    color: #f0f0f5 !important;
    border-radius: 6px;
    padding: 5px 14px;
    font-size: 0.82rem;
    margin: 4px;
    font-family: 'DM Mono', monospace !important;
    letter-spacing: 0.04em;
}}
.skill-tag.gold {{
    background: {GOLD} !important;
    color: #1a1a2e !important;
}}

/* ── Timeline ── */
.timeline-item {{
    border-left: 2px solid {GOLD};
    padding: 0 0 28px 24px;
    position: relative;
}}
.timeline-item::before {{
    content: '';
    position: absolute;
    left: -7px; top: 4px;
    width: 12px; height: 12px;
    background: {GOLD};
    border-radius: 50%;
}}
.timeline-year {{
    font-family: 'DM Mono', monospace !important;
    font-size: 0.8rem;
    color: {GOLD} !important;
    font-weight: 500;
    margin-bottom: 4px;
}}
.timeline-item .card-title {{
    color: {HEADING} !important;
}}
.timeline-item .card-body {{
    color: {TEXT_MUTED} !important;
}}

/* ── Quote ── */
.quote-block {{
    border-left: 4px solid {GOLD};
    background: {QUOTE_BG} !important;
    border-radius: 0 12px 12px 0;
    padding: 20px 28px;
    margin: 24px 0;
    font-family: 'Playfair Display', serif !important;
    font-style: italic;
    font-size: 1.15rem;
    color: {QUOTE_TEXT} !important;
    line-height: 1.6;
}}

/* ── Stat boxes ── */
.stat-box {{
    background: {STAT_BG} !important;
    border-radius: 14px;
    padding: 28px 20px;
    text-align: center;
    border: 1px solid {CARD_BORDER};
}}
.stat-number {{
    font-family: 'Playfair Display', serif !important;
    font-size: 2.8rem;
    color: {GOLD} !important;
    font-weight: 700;
    line-height: 1;
}}
.stat-label {{
    font-size: 0.82rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: {TEXT} !important;
    margin-top: 6px;
}}

/* ── Contact links ── */
.contact-link {{
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px 20px;
    background: {CONTACT_BG} !important;
    border-radius: 10px;
    margin-bottom: 10px;
    border: 1px solid {CARD_BORDER};
    font-size: 0.95rem;
    color: {TEXT} !important;
    text-decoration: none;
    transition: border-color 0.2s, transform 0.15s;
}}
.contact-link:hover {{
    border-color: {GOLD};
    transform: translateX(4px);
}}
.contact-link span {{
    color: {TEXT} !important;
}}

/* ── Streamlit widget overrides ── */

/* Inputs */
.stTextInput input,
.stTextArea textarea {{
    background: {INPUT_BG} !important;
    color: {TEXT} !important;
    border: 1px solid {CARD_BORDER} !important;
    border-radius: 8px !important;
    caret-color: {GOLD} !important;
}}
.stTextInput input::placeholder,
.stTextArea textarea::placeholder {{
    color: {TEXT_MUTED} !important;
    opacity: 0.7;
}}
.stTextInput input:focus,
.stTextArea textarea:focus {{
    border-color: {GOLD} !important;
    box-shadow: 0 0 0 2px rgba(201,168,76,0.2) !important;
}}
.stTextInput label, .stTextArea label {{
    color: {TEXT} !important;
    font-weight: 500 !important;
}}

/* Selectbox */
.stSelectbox label {{ color: {TEXT} !important; }}
div[data-baseweb="select"] > div {{
    background: {INPUT_BG} !important;
    border-color: {CARD_BORDER} !important;
    color: {TEXT} !important;
}}
div[data-baseweb="select"] span,
div[data-baseweb="select"] div {{
    color: {TEXT} !important;
}}
div[data-baseweb="popover"] > div {{
    background: {CARD_BG} !important;
    border: 1px solid {CARD_BORDER} !important;
}}
div[data-baseweb="popover"] li {{
    background: {CARD_BG} !important;
    color: {TEXT} !important;
}}
div[data-baseweb="popover"] li:hover {{
    background: {GOLD} !important;
    color: #1a1a2e !important;
}}

/* File uploader */
.stFileUploader > div {{
    background: {INPUT_BG} !important;
    border: 1.5px dashed {GOLD} !important;
    border-radius: 10px !important;
}}
.stFileUploader label,
.stFileUploader span,
.stFileUploader p,
.stFileUploader div {{
    color: {TEXT} !important;
}}
.stFileUploader small {{ color: {TEXT_MUTED} !important; }}

/* Checkbox & Toggle */
.stCheckbox label span, .stCheckbox span {{ color: {TEXT} !important; }}
.stToggle label span, .stToggle span {{ color: {TEXT} !important; }}

/* Buttons */
.stButton > button {{
    background: #1a1a2e !important;
    color: #f0f0f5 !important;
    border: 1px solid {GOLD} !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    transition: all 0.2s !important;
}}
.stButton > button:hover {{
    background: {GOLD} !important;
    color: #1a1a2e !important;
    transform: translateY(-1px) !important;
}}
.stButton > button * {{ color: inherit !important; }}

/* Sidebar button */
section[data-testid="stSidebar"] .stButton > button {{
    background: rgba(201,168,76,0.15) !important;
    color: #f0f0f5 !important;
    border: 1px solid rgba(201,168,76,0.5) !important;
}}
section[data-testid="stSidebar"] .stButton > button:hover {{
    background: {GOLD} !important;
    color: #1a1a2e !important;
}}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {{
    background: {CARD_BG} !important;
    border-radius: 10px !important;
    padding: 4px !important;
    gap: 4px !important;
    border: 1px solid {CARD_BORDER} !important;
}}
.stTabs [data-baseweb="tab"] {{
    background: transparent !important;
    color: {TEXT} !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
}}
.stTabs [data-baseweb="tab"] span {{ color: {TEXT} !important; }}
.stTabs [aria-selected="true"] {{
    background: {GOLD} !important;
    color: #1a1a2e !important;
}}
.stTabs [aria-selected="true"] span {{ color: #1a1a2e !important; }}
.stTabs [data-baseweb="tab-border"] {{ display: none !important; }}
.stTabs [data-baseweb="tab-panel"] * {{ color: {TEXT} !important; }}

/* Expander */
div[data-testid="stExpander"] {{
    background: {CARD_BG} !important;
    border-radius: 12px !important;
    border: 1px solid {CARD_BORDER} !important;
}}
div[data-testid="stExpander"] summary,
div[data-testid="stExpander"] summary *,
div[data-testid="stExpander"] p,
div[data-testid="stExpander"] span,
div[data-testid="stExpander"] div,
div[data-testid="stExpander"] label {{
    color: {TEXT} !important;
}}

/* Metrics */
.stMetric {{
    background: {CARD_BG} !important;
    border-radius: 12px !important;
    padding: 16px !important;
    border: 1px solid {CARD_BORDER} !important;
}}
[data-testid="stMetricLabel"] p {{ color: {TEXT_MUTED} !important; }}
[data-testid="stMetricValue"] {{ color: {HEADING} !important; }}
[data-testid="stMetricDelta"] {{ color: {GOLD} !important; }}
[data-testid="stMetricDelta"] * {{ color: {GOLD} !important; }}

/* Progress bar */
.stProgress > div {{
    background: {CARD_BORDER} !important;
    border-radius: 999px !important;
}}
.stProgress > div > div {{
    background: linear-gradient(90deg, #1a1a2e, {GOLD}) !important;
    border-radius: 999px !important;
}}
/* Progress text label */
.stProgress p {{ color: {TEXT} !important; }}

/* Alerts */
.stSuccess, .stWarning, .stInfo, .stError {{
    background: {CARD_BG} !important;
    border-radius: 10px !important;
}}
.stSuccess *, .stWarning *, .stInfo *, .stError * {{
    color: {TEXT} !important;
}}
div[data-testid="stNotification"] {{
    background: {CARD_BG} !important;
    color: {TEXT} !important;
}}
div[data-testid="stNotification"] * {{ color: {TEXT} !important; }}

/* Spinner */
.stSpinner > div {{ border-top-color: {GOLD} !important; }}

footer {{ display: none !important; }}
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    sidebar_avatar = avatar_html(size=90, font_size="1.4rem", border=3)
    st.markdown(f"""
    <div style='text-align:center;padding:20px 0 30px;'>
        {sidebar_avatar}
        <div style='margin-top:12px;font-family:Playfair Display,serif;font-size:1.05rem;
                    font-weight:700;color:#f0f0f5;'>Alexandrei Nash Dinapo</div>
        <div style='font-size:0.72rem;color:{GOLD};letter-spacing:0.1em;
                    text-transform:uppercase;margin-top:4px;'>IT Student · CITU · Aspiring UI/UX Designer</div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio("Navigate",
        ["🏠  Home", "👤  About Me", "💼  Portfolio", "📊  Skills", "🎓  Education", "📬  Contact"],
        label_visibility="collapsed")

    st.markdown("<hr style='border-color:rgba(201,168,76,0.3);margin:16px 0'>", unsafe_allow_html=True)

    dm_label = "☀️  Light Mode" if st.session_state.dark_mode else "🌙  Dark Mode"
    if st.button(dm_label, use_container_width=True):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

    st.markdown(f"<div style='font-size:0.72rem;color:rgba(240,240,245,0.4);text-align:center;margin-top:10px;'>© 2025 Alexandrei Nash Dinapo</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# HOME
# ══════════════════════════════════════════════════════════════════════════════
if page == "🏠  Home":
    st.markdown("""
    <div class="hero-container">
        <p class="hero-tagline">✦ IT Student · CITU · Aspiring UI/UX Designer ✦</p>
        <h1 class="hero-name">Alexandrei Nash Dinapo</h1>
        <p class="hero-desc">
            An Information Technology student at CITU with a dream of becoming a UI/UX Designer.
            I'm passionate about crafting digital experiences that feel intuitive and beautiful —
            while also building real projects through code to sharpen my technical foundation.
        </p>
        <div style="margin-top:28px;">
            <span class="hero-badge">Python</span>
            <span class="hero-badge">JavaScript</span>
            <span class="hero-badge">Java</span>
            <span class="hero-badge">UI/UX Design</span>
            <span class="hero-badge">Figma</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="stat-box"><div class="stat-number">CITU</div><div class="stat-label">University</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="stat-box"><div class="stat-number">13+</div><div class="stat-label">GitHub Repos</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="stat-box"><div class="stat-number">4</div><div class="stat-label">Languages Used</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="stat-box"><div class="stat-number">∞</div><div class="stat-label">Willingness to Learn</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f'<div class="quote-block">"The expert in anything was once a beginner." — Helen Hayes</div>', unsafe_allow_html=True)

    st.markdown(f'<h2 class="section-heading">Featured Projects</h2><hr class="section-rule">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    featured = [
        ("🔐 OAuth2 Integration", "Java · Oct 2025", "Implemented GitHub & Google OAuth2 login flows in Java — token exchange, scopes, and session management."),
        ("📚 PeerLendingLibrary", "JavaScript · Dec 2025", "A peer-to-peer book lending web app letting community members list, borrow, and track books."),
        ("✅ SmartFormValidation", "JavaScript · Dec 2025", "Real-time client-side form validation library with custom rules and clean error messaging."),
    ]
    for col, (title, sub, desc) in zip([col1, col2, col3], featured):
        with col:
            st.markdown(f"""
            <div class="card">
                <div class="card-title">{title}</div>
                <div class="card-subtitle">{sub}</div>
                <div class="card-body">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    with st.expander("📡 What I'm Currently Working On"):
        items = [
            "Building this Streamlit portfolio app (just pushed it to GitHub!)",
            "Expanding SmartFormValidation with more validation rule types",
            "Learning more about React through BeanNotes and side projects",
            "Studying OAuth2 flows and secure authentication patterns",
            "Exploring UI/UX design principles using Figma",
        ]
        for a in items:
            st.markdown(f"<p style='color:{TEXT};margin:4px 0;'>• {a}</p>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ABOUT ME
# ══════════════════════════════════════════════════════════════════════════════
elif page == "👤  About Me":
    st.markdown(f'<h2 class="section-heading">About Me</h2><hr class="section-rule">', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"""
        <div class="card">
            <div class="card-title">My Story</div>
            <div class="card-body">
                <p style="color:{TEXT_MUTED};">Hi! I'm <strong style="color:{TEXT};">Alexandrei Nash Dinapo</strong>, an Information Technology student at
                <strong style="color:{TEXT};">CITU</strong>. My dream is to become a <strong style="color:{TEXT};">UI/UX Designer</strong> — someone who
                bridges the gap between technology and people through thoughtful, beautiful, and intuitive design.</p>
                <p style="margin-top:12px;color:{TEXT_MUTED};">I'm still early in my journey, but I've already worked across
                multiple languages and technologies: Python, JavaScript, Java, and Apex. Each project
                teaches me something new, and I embrace that learning curve as part of growing toward my goal.</p>
                <p style="margin-top:12px;color:{TEXT_MUTED};">I use Figma to explore how digital experiences can be made
                simpler and more human — and every line of code I write brings me closer to understanding
                what makes great design work under the hood.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f'<div class="quote-block">"The expert in anything was once a beginner." — Helen Hayes</div>', unsafe_allow_html=True)

    with col2:
        about_avatar = avatar_html(size=110, font_size="2rem", border=3)
        st.markdown(f"""
        <div class="card" style="text-align:center;">
            <div style="margin-bottom:16px;">{about_avatar}</div>
            <div class="card-title">Alexandrei Nash Dinapo</div>
            <div class="card-subtitle">IT Student · CITU · Aspiring UI/UX Designer</div>
            <div style="font-size:0.88rem;color:{TEXT_MUTED};margin-top:6px;">📍 Cebu, Philippines</div>
            <div style="font-size:0.88rem;color:{TEXT_MUTED};margin-top:4px;">🎓 BS Information Technology</div>
            <div style="font-size:0.88rem;color:{TEXT_MUTED};margin-top:4px;">🌐 Filipino · English</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="card">
            <div class="card-title" style="font-size:1rem;">Interests & Hobbies</div>
            <div style="margin-top:10px;">
                <span class="skill-tag gold">🎨 Design</span>
                <span class="skill-tag gold">🖥️ Coding</span>
                <span class="skill-tag gold">📷 Photography</span>
                <span class="skill-tag gold">🎵 Music</span>
                <span class="skill-tag gold">✏️ Sketching</span>
                <span class="skill-tag gold">🎮 Gaming</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f'<h2 class="section-heading">My Journey</h2><hr class="section-rule">', unsafe_allow_html=True)

    timeline_events = [
        ("Early Years", "Curiosity for Technology 💻", "Grew up curious about computers and how things worked digitally — always drawn to screens and gadgets."),
        ("High School", "First Steps in Design 🎨", "Started experimenting with graphic design tools and simple layouts, building a feel for aesthetics."),
        ("2022", "Enrolled at CITU 🎓", "Began BS Information Technology at CITU. Got introduced to real programming."),
        ("2023", "First Real Projects 💻", "Started building Python projects and exploring web technologies. Discovered a love for problem-solving through code."),
        ("2024", "Expanding Skills 🚀", "Worked on Java apps, OAuth2 integration, JavaScript libraries, and began exploring UI/UX design with Figma."),
        ("2025", "Building & Growing 🌟", "Actively pushing to GitHub, building this portfolio, and leveling up across multiple languages and frameworks."),
    ]
    col1, col2 = st.columns(2)
    for i, (year, title, desc) in enumerate(timeline_events):
        with (col1 if i % 2 == 0 else col2):
            st.markdown(f"""
            <div class="timeline-item">
                <div class="timeline-year">{year}</div>
                <div class="card-title" style="font-size:1rem;color:{HEADING};">{title}</div>
                <div class="card-body" style="color:{TEXT_MUTED};">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f'<h2 class="section-heading">Personality Meter</h2><hr class="section-rule">', unsafe_allow_html=True)
    traits = {
        "💡 Willingness to Learn": 95,
        "🎨 Creative Thinking": 75,
        "🔍 Attention to Detail": 70,
        "🤝 Teamwork & Collaboration": 80,
        "☕ Late-Night Coding Sessions": 85,
    }
    for trait, val in traits.items():
        c1, c2 = st.columns([3, 1])
        with c1:
            st.progress(val / 100, text=trait)
        with c2:
            st.markdown(f"<div style='padding-top:8px;font-size:0.9rem;color:{GOLD};font-weight:600;'>{val}%</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PORTFOLIO
# ══════════════════════════════════════════════════════════════════════════════
elif page == "💼  Portfolio":
    st.markdown(f'<h2 class="section-heading">Portfolio</h2><hr class="section-rule">', unsafe_allow_html=True)

    category = st.selectbox("Filter by Category", ["All", "Web Dev", "Academic Project", "Personal"])

    projects = [
        {"title": "📊 Streamlit Portfolio", "category": "Personal", "year": "2025",
         "stack": ["Python", "Streamlit", "Plotly"],
         "desc": "This very portfolio app — personal autobiography and project showcase built with Streamlit, featuring interactive charts, multi-page navigation, dark mode, and custom CSS.",
         "metrics": {"Language": "Python", "Pages": "6", "Status": "Live"},
         "link": "github.com/alexandreinsh/Streamlit"},
        {"title": "✅ SmartFormValidation", "category": "Web Dev", "year": "2025",
         "stack": ["JavaScript", "HTML", "CSS"],
         "desc": "A smart client-side form validation library in JavaScript that provides real-time feedback, custom validation rules, and clean error messaging for web forms.",
         "metrics": {"Language": "JavaScript", "Updated": "Dec 2025", "Visibility": "Public"},
         "link": "github.com/alexandreinsh/SmartFormValidation"},
        {"title": "📚 PeerLendingLibrary", "category": "Web Dev", "year": "2025",
         "stack": ["JavaScript", "HTML", "CSS"],
         "desc": "A peer-to-peer book lending web application that lets users list, borrow, and track books within a community — promoting a culture of shared reading.",
         "metrics": {"Language": "JavaScript", "Updated": "Dec 2025", "Type": "Web App"},
         "link": "github.com/alexandreinsh/PeerLendingLibrary"},
        {"title": "🔐 OAuth2 Integration", "category": "Academic Project", "year": "2025",
         "stack": ["Java", "OAuth2", "GitHub API", "Google API"],
         "desc": "Implemented OAuth2 authentication flows integrating both GitHub and Google login providers in a Java application, handling token exchange, scopes, and session management.",
         "metrics": {"Language": "Java", "Providers": "2", "Updated": "Oct 2025"},
         "link": "github.com/alexandreinsh/OAuth2-Integration-with-GitHub-Google"},
        {"title": "💰 FinApp", "category": "Academic Project", "year": "2025",
         "stack": ["Java"],
         "desc": "A personal finance management application built in Java. Helps users track income, expenses, and budgets with a clean interface and summary reports.",
         "metrics": {"Language": "Java", "Updated": "Oct 2025", "Type": "Finance App"},
         "link": "github.com/alexandreinsh/FinApp"},
        {"title": "🪪 QREntry", "category": "Academic Project", "year": "2025",
         "stack": ["Apex", "QR Code", "Salesforce"],
         "desc": "A QR code-based entry and attendance system built using Apex (Salesforce platform). Enables fast event check-ins by scanning QR codes linked to registrant records.",
         "metrics": {"Language": "Apex", "Updated": "Oct 2025", "Use Case": "Attendance"},
         "link": "github.com/alexandreinsh/QREntry"},
        {"title": "🐍 Nash_Project", "category": "Personal", "year": "2025",
         "stack": ["Python"],
         "desc": "A Python personal project exploring scripting, automation, or data processing. Reflects hands-on practice with Python fundamentals and problem-solving.",
         "metrics": {"Language": "Python", "Updated": "Sep 2025", "Type": "Personal"},
         "link": "github.com/alexandreinsh/Nash_Project"},
        {"title": "📝 BeanNotes", "category": "Web Dev", "year": "2025",
         "stack": ["React", "Tailwind CSS", "JavaScript"],
         "desc": "A simple and modern notes web app built with React and Tailwind CSS. Supports creating, editing, and organizing notes with a clean, minimal UI.",
         "metrics": {"Language": "JavaScript", "Framework": "React", "Updated": "Sep 2025"},
         "link": "github.com/alexandreinsh/BeanNotes"},
    ]

    filtered = [p for p in projects if category == "All" or p["category"] == category]

    for i in range(0, len(filtered), 2):
        cols = st.columns(2)
        for j, col in enumerate(cols):
            if i + j < len(filtered):
                p = filtered[i + j]
                with col:
                    with st.expander(f"{p['title']}  ·  {p['category']}  ·  {p['year']}", expanded=True):
                        st.markdown(f"<p style='font-size:0.95rem;color:{TEXT_MUTED};margin-bottom:14px;line-height:1.6;'>{p['desc']}</p>", unsafe_allow_html=True)
                        st.markdown(f"<p style='color:{TEXT};font-weight:600;font-size:0.9rem;margin-bottom:6px;'>Tools & Stack:</p>", unsafe_allow_html=True)
                        tags_html = "".join([f'<span class="skill-tag">{s}</span>' for s in p["stack"]])
                        st.markdown(tags_html, unsafe_allow_html=True)
                        st.markdown("<br>", unsafe_allow_html=True)
                        m_cols = st.columns(len(p["metrics"]))
                        for mc, (k, v) in zip(m_cols, p["metrics"].items()):
                            mc.metric(k, v)
                        st.markdown(f"<a href='https://{p['link']}' target='_blank' style='display:inline-block;margin-top:12px;font-size:0.82rem;color:{GOLD};font-family:DM Mono,monospace;text-decoration:none;border:1px solid {GOLD};border-radius:6px;padding:6px 14px;'>🔗 View on GitHub ↗</a>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f'<h2 class="section-heading">Project Breakdown</h2><hr class="section-rule">', unsafe_allow_html=True)
    labels = ["JavaScript", "Java", "Python", "Apex"]
    values = [4, 3, 3, 1]
    fig = go.Figure(data=[go.Pie(
        labels=labels, values=values, hole=0.45,
        marker=dict(colors=["#c9a84c", "#1a1a2e", "#0f3460", "#4a4a6a"]),
        textfont=dict(family="DM Sans", size=12, color="#fff"),
        hovertemplate='%{label}: <b>%{value} projects</b><extra></extra>'
    )])
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(family='DM Sans', color=PLOT_TEXT),
                      margin=dict(l=10, r=10, t=10, b=10), height=280,
                      legend=dict(font=dict(family="DM Sans", size=12, color=PLOT_TEXT)))
    st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# SKILLS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📊  Skills":
    st.markdown(f'<h2 class="section-heading">Skills & Expertise</h2><hr class="section-rule">', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["💻 Technical Skills", "📈 Skill Radar", "🧰 Tools & Platforms"])

    with tab1:
        categories = {
            "Programming Languages": [("Python", 60), ("JavaScript", 58), ("Java", 55), ("HTML & CSS", 65), ("Apex (Salesforce)", 40)],
            "Frameworks & Libraries": [("React (Basic)", 45), ("Streamlit", 60), ("Tailwind CSS", 50), ("Node.js (Basic)", 40)],
            "Design & UI/UX":         [("Figma", 62), ("UI Design Principles", 60), ("Wireframing", 58), ("Color & Typography", 55)],
            "Tools & Practices":      [("Git & GitHub", 65), ("VS Code", 75), ("Problem Solving", 65), ("Teamwork & Communication", 70)],
        }
        col1, col2 = st.columns(2)
        for i, (cat, skills) in enumerate(categories.items()):
            with (col1 if i % 2 == 0 else col2):
                st.markdown(f"<p style='font-family:Playfair Display,serif;font-size:1.1rem;font-weight:700;color:{HEADING};margin-bottom:14px;'>⚡ {cat}</p>", unsafe_allow_html=True)
                for skill, level in skills:
                    c1, c2, c3 = st.columns([2.5, 3, 0.6])
                    c1.markdown(f"<p style='font-size:0.9rem;padding-top:6px;color:{TEXT};margin:0;'>{skill}</p>", unsafe_allow_html=True)
                    c2.progress(level / 100)
                    c3.markdown(f"<p style='font-size:0.85rem;color:{GOLD};font-weight:600;padding-top:6px;margin:0;'>{level}%</p>", unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)

        st.markdown(f"<div class='card'><p style='color:{TEXT_MUTED};font-style:italic;'>💡 Skills are self-assessed as a current IT student at CITU. Still learning and growing every day!</p></div>", unsafe_allow_html=True)

    with tab2:
        axes   = ["Python", "JavaScript", "Java", "HTML/CSS", "Figma/Design", "Git & GitHub", "Problem Solving"]
        scores = [60, 58, 55, 65, 62, 65, 65]
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=scores + [scores[0]], theta=axes + [axes[0]],
            fill='toself', fillcolor='rgba(201,168,76,0.15)',
            line=dict(color=GOLD, width=2), name='Alexandrei Nash Dinapo'
        ))
        fig.update_layout(
            polar=dict(bgcolor='rgba(0,0,0,0)',
                radialaxis=dict(visible=True, range=[0, 100], gridcolor=PLOT_GRID, tickfont=dict(size=9, color=PLOT_TEXT)),
                angularaxis=dict(tickfont=dict(family='DM Sans', size=12, color=PLOT_TEXT))),
            paper_bgcolor='rgba(0,0,0,0)', showlegend=False, height=420,
            margin=dict(l=60, r=60, t=30, b=30))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(f"<p style='text-align:center;font-size:0.85rem;color:{TEXT_MUTED};'>Self-assessed skill levels as a current IT student.</p>", unsafe_allow_html=True)

    with tab3:
        tools_list = {
            "🎨 Design": ["Figma", "Canva", "Adobe Photoshop (Basic)"],
            "💻 Development": ["VS Code", "Python", "JavaScript", "Java", "HTML/CSS", "React"],
            "🔧 Dev Tools": ["Git", "GitHub", "Streamlit", "Salesforce / Apex"],
            "📋 Productivity": ["Google Workspace", "Notion", "Microsoft Office"],
        }
        for cat, tools in tools_list.items():
            st.markdown(f"<p style='font-weight:600;color:{TEXT};margin-bottom:8px;'>{cat}</p>", unsafe_allow_html=True)
            st.markdown("".join([f'<span class="skill-tag">{t}</span>' for t in tools]), unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# EDUCATION
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🎓  Education":
    st.markdown(f'<h2 class="section-heading">Education</h2><hr class="section-rule">', unsafe_allow_html=True)

    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown(f"""
        <div class="card">
            <div class="card-title">Bachelor of Science in Information Technology</div>
            <div class="card-subtitle">CITU · Currently Enrolled</div>
            <div class="card-body">
                <p style="color:{TEXT_MUTED};">Studying Information Technology at CITU in Cebu, Philippines. Coursework covers
                programming fundamentals, systems analysis and design, database management, networking,
                web development, and software engineering.</p>
                <p style="margin-top:10px;color:{TEXT_MUTED};">Through academic projects and personal initiatives, I've worked
                with Python, JavaScript, Java, and Apex — building real applications that solve real problems.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f'<h3 class="section-heading" style="font-size:1.5rem;margin-top:20px;">Courses & Self-Learning</h3><hr class="section-rule">', unsafe_allow_html=True)
        certs = [
            ("Google UX Design Certificate", "Google / Coursera", "In Progress"),
            ("UI/UX Design Essentials — Figma", "Udemy", "2024"),
            ("Introduction to User Experience Design", "Georgia Tech / Coursera", "2024"),
            ("Figma for Beginners: Design a Mobile App", "Coursera", "2024"),
        ]
        for cert, issuer, year in certs:
            st.markdown(f"""
            <div class="card" style="padding:16px 22px;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <div class="card-title" style="font-size:1rem;">📖 {cert}</div>
                        <div class="card-subtitle">{issuer}</div>
                    </div>
                    <div style="font-family:'DM Mono',monospace;font-size:0.85rem;color:{GOLD};">{year}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        st.markdown(f'<h3 class="section-heading" style="font-size:1.5rem;">Currently Learning</h3><hr class="section-rule">', unsafe_allow_html=True)
        learning = {"UI/UX Design": 62, "React & Front-End": 45, "Java & OOP": 55, "Python & Scripting": 60, "Git & Version Control": 65}
        for label, pct in learning.items():
            st.markdown(f"<p style='font-size:0.88rem;margin-bottom:4px;color:{TEXT_MUTED};'>{label}</p>", unsafe_allow_html=True)
            st.progress(pct / 100)
            st.markdown("<br>", unsafe_allow_html=True)

        st.markdown(f"""
        <div class="card" style="margin-top:8px;">
            <div class="card-title" style="font-size:1rem;">🎯 Goals & Dream</div>
            <div class="card-body" style="margin-top:8px;">
                <p style="color:{TEXT_MUTED};">🎨 Become a professional <strong style="color:{TEXT};">UI/UX Designer</strong></p>
                <p style="margin-top:6px;color:{TEXT_MUTED};">• Graduate from CITU with strong IT foundations</p>
                <p style="margin-top:6px;color:{TEXT_MUTED};">• Land a UI/UX design internship or role</p>
                <p style="margin-top:6px;color:{TEXT_MUTED};">• Build a polished Figma design portfolio</p>
                <p style="margin-top:6px;color:{TEXT_MUTED};">• Keep learning, keep designing, keep growing</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# CONTACT
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📬  Contact":
    st.markdown(f'<h2 class="section-heading">Get In Touch</h2><hr class="section-rule">', unsafe_allow_html=True)

    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown(f"<p style='font-family:Playfair Display,serif;font-size:1.2rem;font-weight:700;color:{HEADING};margin-bottom:16px;'>Send me a message</p>", unsafe_allow_html=True)
        name    = st.text_input("Your Name", placeholder="Juan dela Cruz")
        email   = st.text_input("Email Address", placeholder="juan@example.com")
        subject = st.selectbox("Subject", [
            "🤝 Collaboration Opportunity", "💼 Internship / Job Offer",
            "🎨 Design Feedback", "💬 General Inquiry", "🙌 Just Saying Hi",
        ])
        message = st.text_area("Message", placeholder="I'd love to connect!", height=150)

        ca, cb = st.columns([2, 1])
        with ca:
            st.checkbox("Notify me about Alexandrei's new projects")
        with cb:
            st.toggle("Mark as Urgent")

        if st.button("✉️  Send Message", use_container_width=True):
            if name and email and message:
                with st.spinner("Sending your message..."):
                    time.sleep(1.5)
                st.success(f"🎉 Thanks, {name}! Alexandrei will get back to you soon.")
                st.balloons()
            else:
                st.warning("Please fill in your name, email, and message.")

    with col2:
        # ── Profile Photo Upload ──────────────────────────────────────────
        st.markdown(f"<p style='font-family:Playfair Display,serif;font-size:1.1rem;font-weight:700;color:{HEADING};margin-bottom:10px;'>🖼️ Profile Photo</p>", unsafe_allow_html=True)

        contact_avatar = avatar_html(size=130, font_size="2.2rem", border=4)
        st.markdown(f"""
        <div style="text-align:center;margin-bottom:12px;">
            {contact_avatar}
            <p style="margin-top:10px;font-family:'Playfair Display',serif;font-size:1rem;
                      font-weight:700;color:{HEADING};">Alexandrei Nash Dinapo</p>
            <p style="font-size:0.78rem;color:{GOLD};letter-spacing:0.1em;
                      text-transform:uppercase;margin-top:2px;">IT Student · CITU</p>
        </div>
        """, unsafe_allow_html=True)

        uploaded_photo = st.file_uploader("Choose a new photo", type=["png", "jpg", "jpeg", "webp"], key="photo_uploader")

        if uploaded_photo is not None:
            preview_bytes = uploaded_photo.read()
            preview_b64   = base64.b64encode(preview_bytes).decode()
            ext  = uploaded_photo.name.split(".")[-1].lower()
            mime = "image/jpeg" if ext in ["jpg", "jpeg"] else f"image/{ext}"

            st.markdown(f"""
            <div style="text-align:center;margin:10px 0 6px;">
                <p style="font-size:0.8rem;color:{TEXT_MUTED};margin-bottom:6px;">Preview:</p>
                <img src="data:{mime};base64,{preview_b64}"
                     style="width:90px;height:90px;border-radius:50%;object-fit:cover;
                            border:2px dashed {GOLD};opacity:0.9;" />
            </div>
            """, unsafe_allow_html=True)

            if st.button("✅  Set as Profile Photo", use_container_width=True, key="confirm_photo"):
                st.session_state.profile_photo_b64  = preview_b64
                st.session_state.profile_photo_mime = mime
                st.success("🎉 Profile photo updated everywhere!")
                st.rerun()

        if st.session_state.profile_photo_b64:
            if st.button("🗑️  Remove Photo", use_container_width=True, key="remove_photo"):
                st.session_state.profile_photo_b64  = None
                st.session_state.profile_photo_mime = None
                st.rerun()

        st.markdown(f"""
        <div class="card" style="margin-top:16px;">
            <div class="card-title">Contact Details</div>
            <div style="margin-top:16px;">
                <a href="mailto:dinaponash26@gmail.com" class="contact-link">📧 <span>dinaponash26@gmail.com</span></a>
                <a href="https://github.com/alexandreinsh" target="_blank" class="contact-link">🐙 <span>github.com/alexandreinsh</span></a>
                <a href="https://figma.com/@nashdinapo" target="_blank" class="contact-link">🎨 <span>figma.com/@nashdinapo</span></a>
                <div class="contact-link">🏫 <span>CITU</span></div>
                <div class="contact-link">📍 <span>Cebu, Philippines (UTC+8)</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"<p style='font-family:Playfair Display,serif;font-size:1rem;font-weight:700;color:{HEADING};margin:16px 0 10px;'>Open To</p>", unsafe_allow_html=True)
        for label, pct in {"Internship Opportunities": 95, "School Collaborations": 90, "Open Source Projects": 80, "Freelance / Side Projects": 70}.items():
            st.markdown(f"<p style='font-size:0.85rem;margin-bottom:4px;color:{TEXT_MUTED};'>{label}</p>", unsafe_allow_html=True)
            st.progress(pct / 100)

        st.markdown("<br>", unsafe_allow_html=True)
        mc1, mc2 = st.columns(2)
        mc1.metric("Response", "< 24h", "↑ Quick")
        mc2.metric("Timezone", "UTC +8", "Cebu, PH")