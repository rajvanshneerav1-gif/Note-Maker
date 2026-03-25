import streamlit as st
from groq import Groq
import json
import os
from datetime import datetime, date

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="The UPSC Digest",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Constants ─────────────────────────────────────────────────────────────────
NOTES_FILE = "notes.json"

CATEGORIES = [
    {"id": "polity",      "label": "Polity & Governance",       "icon": "⚖️",  "color": "#c0392b"},
    {"id": "economy",     "label": "Economy",                    "icon": "📈",  "color": "#27ae60"},
    {"id": "ir",          "label": "International Relations",    "icon": "🌐",  "color": "#2980b9"},
    {"id": "environment", "label": "Environment & Ecology",      "icon": "🌿",  "color": "#16a085"},
    {"id": "science",     "label": "Science & Technology",       "icon": "🔬",  "color": "#8e44ad"},
    {"id": "social",      "label": "Social Issues",              "icon": "🤝",  "color": "#e67e22"},
    {"id": "security",    "label": "Security & Defence",         "icon": "🛡️",  "color": "#2c3e50"},
    {"id": "history",     "label": "History & Culture",          "icon": "🏛️",  "color": "#d35400"},
    {"id": "geography",   "label": "Geography",                  "icon": "🗺️",  "color": "#1abc9c"},
    {"id": "misc",        "label": "Miscellaneous",              "icon": "📌",  "color": "#7f8c8d"},
]
CAT_MAP = {c["id"]: c for c in CATEGORIES}

SYSTEM_PROMPT = """You are AIR 1 of UPSC Civil Services Examination helping a fellow aspirant understand the news better.

When given newspaper article content, produce structured UPSC-focused notes in the following JSON format ONLY (no markdown, no preamble):

{
  "title": "Short crisp headline (max 10 words)",
  "category": "one of: polity, economy, ir, environment, science, social, security, history, geography, misc",
  "one_liner": "One simple sentence explaining what happened and why it matters — like you're telling a friend",
  "key_points": ["point 1", "point 2", "point 3", "point 4", "point 5"],
  "upsc_angle": "Why this matters for UPSC — which paper, which topic, GS1/GS2/GS3/GS4/Essay",
  "key_terms": ["Term 1", "Term 2", "Term 3"],
  "prelims_fact": "One crisp factoid that could appear in Prelims MCQ",
  "mains_question": "A potential UPSC Mains question this topic could generate"
}

LANGUAGE RULES — strictly follow these:
- Write like you are explaining to a smart friend, NOT like a newspaper or textbook
- Use short sentences. One idea per sentence.
- Avoid heavy jargon. If you must use a technical term, briefly explain it in plain words right after.
- Key points should start with simple action words: "The government decided...", "This means...", "India will now...", "The problem is..."
- No complex phrases like "pursuant to", "in the backdrop of", "vis-à-vis", "holistic paradigm" etc.
- The one_liner should sound like something you'd say out loud in conversation
- The prelims_fact should be a clean, memorable one-liner a student can recall easily
- The mains_question should be in plain English, not overly formal

Every note should feel easy to read and remember — clarity over complexity."""


# ── Persistence helpers ───────────────────────────────────────────────────────
def load_notes() -> dict:
    if os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, "r") as f:
            return json.load(f)
    return {}

def save_notes(notes: dict):
    with open(NOTES_FILE, "w") as f:
        json.dump(notes, f, indent=2)


# ── Session state init ────────────────────────────────────────────────────────
if "notes" not in st.session_state:
    st.session_state.notes = load_notes()
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "add"
if "expanded_note" not in st.session_state:
    st.session_state.expanded_note = None


# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=Source+Serif+4:ital,wght@0,300;0,400;0,600;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Source Serif 4', serif;
    background-color: #f5f0e8;
    color: #1a1208;
}

/* Remove default Streamlit top padding */
.block-container { padding-top: 0 !important; max-width: 100% !important; }
header[data-testid="stHeader"] { background: transparent; }

