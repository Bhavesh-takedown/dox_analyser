# ==============================================================================
# rag_pipeline.py — "The Orchestrator"
#
# WHAT THIS FILE DOES:
#   This is the BRAIN that connects all the other modules together.
#   It manages:
#     1. A global VectorStore instance (shared across all requests)
#     2. A registry of all uploaded documents (name, pages, chunk count)
#     3. process_document() — runs the full PDF → index pipeline
#     4. answer_question()  — runs the full query → answer pipeline
#
# WHY A GLOBAL vector_store?
#   In a web server, each API request is handled separately. But the FAISS index
#   must PERSIST between requests (we don't want to re-index on every question).
#   By storing it as a module-level global, it lives for the lifetime of the server.
#
# THE FULL RAG FLOW:
#   UPLOAD:  PDF file → extract_text → chunk_text → embed → FAISS index
#   QUERY:   question → embed → FAISS search → top chunks → Groq LLM → answer
# ==============================================================================

import os
import uuid                                  # For generating unique document IDs
from typing import List, Dict

from .pdf_processor import extract_text_from_pdf, chunk_text   # Step 1: read PDF
from .vector_store import VectorStore                           # Step 2: embed + search
from .groq_client import ask_groq                               # Step 3: LLM answer


# ── Global State ───────────────────────────────────────────────────────────────
# These live for as long as the FastAPI server is running.

FAISS_STORE_DIR = "faiss_store"  # Where the persisted index lives on disk

# The single shared vector store — holds ALL indexed chunks from ALL documents
vector_store = VectorStore()

# Auto-load a previously persisted index so users don't have to re-upload
# documents every time the server restarts.
vector_store.load(FAISS_STORE_DIR)

# Registry: maps doc_id → document metadata
# e.g., {"abc-123": {"doc_id": "abc-123", "filename": "report.pdf", ...}}
documents_registry: Dict[str, Dict] = {}


# ── Document Processing Pipeline ──────────────────────────────────────────────

def process_document(pdf_path: str, filename: str) -> Dict:
    """
    Full pipeline: PDF file → text chunks → embeddings → FAISS index.

    This is called when a user uploads a PDF via the /upload endpoint.

    Args:
        pdf_path: Absolute or relative path to the saved PDF file
        filename: Original filename (e.g., "annual_report_2024.pdf")

    Returns:
        Metadata dict about the processed document:
        {
            "doc_id":     "550e8400-e29b-41d4-a716-446655440000",
            "filename":   "annual_report_2024.pdf",
            "num_pages":  42,
            "num_chunks": 187
        }

    Steps:
        1. PyMuPDF reads the PDF → list of {page_num, text} dicts
        2. chunk_text() splits pages into 200-word overlapping chunks
        3. Each chunk gets tagged with doc_id + filename for traceability
        4. VectorStore.add_chunks() embeds + indexes them in FAISS
        5. Document metadata stored in documents_registry
    """

    # ── Step 1: Extract text from every page ──────────────────────────────────
    print(f"[Pipeline] Extracting text from: {filename}")
    pages = extract_text_from_pdf(pdf_path)
    print(f"[Pipeline] Extracted {len(pages)} pages")

    # ── Step 2: Split pages into overlapping chunks ───────────────────────────
    chunks = chunk_text(pages, chunk_size=200, overlap=30)
    print(f"[Pipeline] Created {len(chunks)} chunks")

    # ── Step 3: Tag each chunk with its document identity ────────────────────
    # uuid4() generates a random universally unique ID, e.g. "550e8400-..."
    doc_id = str(uuid.uuid4())
    for chunk in chunks:
        chunk["doc_id"]   = doc_id    # Which document this chunk came from
        chunk["filename"] = filename  # Human-readable filename for citations

    # ── Step 4: Embed chunks and add to FAISS ─────────────────────────────────
    vector_store.add_chunks(chunks)

    # ── Step 5: Register document metadata ────────────────────────────────────
    doc_metadata = {
        "doc_id":     doc_id,
        "filename":   filename,
        "num_pages":  len(pages),
        "num_chunks": len(chunks),
    }
    documents_registry[doc_id] = doc_metadata

    # ── Step 6: Persist the updated index to disk ──────────────────────────────
    # This lets the index survive server restarts without re-uploading documents.
    vector_store.save(FAISS_STORE_DIR)

    print(f"[Pipeline] Document '{filename}' indexed successfully (ID: {doc_id})")
    return doc_metadata


# ── Question Answering Pipeline ───────────────────────────────────────────────

def answer_question(question: str, top_k: int = 5) -> Dict:
    """
    Full pipeline: question → retrieve relevant chunks → LLM → answer.

    This is called when a user asks a question via the /ask endpoint.

    Args:
        question: The user's natural language question
        top_k:    How many chunks to retrieve from FAISS (default 5)
                  More chunks = more context for LLM, but higher token cost

    Returns:
        {
            "answer":       "According to Page 3, the revenue grew 20%...",
            "sources":      [3, 7],          # Page numbers the answer came from
            "model":        "llama3-70b-8192",
            "tokens_used":  342,
            "chunks_used":  [...]            # The raw chunks (for debugging)
        }
    """

    # ── Step 1: Check if any documents are indexed ────────────────────────────
    if vector_store.is_empty:
        return {
            "answer":      "⚠️ No documents have been uploaded yet. Please upload a PDF first.",
            "sources":     [],
            "model":       "N/A",
            "tokens_used": 0,
            "chunks_used": []
        }

    # ── Step 2: Retrieve the most relevant chunks from FAISS ─────────────────
    # The question is embedded and compared to all stored chunk embeddings
    print(f"[Pipeline] Searching for: '{question}'")
    relevant_chunks = vector_store.search(question, top_k=top_k)
    print(f"[Pipeline] Retrieved {len(relevant_chunks)} chunks")

    # ── Step 3: Send chunks + question to Groq LLM ───────────────────────────
    result = ask_groq(question, relevant_chunks)

    # ── Step 4: Attach the raw chunks to the result (useful for UI display) ──
    result["chunks_used"] = relevant_chunks

    return result


# ── Utility Functions ─────────────────────────────────────────────────────────

def get_documents() -> List[Dict]:
    """Return metadata for all indexed documents."""
    return list(documents_registry.values())


def get_stats() -> Dict:
    """Return summary statistics about the current index."""
    return {
        "total_documents": len(documents_registry),
        "total_chunks":    vector_store.total_chunks,
        "is_empty":        vector_store.is_empty,
    }


def clear_all() -> None:
    """
    Clear ALL documents from the vector store and registry.
    This is irreversible — the user must re-upload documents after calling this.
    Also removes the persisted index from disk.
    """
    vector_store.clear()
    documents_registry.clear()
    # Remove the persisted index so it isn't reloaded on the next server start
    import shutil
    import os
    if os.path.isdir(FAISS_STORE_DIR):
        shutil.rmtree(FAISS_STORE_DIR)
    print("[Pipeline] All documents cleared.")
