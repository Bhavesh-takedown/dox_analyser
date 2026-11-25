# ==============================================================================
# main.py — FastAPI REST API Server
# ==============================================================================

import os
import shutil

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv

load_dotenv()

from .rag_pipeline import (
    process_document,
    answer_question,
    get_documents,
    get_stats,
    clear_all
)

# ── App Setup ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title="DocuMind RAG API",
    description="Intelligent Document Q&A System using RAG (Retrieval-Augmented Generation).",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploaded_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ── Pydantic Schemas ──────────────────────────────────────────────────────────

class QuestionRequest(BaseModel):
    question: str = Field(..., description="Natural language question", example="What is the company's revenue?")
    top_k: int    = Field(default=5, ge=1, le=20, description="Number of chunks to retrieve (1-20)")

class QuestionResponse(BaseModel):
    answer:      str
    sources:     List[int]
    model:       str
    tokens_used: int


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    """Health check — confirms the API is live."""
    return {"status": "running", "message": "DocuMind RAG API is live!", "docs_url": "/docs"}


@app.post("/upload", tags=["Documents"])
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a PDF and index it for Q&A.
    Only text-based (digitally-created) PDFs work — scanned PDFs have no extractable text.
    """
    # Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail=f"Only PDF files are supported. Got: '{file.filename}'"
        )

    # Save to disk
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Index the PDF
    try:
        doc_info = process_document(file_path, file.filename)
    except HTTPException:
        raise
    except ValueError as e:
        # pdf_processor raises ValueError for image-based (scanned) PDFs
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

    # Catch the case where 0 chunks were created (silent fail)
    if doc_info["num_chunks"] == 0:
        raise HTTPException(
            status_code=422,
            detail=(
                f"'{file.filename}' appears to be a scanned/image-based PDF — "
                "no text could be extracted from it. "
                "Please upload a PDF where you can select and highlight text with your mouse. "
                "Scanned documents (photos of pages) are not supported without OCR."
            )
        )

    return {
        "status":   "success",
        "message":  f"'{file.filename}' processed and indexed successfully!",
        "document": doc_info
    }


@app.post("/ask", response_model=QuestionResponse, tags=["Q&A"])
async def ask(request: QuestionRequest):
    """
    Ask a natural language question over the indexed documents.
    Returns a grounded answer with page citations.
    """
    try:
        result = answer_question(request.question, top_k=request.top_k)
        return {
            "answer":      result["answer"],
            "sources":     result["sources"],
            "model":       result["model"],
            "tokens_used": result["tokens_used"]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Q&A error: {str(e)}")


@app.get("/documents", tags=["Documents"])
def list_documents():
    """List all documents currently indexed in the vector store."""
    docs = get_documents()
    return {"count": len(docs), "documents": docs}


@app.get("/stats", tags=["Health"])
def stats():
    """Return statistics about the current vector index."""
    return get_stats()


@app.delete("/clear", tags=["Documents"])
def clear_documents():
    """Clear ALL documents from the vector store. Irreversible."""
    clear_all()
    return {"status": "success", "message": "All documents cleared."}