/* ── App Header ── */
.app-header {
    background: #1a1208;
    color: #f5f0e8;
    padding: 18px 32px 0;
    margin: -1rem -1rem 0;
    text-align: center;
    border-bottom: 1px solid #3a2d10;
}
.app-header .tagline {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    letter-spacing: 4px;
    color: #8b6914;
    text-transform: uppercase;
    margin-bottom: 6px;
}
.app-header h1 {
    font-family: 'Playfair Display', serif;
    font-size: 42px;
    font-weight: 900;
    letter-spacing: -1px;
    margin: 0;
    line-height: 1;
    color: #f5f0e8;
}
.app-header .subtitle {
    font-size: 12px;
    color: #c9a84c;
    letter-spacing: 2px;
    font-style: italic;
    margin-top: 6px;
    margin-bottom: 14px;
}

/* ── Section headings ── */
.section-title {
    font-family: 'Playfair Display', serif;
    font-size: 24px;
    font-weight: 700;
    color: #1a1208;
    border-bottom: 3px double #8b6914;
    padding-bottom: 8px;
    margin-bottom: 4px;
}
.section-sub {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    color: #9b8560;
    letter-spacing: 1px;
    margin-bottom: 18px;
}

/* ── Cards ── */
.note-card {
    background: #ffffff;
    border: 1px solid #d4c098;
    border-radius: 4px;
    box-shadow: 3px 3px 0 #d4c098;
    padding: 20px;
    margin-bottom: 16px;
    transition: transform 0.15s, box-shadow 0.15s;
}
.note-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.1);
}
.note-header { margin-bottom: 8px; }
.cat-pill {
    display: inline-block;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    padding: 2px 10px;
    border-radius: 12px;
    color: #fff;
    margin-right: 8px;
    letter-spacing: 0.5px;
}
.note-title {
    font-family: 'Playfair Display', serif;
    font-size: 20px;
    font-weight: 700;
    line-height: 1.3;
    color: #1a1208;
    margin: 6px 0 4px;
}
.note-oneliner {
    font-size: 13px;
    color: #4a3c1e;
    font-style: italic;
    line-height: 1.6;
}

