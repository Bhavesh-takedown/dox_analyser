# 🧠 DocuMind — Intelligent Document Q&A System (RAG)

> Upload any PDF and ask natural language questions. Get grounded, cited answers powered by LLaMA 3.3 70B via Groq.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.112-green?logo=fastapi)
![Streamlit](https://img.shields.io/badge/Streamlit-1.37-red?logo=streamlit)
![FAISS](https://img.shields.io/badge/FAISS-Vector_Search-orange)
![Groq](https://img.shields.io/badge/Groq-LLaMA_3.3_70B-purple)

---

## What It Does

DocuMind is a **Retrieval-Augmented Generation (RAG)** pipeline that lets you:
- Upload any business PDF (reports, research papers, contracts)
- Ask natural language questions about its content
- Get precise, grounded answers with **page-level citations**
- All powered by **free, local tools** — no paid cloud required

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | Groq API — LLaMA 3.3 70B (free) |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2, local) |
| Vector Store | FAISS (Facebook AI, local) |
| PDF Parsing | PyMuPDF (fitz) |
| Backend API | FastAPI + Uvicorn |
| Frontend UI | Streamlit |

## Architecture

```
PDF Upload → PyMuPDF extracts text → Chunked (200 words, 30 overlap)
         → sentence-transformers embeds → FAISS index

Question → Embed question → FAISS top-5 search → Retrieved chunks
        → Groq LLaMA 3.3 70B → Grounded answer with page citations
```

## Project Structure

```
dox/
├── app/
│   ├── __init__.py          # Python package marker
│   ├── pdf_processor.py     # PDF → text chunks
│   ├── vector_store.py      # FAISS embeddings + similarity search
│   ├── groq_client.py       # Prompt engineering + Groq LLM calls
│   ├── rag_pipeline.py      # Orchestrator connecting all steps
│   └── main.py              # FastAPI REST API (6 endpoints)
├── streamlit_app.py         # Interactive dark-themed web UI
├── requirements.txt         # All dependencies
├── .env.example             # API key template
├── run.bat                  # One-click Windows launcher
└── code_guide.html          # Complete beginner's guide (10 chapters)
```

## Setup

### 1. Get a free Groq API key
Go to [console.groq.com](https://console.groq.com) → sign up → create API key (30 seconds, no credit card)

### 2. Clone and install

```bash
git clone <your-repo-url>
cd dox

# Install uv (fast Python package manager)
# Windows PowerShell:
irm https://astral.sh/uv/install.ps1 | iex

# Create virtual environment with Python 3.11
uv venv .venv --python 3.11

# Install all dependencies
uv pip install -r requirements.txt
```

### 3. Set your API key

```bash
copy .env.example .env
# Open .env and replace YOUR_GROQ_API_KEY_HERE with your actual key
```

### 4. Run

**Option A — One click:** Double-click `run.bat`

**Option B — Manual (two terminals):**

```bash
# Terminal 1 — FastAPI backend
.venv\Scripts\uvicorn.exe app.main:app --port 8000

# Terminal 2 — Streamlit UI
.venv\Scripts\streamlit.exe run streamlit_app.py
```

Open **http://localhost:8501** in your browser.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Health check |
| `POST` | `/upload` | Upload + index a PDF |
| `POST` | `/ask` | Ask a question, get AI answer |
| `GET` | `/documents` | List indexed documents |
| `GET` | `/stats` | Index statistics |
| `DELETE` | `/clear` | Clear all documents |

Interactive docs: **http://localhost:8000/docs**

## How RAG Works

1. **Chunk** — PDF text split into 200-word overlapping pieces
2. **Embed** — Each chunk converted to a 384-dim vector (semantic meaning encoded)
3. **Index** — Vectors stored in FAISS for millisecond similarity search
4. **Retrieve** — User question embedded, top-5 nearest chunks found
5. **Generate** — Chunks + question sent to LLaMA 3.3 70B → grounded answer

## Notes

- Only **text-based PDFs** work (where you can select/highlight text). Scanned PDFs require OCR.
- The FAISS index is **in-memory** — re-upload documents after restarting the server.
- The embedding model (~80MB) downloads automatically on first run and is cached.

---

*Built as an AI portfolio project demonstrating: Python · NLP · LLMs · Vector Search · REST APIs · Unstructured Data*
