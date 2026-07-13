# ==============================================================================
# streamlit_app.py — "The User Interface"
#
# WHAT THIS FILE DOES:
#   This is the Streamlit frontend — the interactive web UI the user sees.
#   Streamlit turns Python scripts into web apps automatically.
#   No HTML/CSS/JavaScript needed — Streamlit handles the browser rendering.
#
# WHAT IS STREAMLIT?
#   Streamlit re-runs this entire Python file top-to-bottom every time:
#   - The user interacts with any widget (button, uploader, text input)
#   - st.session_state preserves data between re-runs (like a RAM cache)
#
# HOW IT TALKS TO THE BACKEND:
#   The Streamlit app calls FastAPI endpoints via HTTP (using the 'requests' lib).
#   FastAPI (port 8000) ←→ Streamlit (port 8501)
#   Both must be running simultaneously.
#
# RUN THIS WITH:
#   streamlit run streamlit_app.py
# ==============================================================================

import streamlit as st    # The UI framework
import requests           # HTTP client to call FastAPI endpoints
import json
from datetime import datetime

# ── Page Configuration ────────────────────────────────────────────────────────
# Must be the FIRST Streamlit command in the script
st.set_page_config(
    page_title="DocuMind — Intelligent Document Q&A",
    page_icon="🧠",
    layout="wide",                  # Use the full browser width
    initial_sidebar_state="expanded"
)

# ── API Base URL ──────────────────────────────────────────────────────────────
API_URL = "http://localhost:8000"  # Where FastAPI is running


