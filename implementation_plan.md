# Intelligent Document Q&A System (RAG) — Implementation Plan

## Overview

Build a full-stack RAG (Retrieval-Augmented Generation) pipeline that lets users upload PDFs/documents and ask natural language questions over them. The system retrieves relevant chunks, feeds them to an LLM (via Groq API — free), and returns grounded answers.

This is a **portfolio-grade** project designed to impress in Celonis interviews by demonstrating:
- NLP & LLM integration
- Unstructured data handling
- REST API design (FastAPI)
- Beautiful interactive UI (Streamlit)
- AI value proposition storytelling

---

## Architecture

```
User Uploads PDF
      ↓
[FastAPI Backend]
      ↓
PDF Parsing (PyMuPDF) → Text Chunks → Embeddings (sentence-transformers)
      ↓
FAISS Vector Store (local, no DB needed)
      ↓
User asks question → Query Embedding → Top-K similar chunks retrieved
      ↓
Chunks + Question sent to Groq LLM (llama3-70b-8192)
      ↓
Answer returned with source citations → Streamlit UI
```

---

## Stack

| Layer | Technology | Why |
|---|---|---|
| LLM | Groq API (llama3-70b-8192) | Free, blazing fast |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) | Free, local, fast |
| Vector Store | FAISS | Local, no server needed |
| PDF Parsing | PyMuPDF (fitz) | Best accuracy |
| Backend | FastAPI | Production-grade REST API |
| Frontend | Streamlit | Interactive, interview-friendly |
| Orchestration | LangChain | Industry standard RAG patterns |

---

## Project Structure

```
dox/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── rag_pipeline.py      # Core RAG logic
│   ├── pdf_processor.py     # PDF → chunks
│   ├── vector_store.py      # FAISS index management
│   └── groq_client.py       # LLM API calls
├── streamlit_app.py         # Streamlit frontend
├── requirements.txt
├── .env.example
├── sample_docs/             # Sample PDFs for demo
│   └── celonis_sample.pdf   # Demo document
└── README.md
```

---

## Proposed Changes

### [NEW] `requirements.txt`
All Python dependencies pinned.

### [NEW] `app/pdf_processor.py`
- Uses PyMuPDF to extract text page-by-page
- Splits text into overlapping chunks (chunk_size=500, overlap=50)
- Preserves page numbers for citations

### [NEW] `app/vector_store.py`
- sentence-transformers for embeddings
- FAISS index (IndexFlatL2) for similarity search
- Save/load index to disk

### [NEW] `app/groq_client.py`
- Async Groq API wrapper
- Prompt engineering for RAG (system prompt + context + question)
- Source citation formatting

### [NEW] `app/rag_pipeline.py`
- Orchestrates PDF → chunks → embed → store → retrieve → answer
- LangChain-style chain

### [NEW] `app/main.py`
- FastAPI app with endpoints:
  - `POST /upload` — upload PDF, process, index
  - `POST /ask` — ask question, get answer + sources
  - `GET /documents` — list indexed documents
  - `DELETE /documents/{id}` — remove document

### [NEW] `streamlit_app.py`
- Dark-themed, premium UI
- File uploader sidebar
- Chat interface with history
- Source citations displayed per answer
- Progress indicators

### [NEW] `README.md`
- Full beginner-friendly explanation of every concept

---

## Open Questions

> [!IMPORTANT]
> **Do you have a Groq API key?** If not, I'll include instructions to get one for free at console.groq.com. It takes 30 seconds and is completely free.

> [!NOTE]
> The system will work **entirely locally** — no paid cloud services needed. FAISS runs in-memory, embeddings run locally.

---

## Verification Plan

### Automated
- `uvicorn app.main:app --reload` — start FastAPI
- `streamlit run streamlit_app.py` — start UI
- Upload a sample PDF and ask a question end-to-end

### Manual
- Demo: upload Celonis annual report PDF, ask "What is Celonis's AI strategy?" → get grounded answer with page citations