/* ── Expanded sections ── */
.expand-section {
    background: #fdfaf4;
    border: 1px solid #e0d0a8;
    border-radius: 4px;
    padding: 16px;
    margin-top: 12px;
}
.section-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    color: #8b6914;
    letter-spacing: 1px;
    margin-bottom: 10px;
    font-weight: 500;
}
.key-point {
    display: flex;
    gap: 10px;
    margin-bottom: 8px;
    align-items: flex-start;
}
.point-num {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    color: #8b6914;
    font-weight: 600;
    flex-shrink: 0;
    margin-top: 2px;
    min-width: 20px;
}
.point-text {
    font-size: 13.5px;
    line-height: 1.6;
    color: #1a1208;
}
.upsc-box {
    background: #1a1208;
    border-radius: 4px;
    padding: 16px;
    color: #e8d9b0;
    font-size: 13px;
    line-height: 1.6;
}
.upsc-box .section-label { color: #8b6914; }
.prelims-box {
    background: #fff9e6;
    border: 1px solid #f0d060;
    border-radius: 4px;
    padding: 16px;
    font-size: 13px;
    line-height: 1.6;
}
.mains-box {
    background: #f0f4ff;
    border: 1px solid #b0c0e8;
    border-radius: 4px;
    padding: 16px;
}
.mains-box .section-label { color: #2c5282; }
.mains-q {
    font-size: 14px;
    font-style: italic;
    font-weight: 600;
    line-height: 1.6;
    color: #1a1208;
}
.term-chip {
    display: inline-block;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
    padding: 4px 12px;
    background: #1a1208;
    color: #c9a84c;
    border-radius: 2px;
    margin-right: 6px;
    margin-bottom: 6px;
    letter-spacing: 0.5px;
}

/* ── Sidebar styling ── */
[data-testid="stSidebar"] {
    background: #1a1208 !important;
}
[data-testid="stSidebar"] * { color: #e8d9b0 !important; }
[data-testid="stSidebar"] .stRadio label { color: #c9a84c !important; }
[data-testid="stSidebar"] hr { border-color: #3a2d10 !important; }
.sidebar-stat-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    letter-spacing: 1px;
    color: #9b8560;
    text-transform: uppercase;
}
.sidebar-stat-value {
    font-family: 'Playfair Display', serif;
    font-size: 28px;
    font-weight: 700;
    color: #8b6914;
}

/* ── Input area ── */
.input-card {
    background: #ffffff;
    border: 1px solid #d4c098;
    border-radius: 4px;
    box-shadow: 4px 4px 0 #d4c098;
    padding: 32px;
    max-width: 760px;
    margin: 0 auto;
}
.input-title {
    font-family: 'Playfair Display', serif;
    font-size: 26px;
    font-weight: 700;
    border-bottom: 3px double #8b6914;
    padding-bottom: 14px;
    margin-bottom: 16px;
}
.input-subtitle {
    font-size: 14px;
    color: #6b5630;
    font-style: italic;
    margin-bottom: 16px;
}

/* ── Feature list ── */
.features-box {
    background: #1a1208;
    border-radius: 4px;
    padding: 20px;
    max-width: 760px;
    margin: 20px auto 0;
}
.feature-item {
    font-family: 'Source Serif 4', serif;
    font-size: 13px;
    color: #e8d9b0;
    margin-bottom: 6px;
}

/* ── Source tags ── */
.source-tag {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    padding: 3px 8px;
    background: #f0e8d8;
    border: 1px solid #c4a96e;
    border-radius: 2px;
    color: #6b5630;
    letter-spacing: 1px;
    margin-right: 6px;
}

/* Make sidebar toggle button visible */
[data-testid="collapsedControl"] {
    display: flex !important;
    background: #1a1208 !important;
    color: #c9a84c !important;
    border-radius: 4px !important;
    width: 36px !important;
    height: 36px !important;
    align-items: center !important;
    justify-content: center !important;
}
[data-testid="collapsedControl"] svg {
    fill: #c9a84c !important;
}

/* Hide Streamlit branding */
#MainMenu, footer { visibility: hidden; }

/* Streamlit button tweaks */
.stButton > button {
    font-family: 'IBM Plex Mono', monospace !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    border-radius: 4px !important;
}
div[data-testid="stTextArea"] textarea {
    font-family: 'Source Serif 4', serif !important;
    font-size: 15px !important;
    line-height: 1.7 !important;
    background: #fdfaf4 !important;
    border: 1px solid #c4a96e !important;
    color: #1a1208 !important;
}
</style>
""", unsafe_allow_html=True)


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <div class="tagline">UPSC Civil Services Preparation</div>
    <h1>The UPSC Digest</h1>
    <p class="subtitle">AI-Powered Newspaper Notes for Serious Aspirants</p>
</div>
""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📰 The UPSC Digest")
    st.markdown("---")

    page = st.radio("Navigate", ["📰 Add News", "📚 My Notes"], label_visibility="collapsed")

    st.markdown("---")

    all_notes_flat = [n for day in st.session_state.notes.values() for n in day]
    total = len(all_notes_flat)

    st.markdown(f"""
    <div class="sidebar-stat-label">Total Notes</div>
    <div class="sidebar-stat-value">{total}</div>
    """, unsafe_allow_html=True)

    if total > 0:
        st.markdown("---")
        st.markdown("<span style='font-family:IBM Plex Mono;font-size:10px;letter-spacing:1px;color:#8b6914;'>BY CATEGORY</span>", unsafe_allow_html=True)
        for cat in CATEGORIES:
            count = sum(1 for n in all_notes_flat if n.get("category") == cat["id"])
            if count > 0:
                st.markdown(f"{cat['icon']} **{cat['label']}** — {count}", unsafe_allow_html=False)

    st.markdown("---")
    api_key = st.secrets.get("GROQ_API_KEY", "")
    if not api_key:
        api_key = st.text_input("Groq API Key", type="password", placeholder="gsk_...", help="Get free key at console.groq.com")


# ── ADD NEWS PAGE ─────────────────────────────────────────────────────────────
if page == "📰 Add News":
    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("""
    <div class="input-card">
        <div class="input-title">Paste Your Newspaper Article</div>
        <div class="input-subtitle">
            Paste any article — The Hindu, Indian Express, PIB, or any source.
            Our AI will extract UPSC-relevant insights in plain, easy language.
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.container():
        col_main, col_pad = st.columns([3, 1])
        with col_main:
            article_text = st.text_area(
                label="Article",
                label_visibility="collapsed",
                placeholder="Paste the full article text here...\n\nExample: 'The Union Cabinet today approved the National Curriculum Framework for School Education...'",
                height=320,
                key="article_input"
            )

            st.markdown("""
            <div style="margin: 4px 0 12px;">
                <span class="source-tag">The Hindu</span>
                <span class="source-tag">IE</span>
                <span class="source-tag">PIB</span>
                <span class="source-tag">Lok Sabha Q&A</span>
                <span class="source-tag">Economic Survey</span>
                <span style="font-size:12px;color:#9b8560;font-style:italic;">compatible sources</span>
            </div>
            """, unsafe_allow_html=True)

            char_count = len(article_text) if article_text else 0
            st.markdown(f"<div style='font-family:IBM Plex Mono;font-size:11px;color:#9b8560;text-align:right;margin-bottom:8px;'>{char_count} chars</div>", unsafe_allow_html=True)

            generate_btn = st.button(
                "✦  Generate UPSC Notes",
                use_container_width=True,
                type="primary",
                disabled=not article_text or not article_text.strip()
            )

        if generate_btn:
            if not api_key:
                st.error("Please enter your Groq API key in the sidebar.")
            elif not article_text.strip():
                st.warning("Please paste an article first.")
            else:
                with st.spinner("⚙️ Generating UPSC notes..."):
                    try:
                        client = Groq(api_key=api_key)
                        response = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[
                                {"role": "system", "content": SYSTEM_PROMPT},
                                {"role": "user", "content": f"Convert this newspaper content into UPSC notes:\n\n{article_text}"}
                            ]
                        )
                        raw = response.choices[0].message.content
                        cleaned = raw.replace("```json", "").replace("```", "").strip()
                        parsed = json.loads(cleaned)

                        today = date.today().isoformat()
                        note_id = f"{today}_{int(datetime.now().timestamp() * 1000)}"
                        note = {
                            **parsed,
                            "id": note_id,
                            "date": today,
                            "createdAt": datetime.now().isoformat()
                        }

                        notes = st.session_state.notes
                        if today not in notes:
                            notes[today] = []
                        notes[today].insert(0, note)
                        save_notes(notes)
                        st.session_state.notes = notes

                        st.success("✓ Note saved! Switch to 'My Notes' to view it.")
                        st.balloons()

                    except json.JSONDecodeError:
                        st.error("Failed to parse AI response. Please try again.")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

    st.markdown("""
    <div class="features-box">
        <div style="font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:1px;color:#8b6914;margin-bottom:10px;">// WHAT YOU GET</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
            <div class="feature-item">📋 Key Points Summary</div>
            <div class="feature-item">🎯 UPSC GS Paper Mapping</div>
            <div class="feature-item">📝 Potential Mains Question</div>
            <div class="feature-item">⚡ Prelims Quick Fact</div>
            <div class="feature-item">🔑 Key Terms & Concepts</div>
            <div class="feature-item">📂 Auto-Category Detection</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── MY NOTES PAGE ─────────────────────────────────────────────────────────────
elif page == "📚 My Notes":
    st.markdown("<br>", unsafe_allow_html=True)
    notes = st.session_state.notes
    all_notes = [n for day in notes.values() for n in day]

    if not all_notes:
        st.markdown("""
        <div style="text-align:center;padding:80px 20px;color:#9b8560;">
            <div style="font-size:56px;margin-bottom:16px;">📰</div>
            <div class="section-title" style="border:none;text-align:center;color:#6b5630;">No notes yet</div>
            <p style="font-size:14px;font-style:italic;">Go to 'Add News' and paste your first article!</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Browse mode selector
        browse_mode = st.radio(
            "Browse by",
            ["📅 Date", "🏷️ Category"],
            horizontal=True,
            label_visibility="visible"
        )

        st.markdown("---")

        if browse_mode == "📅 Date":
            sorted_dates = sorted(notes.keys(), reverse=True)
            selected_date = st.selectbox(
                "Select Date",
                sorted_dates,
                format_func=lambda d: datetime.strptime(d, "%Y-%m-%d").strftime("%A, %d %B %Y")
            )
            display_notes = notes.get(selected_date, [])
            heading = datetime.strptime(selected_date, "%Y-%m-%d").strftime("%A, %d %B %Y")

        else:
            cat_options = [c for c in CATEGORIES if any(n.get("category") == c["id"] for n in all_notes)]
            if not cat_options:
                st.info("No categorized notes yet.")
                st.stop()

            selected_cat_label = st.selectbox(
                "Select Category",
                [f"{c['icon']} {c['label']}" for c in cat_options]
            )
            selected_cat = next(c for c in cat_options if f"{c['icon']} {c['label']}" == selected_cat_label)
            display_notes = [n for n in all_notes if n.get("category") == selected_cat["id"]]
            heading = selected_cat["label"]

        # Heading
        st.markdown(f"""
        <div class="section-title">{heading}</div>
        <div class="section-sub">{len(display_notes)} NOTE{"S" if len(display_notes) != 1 else ""}</div>
        """, unsafe_allow_html=True)

        # Render notes
        for note in display_notes:
            cat = CAT_MAP.get(note.get("category", "misc"), CAT_MAP["misc"])
            note_id = note.get("id", "")
            created = note.get("createdAt", "")
            time_str = ""
            if created:
                try:
                    time_str = datetime.fromisoformat(created).strftime("%I:%M %p")
                except Exception:
                    pass

            # Card header
            st.markdown(f"""
            <div class="note-card">
                <div class="note-header">
                    <span class="cat-pill" style="background:{cat['color']};">{cat['icon']} {cat['label']}</span>
                    <span style="font-family:'IBM Plex Mono',monospace;font-size:10px;color:#9b8560;">{time_str}</span>
                </div>
                <div class="note-title">{note.get('title','')}</div>
                <div class="note-oneliner">{note.get('one_liner','')}</div>
            </div>
            """, unsafe_allow_html=True)

            # Expander for full details
            with st.expander("View full note ▼"):

                # Key Points
                st.markdown('<div class="expand-section">', unsafe_allow_html=True)
                st.markdown('<div class="section-label">// KEY POINTS</div>', unsafe_allow_html=True)
                for i, pt in enumerate(note.get("key_points", []), 1):
                    st.markdown(f"""
                    <div class="key-point">
                        <span class="point-num">0{i}</span>
                        <span class="point-text">{pt}</span>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"""
                    <div class="upsc-box">
                        <div class="section-label">// UPSC ANGLE</div>
                        {note.get('upsc_angle','')}
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""
                    <div class="prelims-box">
                        <div class="section-label">⚡ PRELIMS FACT</div>
                        {note.get('prelims_fact','')}
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                st.markdown(f"""
                <div class="mains-box">
                    <div class="section-label">📝 POTENTIAL MAINS QUESTION</div>
                    <div class="mains-q">"{note.get('mains_question','')}"</div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                # Key terms
                terms_html = "".join(f'<span class="term-chip">{t}</span>' for t in note.get("key_terms", []))
                st.markdown(f"""
                <div>
                    <div class="section-label">🔑 KEY TERMS</div>
                    {terms_html}
                </div>
                """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                # Delete
                if st.button("🗑 Delete this note", key=f"del_{note_id}"):
                    note_date = note.get("date", date.today().isoformat())
                    updated = st.session_state.notes
                    updated[note_date] = [n for n in updated.get(note_date, []) if n.get("id") != note_id]
                    if not updated[note_date]:
                        del updated[note_date]
                    save_notes(updated)
                    st.session_state.notes = updated
                    st.rerun()