# ── Custom CSS — Premium Dark Theme ──────────────────────────────────────────
# st.markdown() can inject raw HTML/CSS into the page
st.markdown("""
<style>
/* ── Import Google Font ─────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Global Reset & Base ────────────────────────────────────────── */
* { font-family: 'Inter', sans-serif !important; box-sizing: border-box; }

.stApp {
    background: linear-gradient(135deg, #0a0a0f 0%, #0d1117 40%, #0a0e1a 100%);
    min-height: 100vh;
}

/* ── Hide Streamlit Default Elements ────────────────────────────── */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* ── Sidebar Styling ────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1117 0%, #0a0e1a 100%);
    border-right: 1px solid rgba(99, 102, 241, 0.2);
}
[data-testid="stSidebar"] .stMarkdown h1,
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown h3 {
    color: #a78bfa !important;
}

/* ── Main Title ─────────────────────────────────────────────────── */
.main-title {
    font-size: 3rem;
    font-weight: 800;
    background: linear-gradient(135deg, #a78bfa 0%, #60a5fa 50%, #34d399 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-align: center;
    margin-bottom: 0.2rem;
    letter-spacing: -1px;
}
.subtitle {
    text-align: center;
    color: #6b7280;
    font-size: 1.1rem;
    margin-bottom: 2rem;
    font-weight: 400;
}

/* ── Chat Messages ──────────────────────────────────────────────── */
.user-message {
    background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
    border: 1px solid rgba(99, 102, 241, 0.4);
    border-radius: 16px 16px 4px 16px;
    padding: 1rem 1.25rem;
    margin: 1rem 0 1rem 3rem;
    color: #e0e7ff;
    font-size: 0.95rem;
    line-height: 1.6;
    position: relative;
}
.user-message::before {
    content: "You";
    font-size: 0.7rem;
    font-weight: 600;
    color: #818cf8;
    text-transform: uppercase;
    letter-spacing: 1px;
    display: block;
    margin-bottom: 0.4rem;
}

.ai-message {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    border: 1px solid rgba(52, 211, 153, 0.3);
    border-radius: 16px 16px 16px 4px;
    padding: 1rem 1.25rem;
    margin: 1rem 3rem 1rem 0;
    color: #e2e8f0;
    font-size: 0.95rem;
    line-height: 1.7;
    position: relative;
}
.ai-message::before {
    content: "🧠 DocuMind AI";
    font-size: 0.7rem;
    font-weight: 600;
    color: #34d399;
    text-transform: uppercase;
    letter-spacing: 1px;
    display: block;
    margin-bottom: 0.4rem;
}

/* ── Source Badge ───────────────────────────────────────────────── */
.source-badge {
    display: inline-block;
    background: rgba(99, 102, 241, 0.15);
    border: 1px solid rgba(99, 102, 241, 0.4);
    border-radius: 20px;
    padding: 0.2rem 0.7rem;
    font-size: 0.75rem;
    color: #a78bfa;
    margin: 0.25rem 0.2rem;
    font-weight: 500;
}
.sources-row {
    margin-top: 0.75rem;
    padding-top: 0.75rem;
    border-top: 1px solid rgba(255,255,255,0.06);
}
.sources-label {
    font-size: 0.72rem;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 0.3rem;
}

/* ── Stats Card ─────────────────────────────────────────────────── */
.stat-card {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    border: 1px solid rgba(99, 102, 241, 0.2);
    border-radius: 12px;
    padding: 1.2rem;
    text-align: center;
    margin-bottom: 0.75rem;
}
.stat-number {
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #a78bfa, #60a5fa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.stat-label {
    color: #6b7280;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-top: 0.2rem;
}

/* ── Document Card ──────────────────────────────────────────────── */
.doc-card {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    border: 1px solid rgba(52, 211, 153, 0.2);
    border-radius: 12px;
    padding: 1rem;
    margin-bottom: 0.6rem;
}
.doc-name {
    color: #34d399;
    font-weight: 600;
    font-size: 0.85rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.doc-meta {
    color: #6b7280;
    font-size: 0.75rem;
    margin-top: 0.3rem;
}

/* ── Buttons ─────────────────────────────────────────────────────── */
.stButton > button {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 0.6rem 1.5rem;
    font-weight: 600;
    font-size: 0.9rem;
    transition: all 0.2s ease;
    width: 100%;
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 8px 25px rgba(99, 102, 241, 0.4);
}

/* ── File Uploader ──────────────────────────────────────────────── */
[data-testid="stFileUploader"] {
    border: 2px dashed rgba(99, 102, 241, 0.3) !important;
    border-radius: 12px !important;
    background: rgba(15, 23, 42, 0.5) !important;
    padding: 1rem !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: rgba(99, 102, 241, 0.6) !important;
}

/* ── Text Input ─────────────────────────────────────────────────── */
.stTextInput > div > div > input,
.stChatInputContainer textarea {
    background: rgba(15, 23, 42, 0.8) !important;
    border: 1px solid rgba(99, 102, 241, 0.3) !important;
    border-radius: 12px !important;
    color: #e2e8f0 !important;
}
.stTextInput > div > div > input:focus {
    border-color: rgba(99, 102, 241, 0.7) !important;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1) !important;
}

/* ── Success/Error Messages ─────────────────────────────────────── */
.stSuccess {
    background: rgba(52, 211, 153, 0.1) !important;
    border: 1px solid rgba(52, 211, 153, 0.3) !important;
    border-radius: 10px !important;
    color: #34d399 !important;
}
.stError {
    background: rgba(239, 68, 68, 0.1) !important;
    border: 1px solid rgba(239, 68, 68, 0.3) !important;
    border-radius: 10px !important;
}

/* ── Spinner ─────────────────────────────────────────────────────── */
.stSpinner > div { border-top-color: #6366f1 !important; }

/* ── Divider ─────────────────────────────────────────────────────── */
hr { border-color: rgba(99, 102, 241, 0.15) !important; }

/* ── Empty State ─────────────────────────────────────────────────── */
.empty-state {
    text-align: center;
    padding: 4rem 2rem;
    color: #374151;
}
.empty-icon {
    font-size: 5rem;
    margin-bottom: 1rem;
    opacity: 0.4;
}
.empty-text {
    font-size: 1.1rem;
    color: #4b5563;
    font-weight: 500;
}
.empty-subtext {
    font-size: 0.85rem;
    color: #374151;
    margin-top: 0.5rem;
}

/* ── Token Badge ─────────────────────────────────────────────────── */
.token-badge {
    display: inline-block;
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 8px;
    padding: 0.15rem 0.6rem;
    font-size: 0.7rem;
    color: #6b7280;
    margin-left: 0.5rem;
}

/* ── How it Works Section ────────────────────────────────────────── */
.step-item {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    margin-bottom: 0.75rem;
    padding: 0.75rem;
    background: rgba(15, 23, 42, 0.4);
    border-radius: 10px;
    border: 1px solid rgba(99, 102, 241, 0.1);
}
.step-num {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: white;
    border-radius: 50%;
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
    font-weight: 700;
    flex-shrink: 0;
}
.step-text {
    color: #9ca3af;
    font-size: 0.82rem;
    line-height: 1.5;
    padding-top: 4px;
}
</style>
""", unsafe_allow_html=True)


# ── Session State Initialization ──────────────────────────────────────────────
# st.session_state persists data across Streamlit re-runs (like page memory)
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []   # List of {role, content, sources, tokens}

if "documents" not in st.session_state:
    st.session_state.documents = []      # List of indexed document metadata

if "total_chunks" not in st.session_state:
    st.session_state.total_chunks = 0


# ── Helper Functions ──────────────────────────────────────────────────────────

def check_api_health() -> bool:
    """Returns True if the FastAPI server is reachable."""
    try:
        r = requests.get(f"{API_URL}/", timeout=2)
        return r.status_code == 200
    except:
        return False


def upload_pdf(file) -> dict:
    """Upload a PDF file to the FastAPI /upload endpoint."""
    files = {"file": (file.name, file.getvalue(), "application/pdf")}
    r = requests.post(f"{API_URL}/upload", files=files, timeout=120)
    r.raise_for_status()
    return r.json()


def ask_question(question: str, top_k: int = 5) -> dict:
    """Send a question to the FastAPI /ask endpoint."""
    payload = {"question": question, "top_k": top_k}
    r = requests.post(f"{API_URL}/ask", json=payload, timeout=60)
    r.raise_for_status()
    return r.json()


def fetch_documents() -> list:
    """Fetch list of indexed documents from FastAPI."""
    try:
        r = requests.get(f"{API_URL}/documents", timeout=5)
        return r.json().get("documents", [])
    except:
        return []


def fetch_stats() -> dict:
    """Fetch index statistics from FastAPI."""
    try:
        r = requests.get(f"{API_URL}/stats", timeout=5)
        return r.json()
    except:
        return {}


def clear_documents():
    """Clear all documents via FastAPI."""
    r = requests.delete(f"{API_URL}/clear", timeout=10)
    r.raise_for_status()


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    # Logo + Title
    st.markdown("""
        <div style='text-align:center; padding: 1rem 0 0.5rem;'>
            <div style='font-size: 3rem;'>🧠</div>
            <div style='font-size: 1.3rem; font-weight: 700;
                        background: linear-gradient(135deg, #a78bfa, #60a5fa);
                        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                        background-clip: text;'>DocuMind</div>
            <div style='font-size: 0.72rem; color: #4b5563; letter-spacing: 1px;
                        text-transform: uppercase; margin-top: 0.2rem;'>RAG · AI · NLP</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # API Status indicator
    api_ok = check_api_health()
    if api_ok:
        st.markdown("🟢 **API Connected** — Backend running")
    else:
        st.markdown("🔴 **API Offline** — Start FastAPI first")
        st.code("uvicorn app.main:app --reload", language="bash")

    st.markdown("---")

    # ── Document Upload Section ────────────────────────────────────────────────
    st.markdown("### 📄 Upload Documents")
    st.markdown("<div style='color:#6b7280; font-size:0.8rem; margin-bottom:0.75rem;'>Upload PDFs to index for Q&A</div>", unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=["pdf"],
        help="Upload any business PDF — reports, contracts, research papers"
    )

    if uploaded_file is not None:
        if st.button("🚀 Process & Index Document", key="upload_btn"):
            if not api_ok:
                st.error("API is offline. Start FastAPI first.")
            else:
                with st.spinner(f"Reading and indexing '{uploaded_file.name}'..."):
                    try:
                        result = upload_pdf(uploaded_file)
                        doc = result["document"]
                        st.success(f"✅ Indexed {doc['num_pages']} pages, {doc['num_chunks']} chunks!")
                        # Refresh document list
                        st.session_state.documents = fetch_documents()
                        stats = fetch_stats()
                        st.session_state.total_chunks = stats.get("total_chunks", 0)
                    except Exception as e:
                        st.error(f"Upload failed: {e}")

    st.markdown("---")

    # ── Stats Cards ────────────────────────────────────────────────────────────
    stats = fetch_stats()
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class='stat-card'>
            <div class='stat-number'>{stats.get('total_documents', 0)}</div>
            <div class='stat-label'>Docs</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class='stat-card'>
            <div class='stat-number'>{stats.get('total_chunks', 0)}</div>
            <div class='stat-label'>Chunks</div>
        </div>""", unsafe_allow_html=True)

    # ── Indexed Documents List ─────────────────────────────────────────────────
    st.markdown("### 📚 Indexed Documents")
    docs = fetch_documents()

    if not docs:
        st.markdown("<div style='color:#4b5563; font-size:0.82rem; padding:0.5rem;'>No documents indexed yet</div>", unsafe_allow_html=True)
    else:
        for doc in docs:
            st.markdown(f"""
            <div class='doc-card'>
                <div class='doc-name'>📄 {doc['filename']}</div>
                <div class='doc-meta'>{doc['num_pages']} pages · {doc['num_chunks']} chunks</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── Settings ───────────────────────────────────────────────────────────────
    st.markdown("### ⚙️ Settings")
    top_k = st.slider(
        "Chunks to Retrieve (top-k)",
        min_value=1, max_value=15, value=5,
        help="More chunks = more context but slower. 5 is usually optimal."
    )

    st.markdown("---")

    # Clear button
    if st.button("🗑️ Clear All Documents", key="clear_btn"):
        try:
            clear_documents()
            st.session_state.chat_history = []
            st.session_state.documents = []
            st.success("All documents cleared!")
            st.rerun()
        except Exception as e:
            st.error(f"Clear failed: {e}")

    # ── How it Works ───────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🔍 How It Works")
    st.markdown("""
    <div class='step-item'>
        <div class='step-num'>1</div>
        <div class='step-text'><b style='color:#e2e8f0'>Upload</b> — PDF text is extracted page by page</div>
    </div>
    <div class='step-item'>
        <div class='step-num'>2</div>
        <div class='step-text'><b style='color:#e2e8f0'>Chunk</b> — Text split into 200-word overlapping pieces</div>
    </div>
    <div class='step-item'>
        <div class='step-num'>3</div>
        <div class='step-text'><b style='color:#e2e8f0'>Embed</b> — Each chunk → 384-number vector (meaning encoded)</div>
    </div>
    <div class='step-item'>
        <div class='step-num'>4</div>
        <div class='step-text'><b style='color:#e2e8f0'>Index</b> — Vectors stored in FAISS for instant search</div>
    </div>
    <div class='step-item'>
        <div class='step-num'>5</div>
        <div class='step-text'><b style='color:#e2e8f0'>Ask</b> — Question embedded, top-5 chunks retrieved</div>
    </div>
    <div class='step-item'>
        <div class='step-num'>6</div>
        <div class='step-text'><b style='color:#e2e8f0'>Answer</b> — Chunks + question → Groq LLaMA 3 70B</div>
    </div>
    """, unsafe_allow_html=True)


# ── Main Chat Area ────────────────────────────────────────────────────────────

# Title
st.markdown("<div class='main-title'>DocuMind</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Intelligent Document Q&A · Powered by RAG + Llama 3 · Ask anything about your PDFs</div>", unsafe_allow_html=True)

st.markdown("---")

# ── Chat History Display ──────────────────────────────────────────────────────
chat_container = st.container()

with chat_container:
    if not st.session_state.chat_history:
        # Empty state — shown before the first question
        st.markdown("""
        <div class='empty-state'>
            <div class='empty-icon'>💬</div>
            <div class='empty-text'>No conversation yet</div>
            <div class='empty-subtext'>Upload a PDF in the sidebar, then ask a question below</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Render each message in the chat history
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(f"""
                <div class='user-message'>{msg['content']}</div>
                """, unsafe_allow_html=True)
            else:
                # AI message — show answer + source citations
                sources_html = ""
                if msg.get("sources"):
                    badges = "".join([f"<span class='source-badge'>📄 Page {p}</span>" for p in msg["sources"]])
                    tokens = f"<span class='token-badge'>⚡ {msg.get('tokens_used', 0)} tokens</span>"
                    sources_html = f"""
                    <div class='sources-row'>
                        <div class='sources-label'>Sources</div>
                        {badges}{tokens}
                    </div>"""

                st.markdown(f"""
                <div class='ai-message'>
                    {msg['content']}
                    {sources_html}
                </div>
                """, unsafe_allow_html=True)

# ── Chat Input ────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)

# st.chat_input creates a sticky input bar at the bottom
question = st.chat_input(
    "Ask a question about your documents...",
    key="question_input"
)

if question:
    # Add user message to history
    st.session_state.chat_history.append({
        "role":    "user",
        "content": question
    })

    if not api_ok:
        st.session_state.chat_history.append({
            "role":    "assistant",
            "content": "⚠️ The API server is offline. Please start FastAPI with: `uvicorn app.main:app --reload`",
            "sources": [],
            "tokens_used": 0
        })
    else:
        # Call the FastAPI /ask endpoint
        with st.spinner("🔍 Searching documents and generating answer..."):
            try:
                result = ask_question(question, top_k=top_k)
                st.session_state.chat_history.append({
                    "role":        "assistant",
                    "content":     result["answer"],
                    "sources":     result.get("sources", []),
                    "tokens_used": result.get("tokens_used", 0),
                    "model":       result.get("model", "")
                })
            except requests.exceptions.HTTPError as e:
                error_detail = "Unknown error"
                try:
                    error_detail = e.response.json().get("detail", str(e))
                except:
                    pass
                st.session_state.chat_history.append({
                    "role":    "assistant",
                    "content": f"❌ Error: {error_detail}",
                    "sources": [],
                    "tokens_used": 0
                })
            except Exception as e:
                st.session_state.chat_history.append({
                    "role":    "assistant",
                    "content": f"❌ Connection error: {str(e)}. Is FastAPI running?",
                    "sources": [],
                    "tokens_used": 0
                })

    # Rerun to display new messages
    st.rerun()
